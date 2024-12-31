import os
import sys
import time
import math
import subprocess
import json

import torch
import whisper
import librosa
import torchaudio

from pyannote.audio import Pipeline
from pyannote.core import Timeline, Segment

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
WAV_FOLDER = r"D:\DCIM"    # <-- Change to your folder containing .wav files
CHUNK_LENGTH = 300         # in seconds
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
WHISPER_MODEL = "tiny"

# Replace with your valid HF token. Make sure you have accepted:
#   1) pyannote/segmentation-3.0
#   2) pyannote/speaker-diarization-3.1
USE_AUTH_TOKEN = "hf_your_access_token_here"

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

def run_ffprobe(filepath):
    """
    Use subprocess to call ffprobe and return the float duration of the audio.
    Raises an exception if ffprobe fails or the duration is not found.
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_format',
        '-print_format', 'json',
        '-i', filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        return duration
    except Exception as e:
        raise RuntimeError(f"Could not probe audio file '{filepath}': {str(e)}")

def time_to_str(seconds: float) -> str:
    """
    Convert a float number of seconds to HH:MM:SS format.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def transcribe_chunk(audio_path, start_time, end_time, model):
    """
    Transcribe a slice of audio between start_time and end_time using Whisper.
    We'll load that slice via librosa for convenience.
    """
    duration = end_time - start_time
    audio_data, sr = librosa.load(
        audio_path, sr=16000, offset=start_time, duration=duration
    )
    audio_data = audio_data.astype('float32')  # Whisper expects float32

    result = model.transcribe(audio_data, language="en")
    return result["segments"]

def diarize_chunk(audio_path, start_time, end_time, pipeline):
    """
    Load a slice of audio between start_time and end_time in memory,
    then pass it to the pipeline via {"waveform": waveform, "sample_rate": sr}.
    Note: pyannote.audio >= 3.1 no longer accepts start/duration directly.
    """
    chunk_duration = end_time - start_time

    sr = 16000
    frame_offset = int(start_time * sr)
    num_frames = int(chunk_duration * sr)

    # Load chunk using torchaudio
    waveform, loaded_sr = torchaudio.load(
        audio_path,
        frame_offset=frame_offset,
        num_frames=num_frames
    )
    # waveform shape is typically [channels, samples]

    # Downmix stereo to mono if needed
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)  # => [1, samples]

    # Ensure shape is [1, time]
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)

    # Resample if needed
    if loaded_sr != sr:
        waveform = torchaudio.functional.resample(waveform, loaded_sr, sr)

    # Ensure float32
    waveform = waveform.float()

    # Pass the chunk to PyAnnote pipeline
    diarization = pipeline({
        "waveform": waveform,
        "sample_rate": sr
    })
    return diarization

def combine_transcript_and_diarization(whisper_segments, diarization_result, offset):
    """
    Match Whisper transcription segments with PyAnnote speaker labels.
    Returns a list of entries with "start", "end", "speaker", "text".
    """
    speaker_timeline = []
    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
        speaker_timeline.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })

    speaker_timeline.sort(key=lambda x: x["start"])

    transcript_output = []
    for seg in whisper_segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg_text = seg["text"].strip()

        absolute_start = seg_start + offset
        absolute_end = seg_end + offset

        best_speaker = "Unknown"
        best_overlap = 0.0
        for st in speaker_timeline:
            overlap = (
                min(absolute_end, st["end"]) -
                max(absolute_start, st["start"])
            )
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = st["speaker"]

        transcript_output.append({
            "start": absolute_start,
            "end": absolute_end,
            "speaker": best_speaker,
            "text": seg_text
        })

    return transcript_output

def format_paragraphs(transcript_data):
    """
    Combine consecutive segments from the same speaker into paragraphs.
    """
    paragraphs = []
    current_speaker = None
    current_paragraph = []
    paragraph_start_time = None

    for entry in transcript_data:
        speaker = entry["speaker"]
        text = entry["text"]
        start_time = entry["start"]

        if speaker != current_speaker:
            # finalize old paragraph
            if current_paragraph:
                timestamp_str = time_to_str(paragraph_start_time)
                paragraph_text = f"[{timestamp_str}] {current_speaker}: " + " ".join(current_paragraph)
                paragraphs.append(paragraph_text)

            current_speaker = speaker
            current_paragraph = [text]
            paragraph_start_time = start_time
        else:
            current_paragraph.append(text)

    # finalize last paragraph
    if current_paragraph:
        timestamp_str = time_to_str(paragraph_start_time)
        paragraph_text = f"[{timestamp_str}] {current_speaker}: " + " ".join(current_paragraph)
        paragraphs.append(paragraph_text)

    return paragraphs

