from pyannote.audio import Pipeline
import whisper
import torch
from pyannote.core import Segment
import time  # For timing

# Reproducibility warning fix
print("C:\\Users\\cicai\\PycharmProjects\\MemryB\\.venv\\Lib\\site-packages\\pyannote\\audio\\utils\\reproducibility.py:74: ReproducibilityWarning: TensorFloat-32 (TF32) has been disabled as it might lead to reproducibility issues and lower accuracy.")
print("It can be re-enabled by calling")
print("   >>> import torch")
print("   >>> torch.backends.cuda.matmul.allow_tf32 = True")
print("   >>> torch.backends.cudnn.allow_tf32 = True")

import torch
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# Check if CUDA is available
if torch.cuda.is_available():
    cuda_device = torch.cuda.get_device_name(0)
    print(f"CUDA is available. Using GPU: {cuda_device}\n")
else:
    print("CUDA is not available. Falling back to CPU.\n")

# Hugging Face access token and Pyannote pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="YOUR_HUGGINGFACE_ACCESS_TOKEN"
)

# Send pipeline to GPU if available
pipeline.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

# Load OpenAI Whisper model
model = whisper.load_model("medium")  # Use "base", "medium", or "large" for better accuracy
model = model.to("cuda" if torch.cuda.is_available() else "cpu")  # Explicitly move model to GPU if available

# Input audio file
audio_file = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Input\Audio\Phillips\Meetings\output\2025.01.02_21.14_01_alex.wav"

# Step 1: Diarization
start_time = time.time()
print("Starting diarization...")
diarization = pipeline(audio_file)
diarization_time = time.time() - start_time
print(f"Diarization completed in {diarization_time:.2f} seconds.\n")

# Step 2: Transcription
start_time = time.time()
print("Starting transcription...")
transcription_result = model.transcribe(audio_file)
transcription_time = time.time() - start_time
print(f"Transcription completed in {transcription_time:.2f} seconds.\n")

# Step 3: Align diarization and transcription with deduplication
def diarize_text(asr_result, diarization_result):
    """
    Align ASR results with diarization results to attribute text to speakers.

    Parameters:
    - asr_result: Dictionary containing ASR transcription results with 'segments'.
    - diarization_result: pyannote.core.Annotation object with diarization results.

    Returns:
    - List of tuples containing (Segment, speaker label, transcribed text).
    """
    results = []
    last_text = ""  # To avoid repeating the same text
    for segment in asr_result['segments']:
        asr_start = segment['start']
        asr_end = segment['end']
        asr_text = segment['text'].strip()
        asr_segment = Segment(asr_start, asr_end)
        # Find overlapping diarization segments
        overlapping_segments = diarization_result.crop(asr_segment, mode='intersection')
        for diarized_segment, _, speaker in overlapping_segments.itertracks(yield_label=True):
            overlap = asr_segment & diarized_segment
            if overlap:
                if asr_text != last_text:  # Avoid duplicate text
                    results.append((overlap, speaker, asr_text))
                last_text = asr_text  # Update the last seen text
    return results

# Step 4: Align transcription with speaker diarization
start_time = time.time()
print("Aligning diarization and transcription...")
final_result = diarize_text(transcription_result, diarization)
alignment_time = time.time() - start_time
print(f"Alignment completed in {alignment_time:.2f} seconds.\n")

# Step 5: Save results to a text file
output_file = r"C:\Users\cicai\PycharmProjects\MemryB\Sandbox\Experimental\X86\Input\Audio\Phillips\Meetings\output\2025.01.02_21.14_01_Alex_More_Accurate_test.txt"
print("Saving results to file...")
start_time = time.time()
with open(output_file, "w") as file:
    file.write("Speaker Segments with Transcription:\n\n")
    for segment, speaker, text in final_result:
        result_line = f"{segment.start:.2f}s - {segment.end:.2f}s | {speaker}: {text}\n"
        file.write(result_line)
        print(result_line)  # Optionally still print to console for immediate feedback
saving_time = time.time() - start_time
print(f"Results saved to {output_file} in {saving_time:.2f} seconds.\n")

# Summary of timings
total_time = diarization_time + transcription_time + alignment_time + saving_time
print(f"Summary of processing times:")
print(f"  Diarization: {diarization_time:.2f} seconds")
print(f"  Transcription: {transcription_time:.2f} seconds")
print(f"  Alignment: {alignment_time:.2f} seconds")
print(f"  Saving results: {saving_time:.2f} seconds")
print(f"  Total time: {total_time:.2f} seconds")
