import pyaudio
import wave
import whisper
from datetime import datetime

# Constants
CHUNK_DURATION = 5  # Duration of each chunk in seconds

def record_audio(output_filename, duration=CHUNK_DURATION):
    """
    Record audio and save it to a WAV file.
    """
    chunk = 1024  # Number of audio samples per buffer
    format = pyaudio.paInt16  # 16-bit audio format
    channels = 1  # Mono audio
    rate = 44100  # Sampling rate in Hz

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream for recording
    print("Recording audio...")
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    # Record audio in chunks
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the recording stream
    stream.stop_stream()
    stream.close()

    # Save the recording to a temporary file
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Recording complete. Audio saved to {output_filename}")

def transcribe_audio_with_whisper(audio_path):
    """
    Transcribe audio using Whisper.ai.
    """
    print("Loading Whisper model...")
    model = whisper.load_model("base")  # You can choose other models like "tiny", "small", "large"
    print(f"Transcribing audio from {audio_path}...")
    result = model.transcribe(audio_path)
    transcription = result.get("text", "No transcription available")
    print(f"Transcription: {transcription}")
    return transcription

# Example usage
if __name__ == "__main__":
    # Record audio and save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_file = f"recording_{timestamp}.wav"
    record_audio(output_filename=audio_file)

    # Transcribe the recorded audio using Whisper
    transcription = transcribe_audio_with_whisper(audio_file)