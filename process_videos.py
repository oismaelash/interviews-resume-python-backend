import os
import ollama
import whisper
import gc
import psutil
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# os.environ["OLLAMA_HOST"] = "127.0.0.1:11434"
print(os.environ["OLLAMA_HOST"])
# Initialize the Ollama client
client = ollama.Client()

VIDEOS_FOLDER = 'videos'
OUTPUT_FOLDER = os.path.join(VIDEOS_FOLDER, "results")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)



videos_with_error = []

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def cleanup_memory():
    """Force garbage collection to free memory"""
    gc.collect()

def extract_audio(video_path, audio_path):
    video = None
    try:
        video = VideoFileClip(video_path)
        # Get video duration in minutes
        duration_minutes = video.duration / 60
        video.audio.write_audiofile(audio_path, codec='mp3', verbose=False, logger=None)
        return duration_minutes
    finally:
        # Properly close video to free memory
        if video:
            video.close()
            del video
        cleanup_memory()

def get_duration_minutes(video_path):
    video = None
    try:
        video = VideoFileClip(video_path)
        return video.duration / 60
    finally:
        if video:
            video.close()
            del video
        cleanup_memory()

def transcribe_audio(audio_path):
    result = whisper_model.transcribe(audio_path)
    return result['text']

def summarize_text(text, duration_minutes):
    # Format duration to include in the prompt
    formatted_duration = f"{int(duration_minutes)} minutes" if duration_minutes >= 1 else f"{int(duration_minutes * 60)} seconds"
    
    prompt = f"""
        You are an assistant that generates professional interview resumes from structured data.
        Below is a JSON object with interview information. Your task is to transform this data into a clear, concise, and professional interview summary, highlighting the candidate’s profile, company context, and key takeaways.

        JSON:
        {{
            "interview_duration": "{formatted_duration}",
            "position": "",
            "seniority": [],
            "technologies": [],
            "company_name": "",
            "company_type": "",
            "candidate_summary": {{
                "experience": "",
                "technologies_used": [],
                "work_methodology": [],
                "salary_expectation": []
            }},
            "interview_summary": "",
            "interviewer_type": [],
            "language": []
        }}

        Output requirements:
        - Start with the basic details: interview duration, company name and type, position, and seniority.
        - Summarize the candidate’s profile: experience, technologies used, and work methodology.
        - Mention salary expectations clearly.
        - Add a short interview summary with evaluation of soft/hard skills.
        - Indicate interviewer type(s) and the language of the interview.
        - Keep it structured in professional report style (no bullet points unless necessary).

        Transcript:
        \"\"\"
        {text}
        \"\"\"
        """
    
    # Send the query to the model using Ollama client
    # prompt_from_env = os.getenv('INTERVIEW_PROMPT', '') + text
    try:
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt)
        return response.response.strip()
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return f"Error generating summary: {e}"

def just_summarize(transcription_path, summary_path, video_path, relative_video_path):
    print(f"Summarizing: {transcription_path}")
    text = open(transcription_path, 'r', encoding='utf-8').read()
    duration_minutes = get_duration_minutes(video_path)
    print(f"Duration: {duration_minutes}")
    summary = summarize_text(text, duration_minutes)
    print(f"Writing summary to {summary_path}")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"Finished: {relative_video_path}")
    print("--------------------------------")
    return
        

def process_video(relative_video_path):
    # relative_video_path can be just the file name or a path with subfolders
    base_name = os.path.splitext(os.path.basename(relative_video_path))[0]
    video_path = os.path.join(VIDEOS_FOLDER, relative_video_path)
    
    # Create output folder structure to keep organization
    video_output_folder = os.path.join(OUTPUT_FOLDER, os.path.dirname(relative_video_path))
    os.makedirs(video_output_folder, exist_ok=True)
    
    audio_path = os.path.join(video_output_folder, f"{base_name}.mp3")
    transcription_path = os.path.join(video_output_folder, f"{base_name}.txt")
    summary_path = os.path.join(video_output_folder, f"{base_name}_resume.md")

    print(f"Memory usage before processing: {get_memory_usage():.1f} MB")
    
    try:
        is_summarizing = os.getenv('JUST_SUMMARIZE', 'false').lower() == 'true'
        print(f"Just summarizing: {is_summarizing}")
        if is_summarizing:
            just_summarize(transcription_path, summary_path, video_path, relative_video_path)
            return
        
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
    finally:
        # Clean up memory after each video
        cleanup_memory()
        print(f"Memory usage after processing: {get_memory_usage():.1f} MB")

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
print(f"Found {len(videos_to_process)} videos to process")

# Define the model
# OLLAMA_MODEL = "deepseek-r1:8b"
# OLLAMA_MODEL = "interview-resume"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")
print(f"Loading Ollama model: {OLLAMA_MODEL}")

# if JUST_SUMMARIZE is true, whisper load model is not needed
if os.getenv('JUST_SUMMARIZE', 'false').lower() == 'true':
    print("Just summarizing, skipping video processing")
    exit()
else:
    # Use a smaller model to reduce memory usage
    # Options: tiny, base, small, medium, large, large-v2, large-v3
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
    print(f"Loading Whisper model: {WHISPER_MODEL}")
    whisper_model = whisper.load_model(WHISPER_MODEL)

# Option: only reprocess videos with previous error
reprocess_failures = os.getenv('REPROCESS_FAILURES', 'false').lower() == 'true'
if reprocess_failures:
    videos_to_process = load_previous_errors()

for i, video in enumerate(videos_to_process):
    print(f"\n=== Processing video {i+1}/{len(videos_to_process)}: {video} ===")
    
    # Check memory before processing
    memory_mb = get_memory_usage()
    if memory_mb > 6000:  # If using more than 6GB, force cleanup
        print(f"High memory usage detected ({memory_mb:.1f} MB), forcing cleanup...")
        cleanup_memory()
        memory_mb = get_memory_usage()
        print(f"Memory after cleanup: {memory_mb:.1f} MB")
    
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
