import azure.cognitiveservices.speech as speechsdk
from Config.config import SPEECH_KEY, SPEECH_REGION

# Input file path
input_file = r"C:\\Users\\cicai\\PycharmProjects\\MemryB\\BodyCam\\OUTPUT_TRUNCATED_Sub_4_Hours.wav"
output_file = "transcription_output.txt"

# Initialize the speech configuration
speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
speech_config.request_word_level_timestamps()
speech_config.set_service_property(
    name="diarizationEnabled", value="true", channel=speechsdk.ServicePropertyChannel.UriQueryParameter
)

# Set up audio configuration with your file
audio_config = speechsdk.audio.AudioConfig(filename=input_file)

# Initialize a SpeechRecognizer
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)


# Function to process the diarized output
def process_diarization(result, output_file):
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        diarized_result = result.properties[speechsdk.PropertyId.SpeechServiceResponse_JsonResult]
        print("Recognized Speech:")
        print(result.text)

        with open(output_file, "a") as file:
            for line in diarized_result.split("\n"):
                try:
                    line_data = json.loads(line)
                    timestamp = line_data.get("Offset", 0) / 10000000  # Convert to seconds
                    hours, remainder = divmod(timestamp, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    formatted_timestamp = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
                    text = line_data.get("Text", "")
                    print(f"[{formatted_timestamp}] {text}")
                    file.write(f"[{formatted_timestamp}] {text}\n")
                except json.JSONDecodeError:
                    print("Skipping malformed line in JSON output.")
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled:", cancellation_details.reason)
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details:", cancellation_details.error_details)


# Start speech recognition and process chunk-by-chunk
print("Starting diarization...")
with open(output_file, "w") as file:
    file.write("Diarization Transcription\n")
    file.write("========================\n")

while True:
    result = speech_recognizer.recognize_once()
    process_diarization(result, output_file)
    print("Chunk processed. Progress saved.")
