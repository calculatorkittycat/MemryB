# This script processes audio files (.wav and .m4a) for diarization using Azure Cognitive Services Speech-to-Text.
# It performs the following steps:
# 1. Reads audio files from the input directory and converts .m4a files to .wav format if needed.
# 2. Iteratively reduces audio quality (bitrate and sample rate) using aggressive compression until a 3% word count loss is observed.
# 3. Tracks file sizes, transcription times, and word counts for each test configuration.
# 4. Outputs transcription files and generates a styled HTML report summarizing the results.
# 5. At the end, displays the lowest audio quality with the highest word count before the 3% loss threshold.
#
# Output:
# Separate transcription files and an HTML report summarizing all test results.
#
# Dependencies:
# - Pydub: For audio manipulation.
# - FFmpeg: For aggressive audio compression.
# - Azure Cognitive Services SDK: For speech-to-text transcription.
# - Configuration file for Azure credentials (SPEECH_KEY and SPEECH_REGION).

import time
import os
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk
from Config.config import SPEECH_KEY, SPEECH_REGION

# Metrics dictionary to store results for HTML output
metrics = []
loss_threshold = 0.03
best_config = None
max_word_count = 0

def conversation_transcriber_transcribed_cb(evt, transcript_output):
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        timestamp = evt.result.offset // 10000  # Convert to milliseconds
        speaker_id = evt.result.speaker_id or "Unknown Speaker"
        text = evt.result.text
        formatted_text = f"[{timestamp}ms] {speaker_id}: {text}\n"
        transcript_output.append(formatted_text)
        print(f"TRANSCRIPTION RECEIVED: {formatted_text.strip()}")
    elif evt.result.reason == speechsdk.ResultReason.NoMatch:
        print("NOMATCH: Speech could not be transcribed.")

def process_audio_combined(file_path, speech_config, transcript_file, duration):
    print(f"Processing audio file: {file_path}")
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config,
                                                                               audio_config=audio_config)

    transcribing_stop = False
    transcript_output = []

    def stop_cb(evt):
        nonlocal transcribing_stop
        transcribing_stop = True

    # Connect callbacks
    conversation_transcriber.transcribed.connect(
        lambda evt: conversation_transcriber_transcribed_cb(evt, transcript_output))
    conversation_transcriber.session_stopped.connect(stop_cb)
    conversation_transcriber.canceled.connect(stop_cb)

    conversation_transcriber.start_transcribing_async()

    start_time = time.time()
    while not transcribing_stop:
        time.sleep(0.5)
        if time.time() - start_time > duration:
            conversation_transcriber.stop_transcribing_async()
            break

    transcription_time = time.time() - start_time

    # Append transcription to the file
    with open(transcript_file, 'a') as f:
        f.writelines(transcript_output)
    word_count = sum(len(line.split()) for line in transcript_output)
    print(f"Finished processing audio file: {file_path}")
    print(f"Time taken for transcription: {transcription_time:.2f} seconds")
    print(f"Word count: {word_count}")

    return transcription_time, word_count

# Main
input_directory = r"C:\\Users\\cicai\\PycharmProjects\\MemryB\\Sandbox\\Experimental\\X86\\Input\\Audio"
output_directory = r"C:\\Users\\cicai\\PycharmProjects\\MemryB\\Sandbox\\Experimental\\X86\\Output"
html_report_file = os.path.join(output_directory, "transcription_metrics.html")

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Get all .wav and .m4a files from the directory
audio_files = sorted(
    [os.path.join(input_directory, file) for file in os.listdir(input_directory) if file.endswith((".wav", ".m4a"))])

