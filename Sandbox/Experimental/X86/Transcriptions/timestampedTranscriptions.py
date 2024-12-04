#####This is work in progress####
#Currently in process of converting logic and folder structure to this pycharm project
#May yield some positive results but still...

####!!!!!UNTESTED!!!!#####


import os
import wave
import pyaudio
from datetime import datetime
import whisper


TRANSCRIPT_DIR = r"Sandbox/Experimental/X86/Output"
RECORDING_DIR = r"Audio/Recordings"


# Function to generate unique filenames
def generate_filenames(base_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}"


def record_audio(duration, output_filename):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []

    print(f"* recording for {duration} seconds")
    for _ in range(0, int(44100 / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)
    print("* done recording")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))


def transcribe_audio_whisper(audio_file):
    # Load Whisper model
    model = whisper.load_model("base")  # You can use 'small', 'medium', 'large' models based on the hardware

    # Transcribe the audio
    print(f"Transcribing {audio_file} with Whisper...")
    result = model.transcribe(audio_file)

    # Extract segments with timestamps and text
    segments = result['segments']
    transcription = ""
    for segment in segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text'].strip()
        transcription += f"[{start_time:.2f}s - {end_time:.2f}s] {text}\n"

    return transcription


def main():
    # Create necessary directories if they don't exist
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    os.makedirs(RECORDING_DIR, exist_ok=True)

    # Ask if user wants to use a pre-recorded file or record new audio
    use_pre_recorded = input("Do you want to use a pre-recorded .wav file? (y/n): ").strip().lower()

    if use_pre_recorded == 'y':
        # Get the name of the pre-recorded file
        pre_recorded_file = input("Enter the name of the pre-recorded .wav file (including .wav): ")
        wave_output_filename = os.path.join(RECORDING_DIR, pre_recorded_file)
    else:
        # User input for duration
        duration = int(input("Enter the duration (in seconds) for the recording: "))
        wave_output_filename = os.path.join(RECORDING_DIR, generate_filenames("output") + ".wav")
        # Record audio
        record_audio(duration, wave_output_filename)
        print(f"Audio saved to: {wave_output_filename}")

    # Transcribe the audio using Whisper
    transcription_result = transcribe_audio_whisper(wave_output_filename)

    # Generate output filenames
    text_output_filename = os.path.join(TRANSCRIPT_DIR, generate_filenames("transcription") + ".txt")


    # Save transcription to the first location
    with open(text_output_filename, 'w') as text_file:
        text_file.write(transcription_result)


    print(f"Transcription complete. Transcription saved to: {text_output_filename}")
    # print(f"Duplicate transcription saved to: {lama_text_output_filename}")
    print("Transcription Output:")
    print(transcription_result)


    # If pre-recorded audio was used, do not ask about retaining the recording
    if use_pre_recorded != 'y':
        # Prompt to retain the recorded audio
        retain_audio = input("Do you want to retain the recorded audio? (y/n): ").strip().lower()
        if retain_audio == 'y':
            print("Recorded audio retained.")
        else:
            os.remove(wave_output_filename)  # Delete the audio file if not retained
            print("Recorded audio discarded.")


if __name__ == "__main__":
    main()
