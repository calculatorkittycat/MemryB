import time
import os
import subprocess
import logging
from datetime import datetime
from math import floor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# -------------------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------------------

WATCH_DIRECTORY = r"C:\Users\cicai\Nextcloud\InstantUpload\gps"

# The name (or subfolder) where screenshots and sound will go -- placed inside this script's dir.
SCREENSHOTS_FOLDER = "screenshots"
SOUND_FOLDER = "sound"
TEXT_EXTRACT_FOLDER = "text_extract"  # new folder for transcriptions

# Path to ffmpeg/ffprobe executables:
FFMPEG_BIN_FOLDER = r"C:\Users\cicai\FFmpeg\tools\ffmpeg-master-latest-win64-gpl-shared\bin"
FFMPEG_BINARY = os.path.join(FFMPEG_BIN_FOLDER, "ffmpeg.exe")
FFPROBE_BINARY = os.path.join(FFMPEG_BIN_FOLDER, "ffprobe.exe")

# Names for logs (still stored in the same directory as this script).
PROCESSED_LOGFILE = "processed_videos.txt"
ERROR_LOGFILE = "error_log.txt"

# Interval (seconds) between size checks to determine if file writing is complete.
CHECK_INTERVAL = 3

# -------------------------------------------------------------------------------------
# IMPORT WHISPER
# -------------------------------------------------------------------------------------
# Assuming you have installed it via: pip install openai-whisper
import whisper

# We will load the base model once at script startup (optional).
WHISPER_MODEL = whisper.load_model("base")  # 'base' model, English audio

# -------------------------------------------------------------------------------------
# DERIVE DIRECTORIES
# -------------------------------------------------------------------------------------

# The directory where this script is running:
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Final absolute paths for screenshots, sound, and text_extract folders:
SCREENSHOTS_PATH = os.path.join(SCRIPT_DIR, SCREENSHOTS_FOLDER)
SOUND_PATH = os.path.join(SCRIPT_DIR, SOUND_FOLDER)
TEXT_EXTRACT_PATH = os.path.join(SCRIPT_DIR, TEXT_EXTRACT_FOLDER)

# A single file where all transcriptions get appended:
TRANSCRIPTIONS_FILE = os.path.join(TEXT_EXTRACT_PATH, "transcriptions.txt")

# -------------------------------------------------------------------------------------
# SETUP LOGGING
# -------------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_error(error_message: str):
    with open(ERROR_LOGFILE, "a", encoding="utf-8") as ef:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ef.write(f"[{current_time}] {error_message}\n")

# -------------------------------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------------------------------

