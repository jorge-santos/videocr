import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import tempfile
import logging
import subprocess # Added for FFmpeg check

# Informational comment for users:
# For NVIDIA GPU acceleration with Whisper, ensure you have the CUDA Toolkit installed
# that is compatible with your PyTorch version. PyTorch is installed as a dependency
# of openai-whisper. If CUDA is not set up correctly, Whisper will fall back to CPU.

# Assuming these files are in the same directory or Python path
from audio_extractor import extract_audio
from stt_processor import transcribe_audio_with_whisper
from subtitle_generator import generate_srt, generate_ass

# Configure basic logging for the application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Updated LANGUAGES list as per new requirements
LANGUAGES = [
    "English", "Mandarin Chinese", "Hindi", "Spanish", "Modern Standard Arabic", 
    "French", "Portuguese (European)", "Portuguese (Brazilian)", "Russian", 
    "Indonesian", "Urdu", "Standard German", "Japanese", "Vietnamese", "Turkish",
    "Italian", "Korean", "Romanian", "Greek", "Persian"
]

def check_ffmpeg() -> bool:
    """Checks if FFmpeg is installed and accessible."""
    try:
        # For Windows, use CREATE_NO_WINDOW to prevent console popup
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True, text=True, check=False, # check=False to handle non-zero exit codes manually
            creationflags=creation_flags
        )
        if result.returncode == 0:
            logging.info("FFmpeg found.")
            return True
        else:
            logging.error(f"FFmpeg check failed. Return code: {result.returncode}. Stderr: {result.stderr}")
            return False
    except FileNotFoundError:
        logging.error("FFmpeg command not found. Ensure FFmpeg is installed and in PATH.")
        return False
    except Exception as e:
        logging.error(f"An error occurred while checking for FFmpeg: {e}")
        return False

class SubtitleApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Subtitle Generator")
        self.root.geometry("700x550")

        self.file_path_var = tk.StringVar()
        self.language_var = tk.StringVar(value="English") # Default language
        self.output_format_var = tk.StringVar(value="srt") # Default format

        self.processing_queue = queue.Queue()
        self.processing_thread = None

        # --- UI Elements ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        file_frame = ttk.LabelFrame(main_frame, text="Video File", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(file_frame, text="Video File:").pack(side=tk.LEFT, padx=5)
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50, state="readonly")
        self.file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.browse_button = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        options_frame = ttk.Frame(main_frame, padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        lang_frame = ttk.Frame(options_frame)
        lang_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT, padx=5)
        self.language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, values=LANGUAGES, state="readonly", width=20)
        self.language_combo.pack(side=tk.LEFT, padx=5)
        if "English" in LANGUAGES:
            self.language_combo.set("English")
        elif LANGUAGES: # If English is not there, set to the first available language
            self.language_combo.set(LANGUAGES[0])


        format_frame = ttk.Frame(options_frame)
        format_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=5)
        self.srt_radio = ttk.Radiobutton(format_frame, text="SRT", variable=self.output_format_var, value="srt")
        self.srt_radio.pack(side=tk.LEFT, padx=5)
        self.ass_radio = ttk.Radiobutton(format_frame, text="ASS", variable=self.output_format_var, value="ass")
        self.ass_radio.pack(side=tk.LEFT, padx=5)

        self.generate_button = ttk.Button(main_frame, text="Generate Subtitles", command=self.start_processing, style="Accent.TButton")
        self.generate_button.pack(pady=10, fill=tk.X)
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 12, "bold"))

        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        self.status_label_var = tk.StringVar(value="Status: Idle")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_label_var, relief=tk.SUNKEN, padding=5)
        self.status_label.pack(fill=tk.X, pady=5)

        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ui_elements_to_toggle = [
            self.browse_button, self.language_combo, self.srt_radio,
            self.ass_radio, self.generate_button, self.file_entry
        ]

        # FFmpeg Check
        if not check_ffmpeg():
            messagebox.showerror("FFmpeg Not Found", "FFmpeg is not found. Please install FFmpeg and ensure it's in your system's PATH for the application to work correctly.")
            self.generate_button.config(state="disabled")
            self.log_message("CRITICAL: FFmpeg not found. Subtitle generation disabled.")
        else:
            self.log_message("FFmpeg found and accessible.")


    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=(("Video files", "*.mp4 *.mkv *.avi *.mov"), ("All files", "*.*"))
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.log_message(f"Selected video file: {file_path}")

    def update_status(self, message):
        self.status_label_var.set(f"Status: {message}")
        # self.log_message(message) # Avoid duplicate logging if already logged by caller

    def update_progress(self, value):
        self.progress_bar["value"] = value

    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        logging.info(message)

    def toggle_ui_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        # Special handling for readonly Entry
        if self.file_entry:
          self.file_entry.config(state="readonly" if enabled else "disabled")

        for element in self.ui_elements_to_toggle:
            if element != self.file_entry and hasattr(element, 'config'):
                element.config(state=state)

    def start_processing(self):
        video_path = self.file_path_var.get()
        if not video_path:
            messagebox.showerror("Error", "Please select a video file first.")
            return
        if not os.path.exists(video_path):
            messagebox.showerror("Error", f"Video file not found: {video_path}")
            return
        
        # Re-check FFmpeg in case it was disabled initially and user fixed it.
        # Or, if it was available and then removed.
        if not check_ffmpeg():
            messagebox.showerror("FFmpeg Not Found", "FFmpeg is required. Please ensure it's installed and in PATH.")
            self.generate_button.config(state="disabled") # Keep it disabled
            return
        else: # If FFmpeg becomes available, ensure button is enabled (if it was previously disabled)
            if self.generate_button['state'] == 'disabled':
                 self.generate_button.config(state="normal")


        self.toggle_ui_state(False)
        self.update_status("Starting...")
        self.log_message("Processing started...")
        self.update_progress(0)
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END) # Clear previous logs from text area
        self.log_text.config(state="disabled")
        self.log_message("Cleared previous logs. Starting new process...")


        self.processing_thread = threading.Thread(
            target=self.process_video_thread,
            args=(video_path, self.language_var.get(), self.output_format_var.get()),
            daemon=True
        )
        self.processing_thread.start()
        self.root.after(100, self.check_queue)

    def check_queue(self):
        try:
            while True:
                message_data = self.processing_queue.get_nowait()
                msg_type = message_data.get('type')
                value = message_data.get('value')

                if msg_type == 'status':
                    self.update_status(value)
                    self.log_message(f"Status update: {value}")
                elif msg_type == 'progress':
                    self.update_progress(value)
                elif msg_type == 'log':
                    self.log_message(value)
                elif msg_type == 'error':
                    messagebox.showerror("Processing Error", value)
                    self.update_status(f"Error occurred. Check logs.") # Generic status
                    self.log_message(f"ERROR: {value}") # Detailed error in log
                    # Error occurred, processing likely stopped or will stop. UI will be re-enabled by 'finish'.
                elif msg_type == 'finish':
                    is_error = message_data.get('is_error', False)
                    if not is_error:
                        self.update_status("Processing finished successfully.")
                        self.log_message("All operations completed successfully.")
                        if self.progress_bar["value"] < 100 : # Ensure 100% on success
                            self.update_progress(100)
                    else:
                        self.update_status("Processing finished with errors. Check logs.")
                        self.log_message("Operations finished, but errors were encountered.")
                    self.toggle_ui_state(True)
                    return # Stop checking queue
        except queue.Empty:
            pass
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.root.after(100, self.check_queue)
        elif not (self.processing_thread and self.processing_thread.is_alive()):
            # Thread finished but might not have sent 'finish' (e.g. crashed hard, though daemon should prevent hangs)
            # Or if the queue was processed fully after thread died.
            # We ensure UI is re-enabled if it's not already.
            if self.generate_button['state'] == 'disabled':
                self.log_message("Process ended unexpectedly. Re-enabling UI.")
                self.update_status("Process ended. Check logs.")
                self.toggle_ui_state(True)


    def process_video_thread(self, video_path, language_name, output_format):
        temp_wav_path = None
        has_error = False
        try:
            self.processing_queue.put({'type': 'log', 'value': f"Thread started. Video: {os.path.basename(video_path)}, Lang: {language_name}, Format: {output_format}"})

            # 1. Audio Extraction
            self.processing_queue.put({'type': 'status', 'value': 'Extracting audio...'})
            self.processing_queue.put({'type': 'progress', 'value': 5})
            
            try:
                # Create a temporary file that won't be deleted on close, so extract_audio can use it
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio_file:
                    temp_wav_path = tmp_audio_file.name
                
                self.processing_queue.put({'type': 'log', 'value': f"Temporary WAV path: {temp_wav_path}"})

                if not extract_audio(video_path, temp_wav_path):
                    # extract_audio should ideally raise an exception on failure or return more info
                    self.processing_queue.put({'type': 'error', 'value': 'Audio extraction failed. The function returned false. Check console for details from audio_extractor.'})
                    has_error = True; return # Stop processing
                
                self.processing_queue.put({'type': 'log', 'value': 'Audio extraction successful.'})
                self.processing_queue.put({'type': 'progress', 'value': 25})

            except Exception as e:
                self.processing_queue.put({'type': 'error', 'value': f'Audio extraction failed: {str(e)}'})
                has_error = True; return


            # 2. STT Processing
            self.processing_queue.put({'type': 'status', 'value': 'Transcribing audio (model loading can take time)...'})
            
            stt_result, error_msg = transcribe_audio_with_whisper(temp_wav_path, language_name)

            if error_msg or not stt_result:
                err_val = error_msg or "STT process returned no result or an unknown error."
                self.processing_queue.put({'type': 'error', 'value': f'Speech-to-text failed: {err_val}'})
                has_error = True; return
            
            self.processing_queue.put({'type': 'log', 'value': f"Transcription successful. Language detected: {stt_result.get('language', 'N/A')}"})
            self.processing_queue.put({'type': 'progress', 'value': 75})

            # 3. Subtitle Generation
            try:
                video_dir = os.path.dirname(video_path)
                video_filename_base = os.path.splitext(os.path.basename(video_path))[0]
                output_subtitle_path = os.path.join(video_dir, f"{video_filename_base}.{output_format}")
            except Exception as e: # Catch potential os.path errors, though unlikely
                self.processing_queue.put({'type': 'error', 'value': f'Error determining output path: {str(e)}'})
                has_error = True; return


            self.processing_queue.put({'type': 'status', 'value': f'Generating {output_format.upper()} subtitles...'})
            
            success_subtitle = False
            try:
                if output_format == "srt":
                    success_subtitle = generate_srt(stt_result, output_subtitle_path)
                elif output_format == "ass":
                    success_subtitle = generate_ass(stt_result, output_subtitle_path)
            except Exception as e:
                self.processing_queue.put({'type': 'error', 'value': f'{output_format.upper()} subtitle generation failed: {str(e)}'})
                has_error = True; return

            if not success_subtitle:
                # Functions generate_srt/generate_ass should log specific errors.
                # This is a fallback if they return False without a clear exception.
                self.processing_queue.put({'type': 'error', 'value': f'{output_format.upper()} subtitle generation returned false. Check logs for details from subtitle_generator.'})
                has_error = True; return

            self.processing_queue.put({'type': 'status', 'value': f'Subtitles saved to: {output_subtitle_path}'})
            self.processing_queue.put({'type': 'log', 'value': f'Subtitles successfully generated: {output_subtitle_path}'})
            self.processing_queue.put({'type': 'progress', 'value': 100})

        except Exception as e:
            # Catch-all for any other unexpected errors in the thread
            self.processing_queue.put({'type': 'error', 'value': f"An unexpected error occurred in the processing thread: {str(e)}"})
            logging.exception("Critical error in processing thread")
            has_error = True
        finally:
            if temp_wav_path: # temp_wav_path is only assigned if the tempfile was created
                try:
                    if os.path.exists(temp_wav_path): # Check if it still exists before trying to remove
                        os.remove(temp_wav_path)
                        self.processing_queue.put({'type': 'log', 'value': f"Cleaned up temporary file: {temp_wav_path}"})
                    else:
                        self.processing_queue.put({'type': 'log', 'value': f"Temporary file {temp_wav_path} was already removed or not created."})
                except FileNotFoundError: # Should be caught by os.path.exists, but as a safeguard
                     self.processing_queue.put({'type': 'log', 'value': f"Temporary file {temp_wav_path} not found during cleanup."})
                except OSError as e:
                    self.processing_queue.put({'type': 'log', 'value': f"Warning: Could not delete temporary file {temp_wav_path}: {e}"})
            
            # Signal GUI thread that processing is finished, regardless of errors
            self.processing_queue.put({'type': 'finish', 'is_error': has_error})


if __name__ == "__main__":
    root = tk.Tk()
    app = SubtitleApp(root)
    root.mainloop()
```
