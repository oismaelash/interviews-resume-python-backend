import os
import ollama
import whisper
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Ollama client
client = ollama.Client()

# Define the model
# OLLAMA_MODEL = "deepseek-r1:8b"
# OLLAMA_MODEL = "interview-resume"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")

VIDEOS_FOLDER = 'videos'
OUTPUT_FOLDER = os.path.join(VIDEOS_FOLDER, "results")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

whisper_model = whisper.load_model("base")

videos_with_error = []

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    # Get video duration in minutes
    duration_minutes = video.duration / 60
    video.audio.write_audiofile(audio_path, codec='mp3', verbose=False, logger=None)
    return duration_minutes

def transcribe_audio(audio_path):
    result = whisper_model.transcribe(audio_path)
    return result['text']

def summarize_text(text, duration_minutes):
    # Format duration to include in the prompt
    formatted_duration = f"{int(duration_minutes)} minutes" if duration_minutes >= 1 else f"{int(duration_minutes * 60)} seconds"
    
    prompt = (
        f"Interview duration: {formatted_duration}\n\n" +
        os.environ.get("INTERVIEW_PROMPT") +
        f"{text}"
    )
    
    # Send the query to the model using Ollama client
    try:
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt)
        return response.response.strip()
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return f"Error generating summary: {e}"

def process_video(relative_video_path):
    # relative_video_path can be just the file name or a path with subfolders
    base_name = os.path.splitext(os.path.basename(relative_video_path))[0]
    video_path = os.path.join(VIDEOS_FOLDER, relative_video_path)
    
    # Create output folder structure to keep organization
    video_output_folder = os.path.join(OUTPUT_FOLDER, os.path.dirname(relative_video_path))
    os.makedirs(video_output_folder, exist_ok=True)
    
    audio_path = os.path.join(video_output_folder, f"{base_name}.mp3")
    transcription_path = os.path.join(video_output_folder, f"{base_name}.txt")
    summary_path = os.path.join(video_output_folder, f"{base_name}.json")

    try:
        print(f"Starting: {relative_video_path}")
        # Extract audio and get duration
        print(f"Extracting audio from {video_path}")
        duration_minutes = extract_audio(video_path, audio_path)
        print(f"Transcribing audio from {audio_path}")
        text = transcribe_audio(audio_path)
        print(f"Writing transcription to {transcription_path}")
        with open(transcription_path, 'w', encoding='utf-8') as f:
            f.write(text)

        # Pass the duration to the summary function
        # print(f"Summarizing text from {text}")
        summary = summarize_text(text, duration_minutes)
        print(f"Writing summary to {summary_path}")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"Finished: {relative_video_path}")
        print("--------------------------------")
    except Exception as e:
        print(f"[ERROR] {relative_video_path} - {e}")
        videos_with_error.append(relative_video_path)

# Allows to repeat only videos with error
def load_previous_errors():
    error_txt = os.path.join(OUTPUT_FOLDER, 'errors.txt')
    if os.path.exists(error_txt):
        with open(error_txt, 'r') as f:
            return [line.strip() for line in f.readlines()]
    return []

def find_videos_recursively(folder):
    """Finds all .mp4 videos in the folder and subfolders"""
    videos = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.mp4') and not file.startswith('.'):
                # Keep the path relative to the videos folder
                relative_path = os.path.relpath(os.path.join(root, file), folder)
                videos.append(relative_path)
    return videos

videos_to_process = find_videos_recursively(VIDEOS_FOLDER)

# Option: only reprocess videos with previous error
reprocess_failures = os.getenv('REPROCESS_FAILURES', 'false').lower() == 'true'
if reprocess_failures:
    videos_to_process = load_previous_errors()

for video in videos_to_process:
    process_video(video)

# Save errors at the end
if videos_with_error:
    with open(os.path.join(OUTPUT_FOLDER, 'errors.txt'), 'w') as f:
        for name in videos_with_error:
            f.write(f"{name}\n")

print("\n--- PROCESSING COMPLETED ---")
if videos_with_error:
    print(f"{len(videos_with_error)} videos with error. Listed in: results/errors.txt")
else:
    print("All videos were processed successfully!")
