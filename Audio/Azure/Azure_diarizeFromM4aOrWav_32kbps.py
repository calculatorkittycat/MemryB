import time
import os
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk
from Config.config import SPEECH_KEY, SPEECH_REGION

def format_time(milliseconds):
    seconds = milliseconds // 1000
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours}h {minutes % 60}m {seconds % 60}s"

def conversation_transcriber_transcribed_cb(evt, transcript_output, speaker_map, elapsed_time):
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        timestamp = evt.result.offset // 10000  # Convert to milliseconds
        total_timestamp = elapsed_time + timestamp
        speaker_id = evt.result.speaker_id or "Unknown Speaker"

        # Map speaker IDs for continuity across files
        if speaker_id not in speaker_map:
            speaker_map[speaker_id] = f"Speaker-{len(speaker_map) + 1}"

        text = evt.result.text
        if text.strip():  # Exclude empty or "Unknown" transcriptions
            formatted_text = f"[{format_time(total_timestamp)}] {speaker_map[speaker_id]}: {text}\n"
            transcript_output.append(formatted_text)
            print(f"TRANSCRIPTION RECEIVED: {formatted_text.strip()}")
    elif evt.result.reason == speechsdk.ResultReason.NoMatch:
        print("NOMATCH: Speech could not be transcribed.")

def process_audio_combined(file_path, speech_config, transcript_file, elapsed_time, speaker_map):
    print(f"Processing audio file: {file_path}")
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config,
                                                                               audio_config=audio_config)

    transcribing_stop = False
    transcript_output = []

    def stop_cb(evt):
        nonlocal transcribing_stop
        transcribing_stop = True
        print(f"Session stopped or canceled: {evt}")

    # Connect callbacks
    conversation_transcriber.transcribed.connect(
        lambda evt: conversation_transcriber_transcribed_cb(evt, transcript_output, speaker_map, elapsed_time))
    conversation_transcriber.session_stopped.connect(stop_cb)
    conversation_transcriber.canceled.connect(stop_cb)

    conversation_transcriber.start_transcribing_async()

    start_time = time.time()
    while not transcribing_stop:
        time.sleep(0.5)

    conversation_transcriber.stop_transcribing_async()

    transcription_time = time.time() - start_time

    # Append transcription to the file, excluding blanks and "Unknown"
    with open(transcript_file, 'a') as f:
        for line in transcript_output:
            if "Unknown:" not in line.strip():
                f.write(line)

    print(f"Finished processing audio file: {file_path}")
    print(f"Time taken for transcription: {format_time(transcription_time * 1000)}")

    return transcription_time, transcript_output

# Main
input_file = r"C:\\Users\\cicai\\PycharmProjects\\MemryB\\BodyCam\\OUTPUT_TRUNCATED_Sub_4_Hours.wav"
output_directory = r"C:\\Users\\cicai\\PycharmProjects\\MemryB\\Audio\\Azure\\transcriptions"

total_start_time = time.time()

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

elapsed_time = 0  # Total elapsed time across all files
speaker_map = {}  # Persistent speaker mapping across files

print(f"Processing file: {input_file}")

# Generate output filename
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_file = os.path.join(output_directory, f"{base_name}_transcription.txt")

try:
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_recognition_language = "en-US"
    speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
                               value='true')

    transcription_time, transcript_output = process_audio_combined(input_file, speech_config, output_file, elapsed_time, speaker_map)

    # Calculate input file duration
    chunk_audio = AudioSegment.from_file(input_file)
    audio_duration = len(chunk_audio)  # in milliseconds
    elapsed_time += audio_duration  # Update elapsed time

    print(f"File duration: {format_time(audio_duration)}")
    print(f"Transcription time: {format_time(transcription_time * 1000)}")

except Exception as e:
    print(f"Error processing audio file {input_file}: {e}")

# Calculate total processing time
total_time = time.time() - total_start_time
print(f"Total processing time for all files: {format_time(total_time * 1000)}")
print("All transcriptions completed.")
