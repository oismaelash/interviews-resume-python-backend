# Memory Optimization for Video Processing

## Problem Fixed
Your script was being killed due to memory exhaustion. The main issues were:
1. Using the large Whisper model (`large-v3`) which requires significant memory
2. Not properly releasing video objects from memory
3. No memory monitoring or cleanup between videos

## Changes Made

### 1. Memory Management
- Added `psutil` for memory monitoring
- Added `gc` for garbage collection
- Added memory cleanup after each video processing
- Added memory usage logging

### 2. Whisper Model Optimization
- Changed default model from `large-v3` to `base` (much lower memory usage)
- Made model configurable via `WHISPER_MODEL` environment variable
- Model options: `tiny`, `base`, `small`, `medium`, `large`, `large-v2`, `large-v3`

### 3. Video Processing Improvements
- Properly close and delete video objects after use
- Added try/finally blocks to ensure cleanup even on errors
- Added memory checks before processing each video

### 4. Better Error Handling
- Added memory usage logging before and after each video
- Added high memory usage detection and cleanup
- Improved progress tracking

## Environment Variables

Create a `.env` file with these options:

```bash
# Ollama model to use for summarization
OLLAMA_MODEL=interview-resume

# Whisper model size (tiny, base, small, medium, large, large-v2, large-v3)
# Use 'base' for lower memory usage, 'large-v3' for best accuracy
WHISPER_MODEL=base

# Set to 'true' to only summarize existing transcriptions
JUST_SUMMARIZE=false

# Set to 'true' to reprocess only videos that previously failed
REPROCESS_FAILURES=false
```

## Usage

1. **For low memory systems** (recommended):
   ```bash
   export WHISPER_MODEL=base
   python process_videos.py
   ```

2. **For better accuracy** (if you have enough memory):
   ```bash
   export WHISPER_MODEL=large-v3
   python process_videos.py
   ```

3. **To only summarize existing transcriptions**:
   ```bash
   export JUST_SUMMARIZE=true
   python process_videos.py
   ```

## Memory Usage Comparison

- `tiny`: ~1GB RAM
- `base`: ~1GB RAM  
- `small`: ~2GB RAM
- `medium`: ~5GB RAM
- `large`: ~10GB RAM
- `large-v2`: ~10GB RAM
- `large-v3`: ~10GB RAM

The script now monitors memory usage and will show you the current usage before and after processing each video.
