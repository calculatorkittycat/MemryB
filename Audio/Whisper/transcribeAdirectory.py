import os
import time
import whisper
from datetime import datetime
import wave

def get_audio_duration(file_path):
    with wave.open(file_path, 'r') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration

def transcribe_audio(directory):
    # Load the Whisper model
    model = whisper.load_model("base")

    # Create or open the transcription file
    with open("transcriptions.txt", "w", encoding="utf-8") as file:
        file.write(f"Transcriptions started at: {datetime.now()}\n\n")

    # Get list of .wav files in the directory
    files = sorted([f for f in os.listdir(directory) if f.endswith('.wav')])

    total_audio_duration = 0.0
    start_time = time.time()

    for audio_file in files:
        file_path = os.path.join(directory, audio_file)
        print(f"Processing file: {audio_file}")

        # Calculate audio file duration
        duration = get_audio_duration(file_path)
        total_audio_duration += duration

        # Transcribe audio file
        result = model.transcribe(file_path)

        # Append transcription to file
        with open("transcriptions.txt", "a", encoding="utf-8") as file:
            file.write(f"Transcription for {audio_file}:\n")
            file.write(result["text"] + "\n")
            file.write("\n")

    end_time = time.time()
    total_runtime = end_time - start_time

    print(f"Total audio duration: {total_audio_duration:.2f} seconds")
    print(f"Total script runtime: {total_runtime:.2f} seconds")

if __name__ == "__main__":
    directory = "D:\DCIM"  # Replace with the path to your directory containing .wav files
    transcribe_audio(directory)
