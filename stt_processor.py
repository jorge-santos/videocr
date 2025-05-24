import whisper
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Language mapping for Whisper
# Updated to reflect the new UI language list and ensure correct Whisper identifiers.
WHISPER_LANGUAGE_MAPPING = {
    "English": "english",
    "Mandarin Chinese": "chinese",
    "Hindi": "hindi",
    "Spanish": "spanish",
    "Modern Standard Arabic": "arabic",
    "French": "french",
    "Portuguese (European)": "portuguese",
    "Portuguese (Brazilian)": "portuguese",
    "Russian": "russian",
    "Indonesian": "indonesian",
    "Urdu": "urdu",
    "Standard German": "german",
    "Japanese": "japanese",
    "Vietnamese": "vietnamese",
    "Turkish": "turkish",
    "Italian": "italian",
    "Korean": "korean",
    "Romanian": "romanian",
    "Greek": "greek",
    "Persian": "persian",
    # Languages removed from UI and mapping:
    # "Bengali", "Nigerian Pidgin", "Egyptian Arabic", "Marathi", "Telugu", "Hausa"
}

def transcribe_audio_with_whisper(audio_file_path: str, language_name: str, model_name: str = "base") -> tuple[dict | None, str | None]:
    """
    Transcribes an audio file using OpenAI Whisper.

    Args:
        audio_file_path: Absolute path to the WAV audio file.
        language_name: Common language name (e.g., "English", "Hindi") from the UI.
        model_name: Name of the Whisper model to use (e.g., "tiny", "base", "small", "medium", "large").

    Returns:
        A tuple containing the transcription result dictionary and None on success,
        or (None, error_message) on failure.
    """
    mapped_language_name = None
    if language_name:
        mapped_language_name = WHISPER_LANGUAGE_MAPPING.get(language_name)
        if not mapped_language_name and language_name not in WHISPER_LANGUAGE_MAPPING.keys() :
             # If language_name is provided but not in our explicit map,
             # we pass None to Whisper for auto-detection as per instructions.
            logging.info(f"Language '{language_name}' not in explicit map. Attempting auto-detection by Whisper.")
        elif not mapped_language_name and language_name in WHISPER_LANGUAGE_MAPPING.keys():
            # This case would mean the mapping value itself is None or empty for a language in the map.
            # For the current map, all defined keys have non-empty string values.
            logging.warning(f"Language '{language_name}' is in map but mapped to None/empty. Attempting auto-detection.")


    device_to_use = "cpu"
    model = None
    try:
        if torch.cuda.is_available():
            device_to_use = "cuda"
            logging.info("CUDA available. Attempting to load model on GPU.")
            model = whisper.load_model(model_name, device=device_to_use)
            logging.info(f"Whisper model '{model_name}' loaded successfully on GPU.")
        else:
            logging.info("CUDA not available. Loading model on CPU.")
            model = whisper.load_model(model_name, device=device_to_use)
            logging.info(f"Whisper model '{model_name}' loaded successfully on CPU.")

    except Exception as e:
        if device_to_use == "cuda":
            logging.warning(f"Failed to load model on CUDA: {e}. Falling back to CPU.")
            device_to_use = "cpu"
            try:
                model = whisper.load_model(model_name, device=device_to_use)
                logging.info(f"Whisper model '{model_name}' loaded successfully on CPU after fallback.")
            except Exception as cpu_e:
                return None, f"Error loading Whisper model '{model_name}' on CPU after CUDA fallback: {cpu_e}"
        else:
            return None, f"Error loading Whisper model '{model_name}' on CPU: {e}"

    if not model:
        return None, "Whisper model could not be loaded."

    try:
        logging.info(f"Starting transcription for {audio_file_path} with language: {mapped_language_name or 'auto-detect'} on device: {device_to_use}")
        
        # Use fp16=True if on CUDA for better performance, False on CPU.
        use_fp16 = True if device_to_use == "cuda" else False
        logging.info(f"fp16 mode for transcription: {use_fp16}")

        # For language, Whisper expects None for auto-detection if the language is not specified or not found in map.
        transcription_result = model.transcribe(audio_file_path, language=mapped_language_name, fp16=use_fp16)
        logging.info(f"Transcription successful for {audio_file_path}")
        return transcription_result, None
    except FileNotFoundError:
        return None, f"Error: Audio file not found at {audio_file_path}"
    except Exception as e:
        return None, f"Error during audio transcription: {e}"
