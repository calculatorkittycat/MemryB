import serial
import time
import csv
import json
import requests
from datetime import datetime
import speech_recognition as sr
import pyaudio
import wave
from queue import Queue
import threading
import cv2
import base64
from openai import OpenAI

# Venice.ai API Configuration
api_key = "1vc8zXqnNa9p50q9Ua5ZzJMVn9K9pE26hQd75gygoZ"  # Replace with your Venice.ai API key
api_endpoint = "https://api.venice.ai/api/v1"
model_id = "nous-theta-8b"
api_timeout = 120

# OpenAI API Configuration
openai_api_key = "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"
client = OpenAI(api_key=openai_api_key)

# Global variables
audio_queue = Queue()
gps_data = None  # Store the latest GPS data
gps_signal_lost = False
five_minute_buffer = []
twenty_minute_buffer = []
hourly_buffer = []

# Constants
CHUNK_DURATION = 30  # Duration of each chunk in seconds

def api_health_check():
    """Perform an API health check."""
    print("Performing API health check...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": "ping"}]
    }
    try:
        response = requests.post(
            f"{api_endpoint}/chat/completions",
            headers=headers,
            json=data,
            timeout=api_timeout
        )
        if response.status_code == 200:
            print(f"API health check successful. Response: {response.json()['choices'][0]['message']['content']}")
        else:
            print(f"API health check failed with status code {response.status_code}: {response.text}")
            raise RuntimeError("API health check failed.")
    except requests.exceptions.RequestException as e:
        print(f"API health check failed with error: {e}")
        raise RuntimeError("API health check failed.")

def get_summary(text):
    """Fetch a summary for the given text."""
    prompt = (
        "Summarize the following text:\n\n"
        f"{text}"
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}]
    }

    for attempt in range(1, 11):  # Retry up to 10 times on failure
        try:
            response = requests.post(
                f"{api_endpoint}/chat/completions",
                headers=headers,
                json=data,
                timeout=api_timeout
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"API call failed with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"API call attempt {attempt} failed with error: {e}")
        time.sleep(5)  # Wait 5 seconds before retrying
    raise RuntimeError("API call failed after 10 attempts.")

# Function to encode the image in Base64 format
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Function to capture image from webcam
def capture_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cv2.imwrite("temp_image.jpg", frame)
    cam.release()
    cv2.destroyAllWindows()

# Function to get image summary using OpenAI API
def get_image_summary(image_path):
    base64_image = encode_image(image_path)
    data_url = f"data:image/png;base64,{base64_image}"  # Adjust MIME type if necessary

    # Call OpenAI API for the current image
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    # Extract content summary from the response
    content_summary = response.choices[0].message.content

    return content_summary

def parse_gngga(sentence):
    """
    Parse a GNGGA sentence and extract relevant information.
    """
    try:
        parts = sentence.split(',')
        if parts[0] != "$GNGGA":
            return None  # Not a GNGGA sentence

        # Check fix quality (0 indicates no fix)
        fix_quality = parts[6]
        if fix_quality == "0":
            global gps_signal_lost
            gps_signal_lost = True
            return None

        # Extract time
        raw_time = parts[1]
        time_str = f"{raw_time[:2]}:{raw_time[2:4]}:{raw_time[4:6]} UTC"

        # Latitude
        raw_lat = parts[2]
        lat_dir = parts[3]
        lat_deg = float(raw_lat[:2])
        lat_min = float(raw_lat[2:])
        latitude = lat_deg + (lat_min / 60.0)
        if lat_dir == "S":
            latitude = -latitude

        # Longitude
        raw_lon = parts[4]
        lon_dir = parts[5]
        lon_deg = float(raw_lon[:3])
        lon_min = float(raw_lon[3:])
        longitude = lon_deg + (lon_min / 60.0)
        if lon_dir == "W":
            longitude = -longitude

        # Satellites used
        satellites_used = parts[7]

        # Altitude
        altitude = parts[9] + " meters"

        gps_signal_lost = False  # Reset signal lost flag
        return {
            "Time": time_str,
            "Latitude": f"{latitude:.6f}° {lat_dir}",
            "Longitude": f"{longitude:.6f}° {lon_dir}",
            "Fix Quality": fix_quality,
            "Satellites Used": satellites_used,
            "Altitude": altitude,
        }
    except (IndexError, ValueError):
        return None

def initialize_csv(filename):
    """
    Create the CSV file with headers if it doesn't already exist.
    """
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Date", "Time", "Latitude", "Longitude", "Fix Quality", "Satellites Used",
            "Altitude", "Transcription", "Summary", "ImageSummary",
            "fiveMinuteSummary", "twentyMinuteSummary", "hourlySummary"
        ])

def append_to_csv(filename, row):
    """
    Append a single row to the CSV file.
    """
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)

def transcribe_and_summarize_audio(gps_entry):
    """
    Record 30 seconds of audio, transcribe it, and summarize it.
    """
    chunk = 1024  # Number of audio samples per buffer
    format = pyaudio.paInt16  # 16-bit audio format
    channels = 1  # Mono audio
    rate = 44100  # Sampling rate in Hz
    record_seconds = CHUNK_DURATION  # Duration of the recording
    output_filename = "temp_audio.wav"  # Temporary file to store audio

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
    for _ in range(0, int(rate / chunk * record_seconds)):
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

    print("Recording complete. Transcribing audio...")

    # Transcribe audio
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(output_filename) as source:
            audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio)
            print(f"Transcription: {transcription}")

            # Prepare prompt for summarization
            prompt = f"GPS Data: Date: {gps_entry['Date']}, Time: {gps_entry['Time']}, Latitude: {gps_entry['Latitude']}, Longitude: {gps_entry['Longitude']}\nTranscription: {transcription}"
            summary = get_summary(prompt)
            print(f"Summary: {summary}")

            # Capture image from webcam
            capture_image()

            # Get image summary using OpenAI API
            image_summary = get_image_summary("temp_image.jpg")
            print(f"Image Summary: {image_summary}")

            return transcription, summary, image_summary
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return "Unintelligible audio", "Unintelligible audio", "No image summary"
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return "Transcription failed", "Summarization failed", "No image summary"

