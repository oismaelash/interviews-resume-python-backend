# Interview Video Processor

A Python application that automatically processes interview videos by extracting audio, transcribing speech using OpenAI's Whisper, and generating intelligent summaries using OpenAI's GPT models.

## Features

- **Audio Extraction**: Extracts audio from MP4 video files using MoviePy
- **Speech Transcription**: Converts audio to text using OpenAI's Whisper model
- **Intelligent Summarization**: Generates comprehensive summaries using OpenAI's GPT models
- **Batch Processing**: Processes multiple videos automatically
- **Error Handling**: Tracks failed videos and allows reprocessing
- **Docker Support**: Containerized for easy deployment

## Project Structure

```
interviews-resume/
├── process_videos.py      # Main processing script
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── videos/               # Input video directory
│   ├── *.mp4            # Video files to process
│   └── resultados/      # Output directory
│       ├── *.mp3        # Extracted audio files
│       ├── *.txt        # Transcription files
│       ├── *_resumo.txt # Summary files
│       └── erros.txt    # Error log
└── README.md            # This file
```

## Prerequisites

- Python 3.10+
- FFmpeg (for audio processing)
- OpenAI API key
- Docker (optional, for containerized deployment)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd interviews-resume
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

### Docker Installation

1. Build the Docker image:
```bash
docker build -t process-videos .
```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
PROMPT_ENTREVISTA=Your custom prompt for interview summarization
REPROCESSAR_FALHAS=false
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: OpenAI model to use for summarization (default: gpt-3.5-turbo)
- `PROMPT_ENTREVISTA`: Custom prompt template for interview summarization
- `REPROCESSAR_FALHAS`: Set to 'true' to reprocess only failed videos

## Usage

### Local Usage

1. Place your MP4 video files in the `videos/` directory
2. Run the processing script:
```bash
python process_videos.py
```

### Docker Usage

1. Place your MP4 video files in the `videos/` directory
2. Run the container:
```bash
docker run -v "$(pwd)/videos":/app/videos process-videos
```

## Output

The application generates the following files in the `videos/resultados/` directory:

- `{filename}.mp3`: Extracted audio file
- `{filename}.txt`: Full transcription
- `{filename}_resumo.txt`: AI-generated summary
- `erros.txt`: List of videos that failed to process (if any)

## How It Works

1. **Video Processing**: Scans the `videos/` directory for MP4 files
2. **Audio Extraction**: Extracts audio from each video using MoviePy
3. **Transcription**: Converts audio to text using OpenAI's Whisper model
4. **Summarization**: Generates intelligent summaries using OpenAI's GPT models
5. **Error Handling**: Tracks and logs any processing failures

## Error Handling

- Failed videos are logged in `videos/resultados/erros.txt`
- Set `REPROCESSAR_FALHAS=true` to retry only failed videos
- The application continues processing other videos even if some fail

## Customization

### Custom Prompts

Modify the `PROMPT_ENTREVISTA` environment variable to customize how interviews are summarized. The prompt receives:
- The full transcription text
- The video duration in minutes/seconds

### Whisper Model

The application uses the "base" Whisper model by default. You can modify this in `process_videos.py`:
```python
modelo_whisper = whisper.load_model("base")  # Change to "small", "medium", "large", etc.
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed and in your PATH
2. **OpenAI API errors**: Verify your API key and check your usage limits
3. **Memory issues**: For large videos, consider using a smaller Whisper model
4. **Docker volume mounting**: Ensure the videos directory path is correct

### Performance Tips

- Use smaller Whisper models for faster processing
- Process videos in smaller batches for large datasets
- Monitor OpenAI API usage to avoid rate limits

## License

This project is open source. Please check the license file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For support or questions, please open an issue in the repository.