def get_video_duration(filepath: str) -> float:
    cmd = [
        FFPROBE_BINARY,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        return float(output.strip())
    except Exception as e:
        logging.warning(f"Could not get duration for {filepath}: {e}")
        return 0.0

def is_file_fully_written(filepath: str, wait_time: int = CHECK_INTERVAL) -> bool:
    initial_size = os.path.getsize(filepath)
    time.sleep(wait_time)
    new_size = os.path.getsize(filepath)
    return initial_size == new_size

def ensure_folders():
    """
    Create the screenshots, sound, and text_extract subfolders (inside the script's directory)
    if they don't exist.
    """
    if not os.path.exists(SCREENSHOTS_PATH):
        os.makedirs(SCREENSHOTS_PATH)
        logging.info(f"Created folder: {SCREENSHOTS_PATH}")

    if not os.path.exists(SOUND_PATH):
        os.makedirs(SOUND_PATH)
        logging.info(f"Created folder: {SOUND_PATH}")

    if not os.path.exists(TEXT_EXTRACT_PATH):
        os.makedirs(TEXT_EXTRACT_PATH)
        logging.info(f"Created folder: {TEXT_EXTRACT_PATH}")

def load_processed_files() -> set:
    processed_files = set()
    if os.path.exists(PROCESSED_LOGFILE):
        with open(PROCESSED_LOGFILE, "r", encoding="utf-8") as f:
            for line in f:
                file_name = line.strip()
                if file_name:
                    processed_files.add(file_name)
    return processed_files

def mark_file_as_processed(filename: str):
    with open(PROCESSED_LOGFILE, "a", encoding="utf-8") as f:
        f.write(filename + "\n")

# -------------------------------------------------------------------------------------
# FRAME & AUDIO EXTRACTION
# -------------------------------------------------------------------------------------

def extract_frames(input_filepath: str, output_folder: str):
    duration_s = get_video_duration(input_filepath)
    expected_frames = int(duration_s // 30) + 1  # approximate

    base_name = os.path.splitext(os.path.basename(input_filepath))[0]
    output_pattern = os.path.join(output_folder, f"{base_name}_%03d.jpg")

    logging.info(
        f"Video length: {duration_s:.2f}s. "
        f"Expecting ~{expected_frames} frames at 1 frame/30s intervals."
    )

    cmd = [
        FFMPEG_BINARY,
        "-i", input_filepath,
        "-vf", "fps=1/30",
        "-vsync", "vfr",
        output_pattern,
        "-hide_banner",
        "-loglevel", "error"
    ]

    logging.info(f"Extracting frames every 30s for: {input_filepath}")
    start_time = time.time()
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Frame extraction failed for {input_filepath} - {e}")
        logging.error(f"Frame extraction failed for {input_filepath}")
    else:
        elapsed = time.time() - start_time
        logging.info(f"Frame extraction completed in {elapsed:.2f} seconds.")

def extract_audio(input_filepath: str, output_folder: str):
    base_name = os.path.splitext(os.path.basename(input_filepath))[0]
    output_filename = f"{base_name}_audio_extract.wav"
    output_path = os.path.join(output_folder, output_filename)

    cmd = [
        FFMPEG_BINARY,
        "-i", input_filepath,
        "-vn",
        "-acodec", "pcm_s16le",
        output_path,
        "-hide_banner",
        "-loglevel", "error"
    ]

    logging.info(f"Extracting audio for: {input_filepath}")
    start_time = time.time()
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Audio extraction failed for {input_filepath} - {e}")
        logging.error(f"Audio extraction failed for {input_filepath}")
    else:
        elapsed = time.time() - start_time
        logging.info(f"Audio extraction completed in {elapsed:.2f} seconds.")

# -------------------------------------------------------------------------------------
# WHISPER TRANSCRIPTION LOGIC
# -------------------------------------------------------------------------------------

def transcribe_wav_file(wav_filepath: str):
    """
    Runs Whisper on the given .wav file and appends the transcript to 'transcriptions.txt'.
    Uses the globally-loaded WHISPER_MODEL.
    Relies on Whisper's native segmentation (which includes timestamps).
    """
    filename = os.path.basename(wav_filepath)
    logging.info(f"Starting Whisper transcription for: {filename}")

    start_time = time.time()
    try:
        # If you want to force English, you can do:
        # result = WHISPER_MODEL.transcribe(wav_filepath, language='en')
        # but base model auto-detects English fairly well.
        result = WHISPER_MODEL.transcribe(wav_filepath, language='en')

        # 'result' will have a "segments" list with start, end, text
        segments = result.get("segments", [])

        # Append transcription to the single output file
        with open(TRANSCRIPTIONS_FILE, "a", encoding="utf-8") as tf:
            current_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tf.write(f"\n----- Transcription for {filename} ({current_dt}) -----\n")
            for seg in segments:
                seg_start = seg["start"]
                seg_end = seg["end"]
                seg_text = seg["text"].strip()
                # Example line: [0.00 - 4.32] Hello, this is segment text
                tf.write(f"[{seg_start:.2f} - {seg_end:.2f}] {seg_text}\n")
            tf.write(f"----- End of transcription for {filename} -----\n\n")

        total_time = time.time() - start_time
        logging.info(f"Transcription completed in {total_time:.2f} seconds.")
    except Exception as e:
        error_msg = f"Transcription failed for {filename}: {e}"
        logging.error(error_msg)
        log_error(error_msg)

# -------------------------------------------------------------------------------------
# WATCHDOG HANDLERS (VIDEOS & WAV FILES)
# -------------------------------------------------------------------------------------

class NewMP4Handler(FileSystemEventHandler):
    """
    Handles .mp4 detection in the WATCH_DIRECTORY,
    extracts frames & audio, logs results, etc.
    """
    def __init__(self, processed_files):
        super().__init__()
        self.processed_files = processed_files
        self.currently_processing = set()

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".mp4"):
            self.handle_new_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".mp4"):
            filename = os.path.basename(event.src_path)
            if filename in self.processed_files or filename in self.currently_processing:
                return
            if is_file_fully_written(event.src_path):
                self.handle_new_file(event.src_path)

    def handle_new_file(self, filepath: str):
        filename = os.path.basename(filepath)
        if filename in self.processed_files:
            logging.info(f"File '{filename}' was already processed. Skipping.")
            return
        if filename in self.currently_processing:
            logging.info(f"File '{filename}' is already being processed. Skipping.")
            return

        if not is_file_fully_written(filepath):
            logging.info(f"File '{filename}' is still growing. Will try later.")
            return

        self.currently_processing.add(filename)
        logging.info(f"Processing new file: {filename}")
        start_time = time.time()

        try:
            ensure_folders()

            # Extract frames -> screenshots folder
            extract_frames(filepath, SCREENSHOTS_PATH)

            # Extract audio -> sound folder
            extract_audio(filepath, SOUND_PATH)

            self.processed_files.add(filename)
            mark_file_as_processed(filename)

            total_time = time.time() - start_time
            logging.info(f"Completed processing for '{filename}' in {total_time:.2f} seconds.")
        except Exception as e:
            error_msg = f"Error processing {filename}: {e}"
            logging.error(error_msg)
            log_error(error_msg)
        finally:
            self.currently_processing.remove(filename)