def process_audio(audio_path, output_path, whisper_model, diarization_pipeline):
    """
    Process a single .wav file: transcribe + diarize in chunks, combine results,
    format paragraphs, and write to output file.

    Also prints partial results chunk-by-chunk to the console.
    """
    start_time_overall = time.time()

    print(f"[INFO] Reading metadata for '{audio_path}'...")
    try:
        full_duration = run_ffprobe(audio_path)
    except RuntimeError as e:
        print(f"[ERROR] {str(e)}")
        return

    print(f"[INFO] Duration: {full_duration / 3600:.2f} hours.")
    all_transcript_data = []

    num_chunks = math.ceil(full_duration / CHUNK_LENGTH)
    print(f"[INFO] Splitting into {num_chunks} chunks (chunk length: {CHUNK_LENGTH} seconds).")

    for i in range(num_chunks):
        chunk_start = i * CHUNK_LENGTH
        chunk_end = min(full_duration, (i + 1) * CHUNK_LENGTH)

        print(f"[INFO] Processing chunk {i+1}/{num_chunks} "
              f"({time_to_str(chunk_start)} - {time_to_str(chunk_end)})")

        # --- Whisper Transcription ---
        whisper_segments = transcribe_chunk(audio_path, chunk_start, chunk_end, whisper_model)

        # --- PyAnnote Diarization ---
        diarization_result = diarize_chunk(audio_path, chunk_start, chunk_end, diarization_pipeline)

        # --- Combine ---
        combined = combine_transcript_and_diarization(
            whisper_segments, diarization_result, offset=chunk_start
        )

        # -------------------------------------------------------------------
        # Print partial paragraphs in console (just this chunk)
        # -------------------------------------------------------------------
        partial_paragraphs = format_paragraphs(combined)
        print(f"[CHUNK {i+1}/{num_chunks} OUTPUT]")
        for para in partial_paragraphs:
            print(para)
        print("--------------------------------------------------\n")

        # Accumulate combined data for final output
        all_transcript_data.extend(combined)

    print("[INFO] Formatting full paragraphs...")
    paragraphs = format_paragraphs(all_transcript_data)

    # Write final transcript
    print(f"[INFO] Writing transcript to '{output_path}'...")
    with open(output_path, "w", encoding="utf-8") as f:
        for para in paragraphs:
            f.write(para + "\n\n")

    # -------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------
    end_time_overall = time.time()
    execution_time = end_time_overall - start_time_overall
    word_count = sum(len(item["text"].split()) for item in all_transcript_data)
    unique_speakers = set(item["speaker"] for item in all_transcript_data)
    speaker_count = len(unique_speakers)

    print("[INFO] --- Metrics ---")
    print(f"[INFO] Execution time: {execution_time:.2f} seconds")
    print(f"[INFO] Word count: {word_count}")
    print(f"[INFO] Number of unique speakers: {speaker_count}")
    print("[INFO] ---------------")

def main():
    # Check for GPU availability, fail if not present
    if not torch.cuda.is_available():
        print("[ERROR] CUDA is not available. The script will now exit.")
        sys.exit(1)
    else:
        print("[INFO] Using GPU (CUDA).")

    print("[INFO] Loading Whisper model...")
    whisper_model = whisper.load_model(WHISPER_MODEL, device="cuda")

    print("[INFO] Loading PyAnnote diarization pipeline...")
    try:
        diarization_pipeline = Pipeline.from_pretrained(
            DIARIZATION_MODEL,
            use_auth_token=USE_AUTH_TOKEN
        )
        # Optionally run the pipeline on GPU
        diarization_pipeline.to(torch.device("cuda"))

    except Exception as e:
        print("\n[ERROR] Could not download/load PyAnnote pipeline. "
              "Ensure you accepted the pyannote/speaker-diarization-3.1 model license.")
        print(f"Error details: {str(e)}")
        sys.exit(1)

    if not os.path.isdir(WAV_FOLDER):
        print(f"[ERROR] The folder '{WAV_FOLDER}' does not exist.")
        sys.exit(1)

    wav_files = [f for f in os.listdir(WAV_FOLDER) if f.lower().endswith('.wav')]
    wav_files.sort()

    if not wav_files:
        print(f"[INFO] No .wav files found in '{WAV_FOLDER}'.")
        return

    print("[INFO] Found the following .wav files:")
    for wf in wav_files:
        print(f"   - {wf}")

    print("[INFO] Beginning processing of each .wav file in alphabetical order...")

    for wav_file in wav_files:
        input_audio_path = os.path.join(WAV_FOLDER, wav_file)
        base_name, _ = os.path.splitext(wav_file)
        output_txt_path = os.path.join(WAV_FOLDER, f"{base_name}_transcript.txt")

        print("======================================")
        print(f"[INFO] Now processing: {input_audio_path}")
        process_audio(input_audio_path, output_txt_path, whisper_model, diarization_pipeline)
        print(f"[INFO] Finished processing: {wav_file}")
        print("======================================\n")

if __name__ == "__main__":
    main()
