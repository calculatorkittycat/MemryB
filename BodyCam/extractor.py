import os
import subprocess

def create_output_folder(base_folder):
    output_folder = os.path.join(base_folder, "extracted")
    os.makedirs(output_folder, exist_ok=True)
    return output_folder

def get_video_duration(file_path):
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError:
        print(f"Failed to get duration for {file_path}")
        return 0

def extract_frames(input_folder, output_folder):
    mov_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(".mov")])
    frame_counter = 1

    for mov_file in mov_files:
        input_path = os.path.join(input_folder, mov_file)
        duration = get_video_duration(input_path)

        if duration < 20:
            print(f"Skipping {mov_file}: Duration too short for extraction.")
            continue

        output_template = os.path.join(output_folder, f"temp_%04d.jpg")

        try:
            # Use ffmpeg to extract frames every 20 seconds
            command = [
                "ffmpeg",
                "-i", input_path,
                "-vf", "fps=1/20",
                output_template
            ]
            subprocess.run(command, check=True)

            # Rename files to sequential numbers
            extracted_files = sorted([f for f in os.listdir(output_folder) if f.startswith("temp_") and f.endswith(".jpg")])
            for file in extracted_files:
                os.rename(
                    os.path.join(output_folder, file),
                    os.path.join(output_folder, f"{frame_counter}.jpg")
                )
                frame_counter += 1
        except subprocess.CalledProcessError as e:
            print(f"Error extracting frames from {mov_file}: {e}")

def combine_audio(input_folder, output_folder):
    mov_files = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(".mov")])
    audio_list_file = os.path.join(output_folder, "file_list.txt")

    # Create a file list for ffmpeg
    with open(audio_list_file, "w") as f:
        for mov_file in mov_files:
            f.write(f"file '{mov_file}'\n")

    output_audio = os.path.join(output_folder, "OUTPUT.wav")

    try:
        # Combine audio from all .mov files into a single .wav
        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", audio_list_file,
            "-c", "copy",
            output_audio
        ]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error combining audio: {e}")

if __name__ == "__main__":
    input_folder = "D:\\DCIM"
    output_folder = create_output_folder(input_folder)

    print("Extracting frames from .mov files...")
    extract_frames(input_folder, output_folder)

    print("Combining audio from .mov files...")
    combine_audio(input_folder, output_folder)

    print(f"Processing complete. Output folder: {output_folder}")