class NewWAVHandler(FileSystemEventHandler):
    """
    Watches the SOUND_PATH folder for newly-created .wav files
    and transcribes them using Whisper.
    """
    def __init__(self):
        super().__init__()
        self.processed_wavs = set()
        self.currently_processing = set()

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".wav"):
            self.handle_new_wav(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".wav"):
            filename = os.path.basename(event.src_path)
            if filename in self.processed_wavs or filename in self.currently_processing:
                return
            if is_file_fully_written(event.src_path):
                self.handle_new_wav(event.src_path)

    def handle_new_wav(self, filepath: str):
        filename = os.path.basename(filepath)
        # Skip if we've done it before or are mid-processing:
        if filename in self.processed_wavs:
            logging.info(f"WAV '{filename}' was already transcribed. Skipping.")
            return
        if filename in self.currently_processing:
            logging.info(f"WAV '{filename}' is already being transcribed. Skipping.")
            return

        if not is_file_fully_written(filepath):
            logging.info(f"WAV '{filename}' is still growing. Will try later.")
            return

        self.currently_processing.add(filename)
        logging.info(f"Transcribing new WAV file: {filename}")
        start_time = time.time()

        try:
            ensure_folders()  # ensure text_extract folder, etc.

            # Transcribe with Whisper
            transcribe_wav_file(filepath)

            self.processed_wavs.add(filename)

            total_time = time.time() - start_time
            logging.info(f"Completed transcription for '{filename}' in {total_time:.2f} seconds.")
        except Exception as e:
            error_msg = f"Error transcribing WAV '{filename}': {e}"
            logging.error(error_msg)
            log_error(error_msg)
        finally:
            self.currently_processing.remove(filename)

# -------------------------------------------------------------------------------------
# STARTUP LOGIC
# -------------------------------------------------------------------------------------

def process_existing_mp4_files(handler):
    logging.info("Scanning for unprocessed MP4 files at startup...")
    for file_name in os.listdir(WATCH_DIRECTORY):
        if file_name.lower().endswith(".mp4") and file_name not in handler.processed_files:
            filepath = os.path.join(WATCH_DIRECTORY, file_name)
            if is_file_fully_written(filepath):
                handler.handle_new_file(filepath)
            else:
                logging.info(f"File '{file_name}' is still growing. It will be handled when stable.")

def process_existing_wav_files(handler):
    """
    Scan the SOUND_PATH folder for any existing .wav files
    that have not been transcribed yet.
    """
    logging.info("Scanning for existing .wav files in sound folder at startup...")
    if not os.path.exists(SOUND_PATH):
        return  # no folder => no files

    for file_name in os.listdir(SOUND_PATH):
        if file_name.lower().endswith(".wav"):
            filepath = os.path.join(SOUND_PATH, file_name)
            if is_file_fully_written(filepath):
                handler.handle_new_wav(filepath)
            else:
                logging.info(f"WAV file '{file_name}' is still growing. Will handle when stable.")

def main():
    # Session header in error log
    with open(ERROR_LOGFILE, "a", encoding="utf-8") as ef:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ef.write(f"\n---- New Session {current_time} ----\n")

    logging.info(f"Starting watch on directory: {WATCH_DIRECTORY}")

    # Ensure our subfolders exist (screenshots, sound, text_extract)
    ensure_folders()

    # Set up observer for MP4 files (video + audio extraction)
    processed_files = load_processed_files()
    mp4_handler = NewMP4Handler(processed_files)

    mp4_observer = Observer()
    mp4_observer.schedule(mp4_handler, WATCH_DIRECTORY, recursive=False)
    mp4_observer.start()

    # Also set up observer for WAV transcription
    wav_handler = NewWAVHandler()
    wav_observer = Observer()
    wav_observer.schedule(wav_handler, SOUND_PATH, recursive=False)
    wav_observer.start()

    # Handle existing .mp4 or .wav files at startup
    process_existing_mp4_files(mp4_handler)
    process_existing_wav_files(wav_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping directory watch.")
    finally:
        mp4_observer.stop()
        wav_observer.stop()
        mp4_observer.join()
        wav_observer.join()

if __name__ == "__main__":
    main()
