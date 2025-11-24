"""
Optional voice utilities for speech-to-text and text-to-speech.
Supports both free local Whisper (via Hugging Face) and OpenAI API.
"""
from typing import Optional
import io
from config import config


class VoiceUtils:
    """Utilities for voice input/output."""
    
    def __init__(self):
        """Initialize voice utilities."""
        self.stt_method = "none"  # none, local_whisper, openai
        self.tts_method = "none"  # none, openai
        
        # Try to initialize local Whisper for STT (free)
        if config.ENABLE_VOICE_INPUT:
            self._init_local_whisper()
        
        # Initialize OpenAI for TTS if enabled
        if config.ENABLE_VOICE_OUTPUT:
            self._init_openai_tts()
    
    def _init_local_whisper(self):
        """Initialize local Whisper model via Hugging Face (free)."""
        try:
            from transformers import pipeline
            import torch
            
            # Use smaller model for faster inference
            # Options: "openai/whisper-tiny", "openai/whisper-base", "openai/whisper-small"
            model_name = "openai/whisper-base"
            
            # Determine device (GPU if available, else CPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            print(f"Loading Whisper model ({model_name}) on {device}...")
            self.whisper_pipeline = pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device=device
            )
            self.stt_method = "local_whisper"
            print("✅ Local Whisper STT initialized (free)")
            
        except ImportError:
            print("⚠️ transformers/torch not installed. Install with: pip install transformers torch")
            self.stt_method = "none"
        except Exception as e:
            print(f"⚠️ Could not initialize local Whisper: {e}")
            self.stt_method = "none"
    
    def _init_openai_tts(self):
        """Initialize OpenAI for TTS (requires API key)."""
        if not config.OPENAI_API_KEY:
            print("⚠️ OpenAI API key required for TTS")
            self.tts_method = "none"
            return
        
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.tts_method = "openai"
            print("✅ OpenAI TTS initialized")
        except ImportError:
            print("⚠️ openai package not installed")
            self.tts_method = "none"
        except Exception as e:
            print(f"⚠️ Could not initialize OpenAI TTS: {e}")
            self.tts_method = "none"
    
    def speech_to_text(self, audio_file) -> Optional[str]:
        """
        Convert speech to text using available method.
        
        Args:
            audio_file: Audio file path or file object
            
        Returns:
            Transcribed text or None if failed
        """
        if self.stt_method == "local_whisper":
            return self._whisper_stt(audio_file)
        elif self.stt_method == "openai":
            return self._openai_stt(audio_file)
        else:
            return None
    
    def _whisper_stt(self, audio_file) -> Optional[str]:
        """Use local Whisper for STT (free)."""
        try:
            # Handle both file path and file object
            if isinstance(audio_file, str):
                audio_path = audio_file
            else:
                # Save uploaded file temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_file.read())
                    audio_path = tmp.name
            
            # Transcribe using Whisper pipeline
            result = self.whisper_pipeline(audio_path)
            return result["text"]
            
        except Exception as e:
            print(f"Error in local Whisper STT: {e}")
            return None
    
    def _openai_stt(self, audio_file) -> Optional[str]:
        """Use OpenAI Whisper API for STT (requires API key)."""
        try:
            transcript = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text
        except Exception as e:
            print(f"Error in OpenAI STT: {e}")
            return None
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> Optional[bytes]:
        """
        Convert text to speech using available method.
        
        Args:
            text: Text to convert
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            Audio bytes or None if failed
        """
        if self.tts_method == "openai":
            return self._openai_tts(text, voice)
        else:
            return None
    
    def _openai_tts(self, text: str, voice: str) -> Optional[bytes]:
        """Use OpenAI TTS API."""
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"Error in OpenAI TTS: {e}")
            return None
    
    @property
    def stt_available(self) -> bool:
        """Check if STT is available."""
        return self.stt_method != "none"
    
    @property
    def tts_available(self) -> bool:
        """Check if TTS is available."""
        return self.tts_method != "none"


# Create singleton instance
voice_utils = VoiceUtils()

