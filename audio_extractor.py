import moviepy.editor as mp
import logging # Recommended for better logging than print

# It's good practice to get a logger instance rather than using root logger directly via print
logger = logging.getLogger(__name__)

def extract_audio(video_file_path: str, output_wav_path: str) -> bool:
    """
    Extracts audio from a video file and saves it as a WAV file.

    Args:
        video_file_path: The absolute path to the video file.
        output_wav_path: The desired absolute path for the output WAV audio file.

    Returns:
        True if audio extraction is successful, False otherwise.
    """
    video_clip = None
    audio_clip = None
    success = False
    try:
        # Load the video file
        video_clip = mp.VideoFileClip(video_file_path)

        # Extract the audio
        # VideoFileClip.audio can be None if the video has no audio track
        if video_clip.audio is None:
            logger.error(f"Video file {video_file_path} has no audio track.")
            # success remains False
        else:
            audio_clip = video_clip.audio
            # Write the audio to the output WAV file
            # Use codec 'pcm_s16le' for compatibility with STT systems
            audio_clip.write_audiofile(output_wav_path, codec='pcm_s16le', logger=None) # Moviepy can be noisy, suppress its default logger for this call if desired or pass 'bar'
            logger.info(f"Audio successfully extracted to {output_wav_path}")
            success = True

    except FileNotFoundError:
        logger.error(f"Error: Video file not found at {video_file_path}")
        # success remains False
    except Exception as e:
        # Log the full traceback for better debugging
        logger.exception(f"An error occurred during audio extraction for {video_file_path}: {e}")
        # success remains False
    finally:
        # Ensure clips are closed if they were opened
        if audio_clip:
            try:
                audio_clip.close()
            except Exception as e_ac:
                logger.error(f"Error closing audio_clip: {e_ac}")
        if video_clip:
            try:
                video_clip.close()
            except Exception as e_vc:
                logger.error(f"Error closing video_clip: {e_vc}")
    
    return success