for audio_file in audio_files:
    print(f"Processing file: {audio_file}")
    if audio_file.endswith(".m4a"):
        print(f"Converting {audio_file} to WAV format...")
        audio = AudioSegment.from_file(audio_file, format="m4a")
    else:
        audio = AudioSegment.from_file(audio_file, format="wav")

    # Display initial audio properties
    initial_size = os.path.getsize(audio_file)
    print(f"Initial file size: {initial_size / 1024:.2f} KB")
    print(f"Initial frame rate: {audio.frame_rate} Hz")

    current_bitrate = 96000  # Start with 96kbps
    while True:
        suffix = f"{current_bitrate // 1000}kbps"
        print(f"Reducing sample rate for {audio_file} to {current_bitrate} bps...")
        adjusted_audio = audio.set_frame_rate(current_bitrate)

        adjusted_file = os.path.join(output_directory, f"adjusted_{suffix}_{os.path.basename(audio_file).replace('.m4a', '.wav')}")
        adjusted_audio.export(adjusted_file, format="wav")

        # Display adjusted audio properties
        adjusted_size = os.path.getsize(adjusted_file)
        print(f"Adjusted file size ({suffix}): {adjusted_size / 1024:.2f} KB")
        print(f"Adjusted frame rate: {adjusted_audio.frame_rate} Hz")

        # Generate output filename with input file name included
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        output_file = os.path.join(output_directory, f"{base_name}_{suffix}_transcription.txt")

        print(f"Starting transcription for {suffix} audio...")
        try:
            speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
            speech_config.speech_recognition_language = "en-US"
            speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
                                       value='true')

            transcription_time, word_count = process_audio_combined(adjusted_file, speech_config, output_file, duration=60)

            metrics.append({
                "file": base_name,
                "bitrate": suffix,
                "initial_size_kb": initial_size / 1024,
                "adjusted_size_kb": adjusted_size / 1024,
                "transcription_time": transcription_time,
                "word_count": word_count
            })

            # Check for word count loss
            if len(metrics) > 1:
                previous_word_count = metrics[-2]['word_count']
                word_count_loss = (previous_word_count - word_count) / previous_word_count

                if word_count_loss > loss_threshold:
                    print(f"3% word count loss threshold reached. Stopping further reduction.")
                    break

            # Update best configuration
            if word_count >= max_word_count:
                max_word_count = word_count
                best_config = suffix

        except Exception as e:
            print(f"Error processing audio file {audio_file} at {suffix}: {e}")
        finally:
            if os.path.exists(adjusted_file):
                os.remove(adjusted_file)

        current_bitrate //= 2  # Halve the bitrate for next iteration

# Generate HTML report
with open(html_report_file, 'w') as html:
    html.write("<html><head><title>Transcription Metrics</title>")
    html.write("<style>")
    html.write("body { font-family: Arial, sans-serif; margin: 20px; }")
    html.write("h1 { color: #333; text-align: center; }")
    html.write("table { width: 100%; border-collapse: collapse; margin-top: 20px; }")
    html.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }")
    html.write("th { background-color: #f4f4f4; color: #333; }")
    html.write("tr:nth-child(even) { background-color: #f9f9f9; }")
    html.write("tr:hover { background-color: #f1f1f1; }")
    html.write("</style></head><body>")
    html.write("<h1>Transcription Metrics Report</h1>")
    html.write("<table>")
    html.write("<tr><th>File</th><th>Bitrate</th><th>Initial Size (KB)</th><th>Adjusted Size (KB)</th><th>Transcription Time (s)</th><th>Word Count</th></tr>")

    for metric in metrics:
        html.write(f"<tr><td>{metric['file']}</td><td>{metric['bitrate']}</td><td>{metric['initial_size_kb']:.2f}</td>")
        html.write(f"<td>{metric['adjusted_size_kb']:.2f}</td><td>{metric['transcription_time']:.2f}</td>")
        html.write(f"<td>{metric['word_count']}</td></tr>")

    html.write("</table>")
    html.write("<h2>Best Configuration</h2>")
    html.write(f"<p>The lowest audio quality with the highest word count before the 3% loss threshold was <strong>{best_config}</strong>.</p>")
    html.write("</body></html>")

print(f"Metrics report saved to {html_report_file}")
print(f"Best configuration: {best_config} with word count: {max_word_count}")
print("All transcriptions completed.")