def gps_listener():
    """
    Continuously listen for GPS data, updating the latest GPS data every 5 seconds.
    """
    global gps_data
    with serial.Serial('/dev/serial0', baudrate=9600, timeout=1) as ser:
        print("Listening for GPS data...")
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if "$GNGGA" in line:
                data = parse_gngga(line)
                if data:
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    data["Date"] = current_date
                    gps_data = data  # Update the latest GPS data
            time.sleep(5)  # Wait before checking again

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    csv_filename = f"location_history_{today}.csv"
    initialize_csv(csv_filename)

    # Start GPS listener in a separate thread
    gps_thread = threading.Thread(target=gps_listener)
    gps_thread.daemon = True  # Ensure the thread exits with the program
    gps_thread.start()

    print("Starting audio recording and transcription...")
    while True:
        try:
            # Wait for GPS data
            if not gps_data:
                print("No GPS data available.")
                gps_entry = {
                    "Date": "GPS DATA NOT AVAILABLE",
                    "Time": "GPS DATA NOT AVAILABLE",
                    "Latitude": "GPS DATA NOT AVAILABLE",
                    "Longitude": "GPS DATA NOT AVAILABLE",
                    "Fix Quality": "GPS DATA NOT AVAILABLE",
                    "Satellites Used": "GPS DATA NOT AVAILABLE",
                    "Altitude": "GPS DATA NOT AVAILABLE"
                }
                gps_summary = ""
            else:
                gps_entry = gps_data
                gps_summary = f"GPS Data: Date: {gps_entry['Date']}, Time: {gps_entry['Time']}, Latitude: {gps_entry['Latitude']}, Longitude: {gps_entry['Longitude']}"

            # Record and transcribe audio
            transcription, summary, image_summary = transcribe_and_summarize_audio(gps_summary)

            # Append transcription and summary to the CSV
            row = [
                gps_entry.get("Date", "N/A"),
                gps_entry.get("Time", "N/A"),
                gps_entry.get("Latitude", "N/A"),
                gps_entry.get("Longitude", "N/A"),
                gps_entry.get("Fix Quality", "N/A"),
                gps_entry.get("Satellites Used", "N/A"),
                gps_entry.get("Altitude", "N/A"),
                transcription,
                summary,
                image_summary,
                "",  # Placeholder for fiveMinuteSummary
                "",  # Placeholder for twentyMinuteSummary
                ""   # Placeholder for hourlySummary
            ]
            append_to_csv(csv_filename, row)
            print(f"Appended to CSV at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except KeyboardInterrupt:
            print("Exiting...")
            break

def transcribe_and_summarize_audio(gps_summary):
    """
    Record 30 seconds of audio, transcribe it, and summarize it.
    """
    chunk = 1024  # Number of audio samples per buffer
    format = pyaudio.paInt16  # 16-bit audio format
    channels = 1  # Mono audio
    rate = 44100  # Sampling rate in Hz
    record_seconds = CHUNK_DURATION  # Duration of the recording
    output_filename = "temp_audio.wav"  # Temporary file to store audio

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
    for _ in range(0, int(rate / chunk * record_seconds)):
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

    print("Recording complete. Transcribing audio...")

    # Transcribe audio
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(output_filename) as source:
            audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio)
            print(f"Transcription: {transcription}")

            # Prepare prompt for summarization
            if gps_summary:
                prompt = f"{gps_summary}\nTranscription: {transcription}"
            else:
                prompt = f"Transcription: {transcription}"
            summary = get_summary(prompt)
            print(f"Summary: {summary}")

            # Capture image from webcam
            capture_image()
            print("Image captured at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Get image summary using OpenAI API
            image_summary = get_image_summary("temp_image.jpg")
            print(f"Image Summary: {image_summary}")

            return transcription, summary, image_summary
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return "Unintelligible audio", "Unintelligible audio", "No image summary"
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return "Transcription failed", "Summarization failed", "No image summary"

def transcribe_and_summarize_audio(gps_summary):
    """
    Record 30 seconds of audio, transcribe it, and summarize it.
    """
    chunk = 1024  # Number of audio samples per buffer
    format = pyaudio.paInt16  # 16-bit audio format
    channels = 1  # Mono audio
    rate = 44100  # Sampling rate in Hz
    record_seconds = CHUNK_DURATION  # Duration of the recording
    output_filename = "temp_audio.wav"  # Temporary file to store audio

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
    for _ in range(0, int(rate / chunk * record_seconds)):
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

    print("Recording complete. Transcribing audio...")

    # Transcribe audio
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(output_filename) as source:
            audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio)
            print(f"Transcription: {transcription}")

            # Prepare prompt for summarization
            if gps_summary:
                prompt = f"{gps_summary}\nTranscription: {transcription}"
            else:
                prompt = f"Transcription: {transcription}"
            summary = get_summary(prompt)
            print(f"Summary: {summary}")

            # Capture image from webcam
            capture_image()

            # Get image summary using OpenAI API
            image_summary = get_image_summary("temp_image.jpg")
            print(f"Image Summary: {image_summary}")

            return transcription, summary, image_summary
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return "Unintelligible audio", "Unintelligible audio", "No image summary"
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return "Transcription failed", "Summarization failed", "No image summary"
if __name__ == "__main__":
    # Perform API health check before starting
    api_health_check()
    main()