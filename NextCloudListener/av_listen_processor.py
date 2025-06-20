import time
import os
import subprocess
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# -------------------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------------------

# Directory to watch (the folder where new .mp4 files will appear).
WATCH_DIRECTORY = r"C:\Users\cicai\Nextcloud\InstantUpload\gps"

# The name (or subfolder) where screenshots and sound will go -- but these will now
# be placed inside the script's directory, not the watch directory.
SCREENSHOTS_FOLDER = "screenshots"
SOUND_FOLDER = "sound"

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
# DERIVE DIRECTORIES
# -------------------------------------------------------------------------------------

# The directory where this script is running:
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Final absolute paths for screenshots and sound folders:
SCREENSHOTS_PATH = os.path.join(SCRIPT_DIR, SCREENSHOTS_FOLDER)
SOUND_PATH = os.path.join(SCRIPT_DIR, SOUND_FOLDER)

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
    """
    Use ffprobe to fetch the total duration (in seconds) of a video.
    """
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
    """
    Check if a file is still being written to by comparing its size over two intervals.
    Returns True if the size is stable (i.e., the file is likely fully written).
    """
    initial_size = os.path.getsize(filepath)
    time.sleep(wait_time)
    new_size = os.path.getsize(filepath)
    return initial_size == new_size

def ensure_subfolders():
    """
    Create the screenshots and sound subfolders (inside the script's directory) if they don't exist.
    """
    if not os.path.exists(SCREENSHOTS_PATH):
        os.makedirs(SCREENSHOTS_PATH)
        logging.info(f"Created folder: {SCREENSHOTS_PATH}")

    if not os.path.exists(SOUND_PATH):
        os.makedirs(SOUND_PATH)
        logging.info(f"Created folder: {SOUND_PATH}")

def load_processed_files() -> set:
    """
    Load the names of files that have already been processed (from PROCESSED_LOGFILE),
    returning a set for quick membership checks.
    """
    processed_files = set()
    if os.path.exists(PROCESSED_LOGFILE):
        with open(PROCESSED_LOGFILE, "r", encoding="utf-8") as f:
            for line in f:
                file_name = line.strip()
                if file_name:
                    processed_files.add(file_name)
    return processed_files

def mark_file_as_processed(filename: str):
    """
    Append the given filename to the log of processed files (PROCESSED_LOGFILE).
    """
    with open(PROCESSED_LOGFILE, "a", encoding="utf-8") as f:
        f.write(filename + "\n")

# -------------------------------------------------------------------------------------
# EXTRACTION FUNCTIONS
# -------------------------------------------------------------------------------------

def extract_frames(input_filepath: str, output_folder: str):
    """
    Extract 1 frame every 30 seconds at ~30s intervals using fps=1/30.
    """
    # Gather some info about the video:
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
# WATCHDOG HANDLER
# -------------------------------------------------------------------------------------

class NewMP4Handler(FileSystemEventHandler):
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

        # Mark the file as in progress
        self.currently_processing.add(filename)
        logging.info(f"Processing new file: {filename}")
        start_time = time.time()

        try:
            # Ensure subfolders (screenshots, sound) exist in the script's directory
            ensure_subfolders()

            # Extract frames into the script's screenshots folder
            extract_frames(filepath, SCREENSHOTS_PATH)

            # Extract audio into the script's sound folder
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

# -------------------------------------------------------------------------------------
# INITIAL PROCESSING OF EXISTING FILES
# -------------------------------------------------------------------------------------

def process_existing_files(handler):
    logging.info("Scanning for unprocessed MP4 files at startup...")
    for file_name in os.listdir(WATCH_DIRECTORY):
        if file_name.lower().endswith(".mp4") and file_name not in handler.processed_files:
            filepath = os.path.join(WATCH_DIRECTORY, file_name)
            if is_file_fully_written(filepath):
                handler.handle_new_file(filepath)
            else:
                logging.info(f"File '{file_name}' is still growing. It will be handled when stable.")

# -------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------

def main():
    # Add a session header to the error log
    with open(ERROR_LOGFILE, "a", encoding="utf-8") as ef:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ef.write(f"\n---- New Session {current_time} ----\n")

    logging.info(f"Starting watch on directory: {WATCH_DIRECTORY}")

    processed_files = load_processed_files()

    event_handler = NewMP4Handler(processed_files)
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    observer.start()

    # Process any existing .mp4 files in the watch directory that are unprocessed
    process_existing_files(event_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping directory watch.")
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()
