import moviepy.editor as mp

def extract_audio(video_file_path: str, output_wav_path: str) -> bool:
    """
    Extracts audio from a video file and saves it as a WAV file.

    Args:
        video_file_path: The absolute path to the video file.
        output_wav_path: The desired absolute path for the output WAV audio file.

    Returns:
        True if audio extraction is successful, False otherwise.
    """
    try:
        # Load the video file
        video_clip = mp.VideoFileClip(video_file_path)

        # Extract the audio
        audio_clip = video_clip.audio

        # Write the audio to the output WAV file
        # Use codec 'pcm_s16le' for compatibility with STT systems
        audio_clip.write_audiofile(output_wav_path, codec='pcm_s16le')

        # Close the clips to release resources
        audio_clip.close()
        video_clip.close()

        return True

    except FileNotFoundError:
        print(f"Error: Video file not found at {video_file_path}")
        return False
    except Exception as e:
        print(f"An error occurred during audio extraction: {e}")
        if 'audio_clip' in locals() and audio_clip:
            audio_clip.close()
        if 'video_clip' in locals() and video_clip:
            video_clip.close()
        return False
