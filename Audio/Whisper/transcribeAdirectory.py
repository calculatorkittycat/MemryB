import os
import time
import math
import whisper
from datetime import datetime
import wave
import pydub


def split_audio_by_size(file_path, chunk_size_kb=50000):
    import math

    file_size_bytes = os.path.getsize(file_path)

    # Explicitly set format="mp3"
    audio = pydub.AudioSegment.from_file(file_path, format="mp3")
    total_length_ms = len(audio)

    # Calculate how many chunks we need
    chunk_count = math.ceil(file_size_bytes / (chunk_size_kb * 1024))

    # If smaller than the threshold, no split
    if chunk_count <= 1:
        return [file_path]

    segment_paths = []
    segment_length_ms = total_length_ms / chunk_count

    for idx in range(chunk_count):
        start_ms = int(idx * segment_length_ms)
        end_ms = int((idx + 1) * segment_length_ms)
        segment = audio[start_ms:end_ms]

        base_name, ext = os.path.splitext(file_path)
        segment_path = f"{base_name}_part{idx}.mp3"
        segment.export(segment_path, format="mp3")
        segment_paths.append(segment_path)

    return segment_paths


def convert_mp3_to_wav(mp3_path, wav_path):
    """
    Converts an MP3 file to WAV format using pydub.
    """
    audio = pydub.AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")


def get_audio_duration(file_path):
    """
    Returns the duration (in seconds) of a WAV audio file using the wave module.
    """
    with wave.open(file_path, 'r') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def transcribe_audio(directory):
    """
    Main function to:
    1. Find MP3/WAV files.
    2. Split MP3 files bigger than 50,000 KB.
    3. Convert splits to WAV and transcribe using Whisper (with timestamps).
    4. Save transcriptions (with timestamps) to a text file.
    """
    # Load the Whisper model
    model = whisper.load_model("base")

    # Create or open the transcription file
    with open("transcriptions12312024.txt", "w", encoding="utf-8") as file:
        file.write(f"Transcriptions started at: {datetime.now()}\n\n")

    # Print absolute directory path for debugging
    print(f"Searching directory: {os.path.abspath(directory)}")

    # Get list of .mp3 and .wav files in the directory (case-insensitive)
    files = sorted([f for f in os.listdir(directory)
                    if f.lower().endswith('.mp3') or f.lower().endswith('.wav')])

    print("Files found in the directory:")
    if not files:
        print("No .mp3 or .wav files found.")
    else:
        for audio_file in files:
            print(audio_file)

    total_audio_duration = 0.0
    start_time = time.time()

    for audio_file in files:
        file_path = os.path.join(directory, audio_file)
        extension = audio_file.lower().split('.')[-1]

        # ----------------
        # Handle MP3 files
        # ----------------
        if extension == 'mp3':
            segments = split_audio_by_size(file_path, 50000)
            for segment_path in segments:
                # Convert .mp3 to .wav
                wav_path = os.path.join(directory, os.path.splitext(segment_path)[0] + '.wav')
                print(f"Processing file: {segment_path} (converted to WAV)")
                convert_mp3_to_wav(segment_path, wav_path)

                # Calculate audio file duration
                duration = get_audio_duration(wav_path)
                total_audio_duration += duration

                # Transcribe audio file with Whisper
                # Setting `task="transcribe"` or `language="en"` etc. if needed.
                result = model.transcribe(wav_path)

                # Write transcription (with timestamps) to text file
                with open("transcriptions12312024.txt", "a", encoding="utf-8") as file:
                    file.write(f"Transcription for {audio_file} (segment: {os.path.basename(segment_path)}):\n")

                    # Check if segments exist in the result
                    if "segments" in result:
                        for seg in result["segments"]:
                            start_ts = seg["start"]
                            end_ts = seg["end"]
                            text = seg["text"]
                            file.write(f"[{start_ts:6.2f}s - {end_ts:6.2f}s] {text}\n")
                    else:
                        # If no segments were returned, just write raw text
                        file.write(result["text"] + "\n")

                    file.write("\n")  # Add spacing

                # Clean up the WAV file
                os.remove(wav_path)

                # If you do NOT want to keep the split MP3 files, uncomment:
                if segment_path != file_path:
                     os.remove(segment_path)

        # ---------------
        # Handle WAV files
        # ---------------
        else:
            print(f"Processing file: {audio_file}")

            # Calculate audio file duration
            duration = get_audio_duration(file_path)
            total_audio_duration += duration

            # Transcribe audio file
            result = model.transcribe(file_path)

            with open("transcriptions12312024.txt", "a", encoding="utf-8") as file:
                file.write(f"Transcription for {audio_file}:\n")

                # Check if segments exist in the result
                if "segments" in result:
                    for seg in result["segments"]:
                        start_ts = seg["start"]
                        end_ts = seg["end"]
                        text = seg["text"]
                        file.write(f"[{start_ts:6.2f}s - {end_ts:6.2f}s] {text}\n")
                else:
                    file.write(result["text"] + "\n")

                file.write("\n")  # Add spacing

    end_time = time.time()
    total_runtime = end_time - start_time

    print(f"Total audio duration: {total_audio_duration:.2f} seconds")
    print(f"Total script runtime: {total_runtime:.2f} seconds")


if __name__ == "__main__":
    directory = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Input\Audio\Phillips\Meetings\output"
    transcribe_audio(directory)
