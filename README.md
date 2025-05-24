# AI Subtitle Generator

## 1. Overview
A brief description of the application: This Python application provides a graphical user interface (GUI) to generate subtitles (SRT or ASS format) from the audio track of a video file using the OpenAI Whisper speech-to-text model. It supports multiple languages and is optimized for use with NVIDIA GPUs.

## 2. System Requirements
- **Operating System:** Windows 10 (Tested on this OS).
- **Python:** Python 3.8 - 3.11 recommended.
- **Hardware (Recommended for optimal performance):**
    - RAM: 16GB+ (48GB available on test machine)
    - CPU: Modern multi-core CPU (e.g., Intel Core i5 9th gen or equivalent/better)
    - GPU: NVIDIA GPU with CUDA support (e.g., RTX 3060 12GB or similar/better) for significantly faster processing. CPU-only mode is also supported but will be much slower.
- **Key Dependencies (Software):**
    - **FFmpeg:** This is **CRITICAL**. FFmpeg must be installed on your system and accessible from the command line (i.e., added to your system's PATH environment variable).
        - Download FFmpeg from: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
    - **NVIDIA CUDA Toolkit (Optional, for GPU acceleration):** If you have an NVIDIA GPU and want the best performance, install the CUDA Toolkit version compatible with PyTorch (which Whisper uses).
        - Download CUDA Toolkit from: [https://developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads)
        - *The application will automatically attempt to use the GPU if CUDA is correctly set up and fall back to CPU otherwise.* An informational comment about this is included in `main_gui.py`.

## 3. Setup Instructions
1.  **Create a Virtual Environment (Recommended):**
    Open a command prompt or PowerShell in the project's root directory (where this README is located).
    ```bash
    python -m venv venv
    ```
2.  **Activate the Virtual Environment:**
    ```bash
    venv\Scripts\activate
    ```
3.  **Install Python Dependencies:**
    Ensure `requirements.txt` is in the same directory.
    ```bash
    pip install -r requirements.txt
    ```
    This will install `openai-whisper`, `moviepy`, `pysrt`, and their dependencies (like `torch`).

## 4. Running the Application
1.  Make sure your virtual environment is activated.
2.  Navigate to the project's root directory in your command prompt or PowerShell.
3.  Run the main GUI script:
    ```bash
    python main_gui.py
    ```

## 5. How to Use
1.  **Browse for Video:** Click the "Browse..." button to select your video file.
2.  **Select Language:** Choose the language spoken in the video from the dropdown menu.
    - *Note on Portuguese:* "Portuguese (European)" and "Portuguese (Brazilian)" options are provided for clarity; both use Whisper's general "portuguese" model. The transcription will reflect the dialect in the audio.
3.  **Choose Output Format:** Select either SRT or ASS.
4.  **Generate Subtitles:** Click the "Generate Subtitles" button.
    - The process may take some time, especially for long videos or if running on CPU. The GUI will show progress and status updates.
    - The first time you use a specific Whisper model or language, the model files will be downloaded, which can take a while depending on your internet speed. Subsequent uses will be faster as the model will be cached.
5.  **Output:** The generated subtitle file (.srt or .ass) will be saved in the same directory as the input video file, with the same base name.

## 6. Troubleshooting & Notes
- **FFmpeg Not Found:** The application checks for FFmpeg at startup. If it's not found or not in PATH, an error message will be displayed, and the generation feature will be disabled. Please ensure FFmpeg is correctly installed.
- **GPU Not Used:** If you have an NVIDIA GPU but it's not being used (check Task Manager > Performance > GPU, or use `nvidia-smi` if familiar):
    - Ensure your NVIDIA drivers are up to date.
    - Ensure you have installed the correct CUDA Toolkit version compatible with the PyTorch version that `openai-whisper` installed.
    - The application logs a message to the console if it falls back to CPU mode.
- **Model Downloads:** Whisper models are downloaded to a cache directory (usually `~/.cache/whisper` or as per Whisper's documentation).
- **Permissions:** Ensure the application has read permissions for the input video and write permissions for the directory where the video is located (to save the subtitle file and temporary audio).
