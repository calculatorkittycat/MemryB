from pydub import AudioSegment
import math
import os

def reduce_quality_and_split(input_wav, output_dir, target_bitrate, chunk_duration_minutes):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load the input WAV file
    audio = AudioSegment.from_wav(input_wav)

    # Convert to desired bitrate
    reduced_audio_path = os.path.join(output_dir, r"C:\\Users\\cicai\\PycharmProjects\\MemryB\\Sandbox\\Experimental\\X86\\Input\\Audio\\Chunked\\reduced_quality.wav")
    audio.export(reduced_audio_path, format="wav", bitrate=str(target_bitrate))

    # Reload reduced quality audio
    reduced_audio = AudioSegment.from_wav(reduced_audio_path)

    # Calculate chunk duration in milliseconds
    chunk_duration_ms = chunk_duration_minutes * 60 * 1000

    # Calculate number of chunks
    total_chunks = math.ceil(len(reduced_audio) / chunk_duration_ms)

    for i in range(total_chunks):
        start_ms = i * chunk_duration_ms
        end_ms = min(start_ms + chunk_duration_ms, len(reduced_audio))

        # Extract chunk
        chunk = reduced_audio[start_ms:end_ms]

        # Save chunk
        chunk_name = f"chunk_{i + 1}.wav"
        chunk_path = os.path.join(output_dir, chunk_name)
        chunk.export(chunk_path, format="wav")

        print(f"Saved {chunk_name}")

# Parameters
input_wav = r"D:\\DCIM\\extracted\\OUTPUT.wav"  # Path to your input WAV file
output_dir = "output_chunks"  # Directory to save the chunks
target_bitrate = 16 * 1000  # 16 kbps in bits per second
chunk_duration_minutes = 20  # Chunk duration in minutes

reduce_quality_and_split(input_wav, output_dir, target_bitrate, chunk_duration_minutes)
