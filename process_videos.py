import os
from openai import OpenAI
import whisper
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

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
        os.environ.get("PROMPT_ENTREVISTA") +
        f"\n\nInterview duration: {formatted_duration}\n\n" +
        f"{text}"
    )
    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL"),
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
    # return "Summary disabled - OpenAI commented"

def process_video(relative_video_path):
    # relative_video_path can be just the file name or a path with subfolders
    base_name = os.path.splitext(os.path.basename(relative_video_path))[0]
    video_path = os.path.join(VIDEOS_FOLDER, relative_video_path)
    
    # Create output folder structure to keep organization
    video_output_folder = os.path.join(OUTPUT_FOLDER, os.path.dirname(relative_video_path))
    os.makedirs(video_output_folder, exist_ok=True)
    
    audio_path = os.path.join(video_output_folder, f"{base_name}.mp3")
    transcription_path = os.path.join(video_output_folder, f"{base_name}.txt")
    summary_path = os.path.join(video_output_folder, f"{base_name}_summary.txt")

    try:
        print(f"Starting: {relative_video_path}")
        # Extract audio and get duration
        duration_minutes = extract_audio(video_path, audio_path)
        text = transcribe_audio(audio_path)
        with open(transcription_path, 'w', encoding='utf-8') as f:
            f.write(text)

        # Pass the duration to the summary function
        # summary = summarize_text(text, duration_minutes)
        # with open(summary_path, 'w', encoding='utf-8') as f:
        #     f.write(summary)

        print(f"Finished: {relative_video_path}")
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
reprocess_failures = os.getenv('REPROCESSAR_FALHAS', 'false').lower() == 'true'
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
