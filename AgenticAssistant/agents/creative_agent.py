"""
Creative Agent for generating poems, summaries, and creative content.
Now with image generation capabilities using Pollinations.ai.
"""
from typing import Optional, Dict, Any
import requests
import urllib.parse

from agents.base_agent import BaseAgent
from llm.prompts import CREATIVE_AGENT_PROMPT
from database.db_manager import DatabaseManager


class CreativeAgent(BaseAgent):
    """Agent for creative content generation."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Creative Agent."""
        super().__init__(
            agent_name="creative",
            system_prompt=CREATIVE_AGENT_PROMPT,
            db_manager=db_manager
        )
        self.active_game = None
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a creative content request.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Returns:
            Creative response
        """
        # Load active game state for the user
        game_state = self.db_manager.get_game_state(user_id)
        self.active_game = game_state.get('active_game') if game_state else None
        
        # Determine creative task type
        task_type = self._identify_creative_task(message)
        
        # Update active game state if user explicitly asks for a game
        if task_type in ['word_chain', 'riddle', 'hangman', 'word_game']:
            self.active_game = task_type
        elif task_type in ['poem', 'story', 'summary', 'report', 'brainstorming', 'general_creative']:
            # If user switches to a different creative task, clear game state
            self.active_game = None
            
        # Add task-specific context
        additional_context = f"Creative task type: {task_type}"
        if self.active_game:
            additional_context += f"\nCURRENT ACTIVE GAME: {self.active_game.upper()}. Stick to the rules of this game."
            if game_state and game_state.get('game_data'):
                additional_context += f"\nGAME STATE: {game_state['game_data']}"
        
        # Generate creative content
        response = self.create_response(
            user_id,
            message,
            additional_context=additional_context
        )
        
        # Generate image if appropriate
        if self.should_generate_image(task_type, message):
            # Extract a concise image prompt from the response
            image_prompt = self._extract_image_prompt(response, message)
            if image_prompt:
                image_embed = self.generate_image(image_prompt)
                response += image_embed
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response,
            metadata={'task_type': task_type, 'active_game': self.active_game}
        )
        
        # Persist game state (only active_game)
        self.db_manager.set_game_state(user_id, {'active_game': self.active_game})
        
        return response
    
    def process_stream(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Process a creative content request and stream response.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Yields:
            Response chunks
        """
        # Load active game state for the user
        game_state = self.db_manager.get_game_state(user_id)
        self.active_game = game_state.get('active_game') if game_state else None
        
        # Determine creative task type
        task_type = self._identify_creative_task(message)
        
        # Update active game state based on user intent
        if task_type in ['word_chain', 'riddle', 'hangman', 'word_game']:
            self.active_game = task_type
        elif task_type in ['poem', 'story', 'summary', 'report', 'brainstorming', 'general_creative']:
            # Switching to non‑game creative task clears game state
            self.active_game = None
            
        # Add task‑specific context
        additional_context = f"Creative task type: {task_type}"
        if self.active_game:
            additional_context += f"\nCURRENT ACTIVE GAME: {self.active_game.upper()}. Stick to the rules of this game."
            if game_state and game_state.get('game_data'):
                additional_context += f"\nGAME STATE: {game_state['game_data']}"
        
        # Stream creative content
        full_response = ""
        for chunk in self.create_response_stream(
            user_id,
            message,
            additional_context=additional_context
        ):
            full_response += chunk
            yield chunk
        
        # Generate image if appropriate
        if self.should_generate_image(task_type, message):
            # Notify user that image generation is starting
            yield "\n\n🎨 **Generating image locally (this may take a few minutes)...**\n\n"
            
            # Extract a concise image prompt from the response
            image_prompt = self._extract_image_prompt(full_response, message)
            if image_prompt:
                image_embed = self.generate_image(image_prompt)
                full_response += image_embed
                yield image_embed
                
                # Notify completion
                yield "\n✅ **Image generation complete!**\n"
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=full_response,
            metadata={'task_type': task_type, 'active_game': self.active_game}
        )
        
        # Persist game state (only active_game)
        self.db_manager.set_game_state(user_id, {'active_game': self.active_game})
    
    def _identify_creative_task(self, message: str) -> str:
        """Identify the type of creative task."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['poem', 'poetry', 'verse']):
            return 'poem'
        elif any(word in message_lower for word in ['story', 'tale', 'narrative']):
            return 'story'
        elif any(word in message_lower for word in ['summary', 'summarize', 'tldr']):
            return 'summary'
        elif any(word in message_lower for word in ['report', 'analysis', 'review']):
            return 'report'
        elif any(word in message_lower for word in ['brainstorm', 'ideas', 'suggest']):
            return 'brainstorming'
        elif 'word chain' in message_lower:
            return 'word_chain'
        elif 'riddle' in message_lower:
            return 'riddle'
        elif 'hangman' in message_lower:
            return 'hangman'
        elif any(word in message_lower for word in ['game', 'play']):
            return 'word_game'
        else:
            return 'general_creative'
    
    def generate_proactive_suggestion(self, user_id: int) -> Optional[str]:
        """
        Generate a proactive suggestion based on user context.
        
        Args:
            user_id: User ID
            
        Returns:
            Suggestion or None
        """
        # Get user context
        context = self.get_user_context(user_id)
        
        if not context or "No previous context" in context:
            return None
        
        # Generate suggestion
        suggestion_prompt = """Based on the user's recent activity and preferences, 
        generate a brief, helpful suggestion or creative idea they might enjoy. 
        Keep it concise (2-3 sentences) and relevant."""
        
        try:
            suggestion = self.create_response(
                user_id,
                suggestion_prompt,
                additional_context="This is a proactive suggestion."
            )
            return suggestion
        except:
            return None
    
    def generate_image(self, prompt: str) -> str:
        """
        Generate an image using local SDXL with fallback to free APIs.
        Tries: Local SDXL -> Hugging Face -> DeepAI -> Pollinations
        
        Args:
            prompt: Image generation prompt
            
        Returns:
            Markdown image embed or error message
        """
        # Try Local SDXL first
        try:
            import torch
            from diffusers import StableDiffusionXLPipeline
            import base64
            from io import BytesIO

            print(f"Attempting local generation for: {prompt}")
            
            # Load pipeline (will download on first run)
            import os
            model_path = os.path.join(os.getcwd(), "models", "sdxl")
            os.makedirs(model_path, exist_ok=True)
            
            print(f"Loading model from: {model_path}")
            pipe = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0", 
                torch_dtype=torch.float16, 
                use_safetensors=True, 
                variant="fp16",
                cache_dir=model_path
            )
            
            # Move to GPU directly instead of offloading (fixes meta tensor error)
            pipe.to("cuda")
            
            # Generate
            image = pipe(prompt=prompt, num_inference_steps=30).images[0]
            
            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return f"\n\n![Generated Image](data:image/png;base64,{img_str})\n\n*Image generated locally using SDXL for: \"{prompt}\"*"
            
        except Exception as e:
            print(f"Local generation failed: {e}")
            # Fallthrough to APIs
        
        # Try Hugging Face Inference API first (best quality)
        try:
            hf_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            headers = {"Content-Type": "application/json"}
            payload = {"inputs": prompt}
            
            response = requests.post(hf_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                # Save image temporarily and return URL
                import base64
                image_data = base64.b64encode(response.content).decode()
                return f"\n\n![Generated Image](data:image/png;base64,{image_data})\n\n*Image generated for: \"{prompt}\"*"
        except Exception as e:
            print(f"Hugging Face API failed: {e}")
        
        # Try DeepAI as fallback
        try:
            deepai_url = "https://api.deepai.org/api/text2img"
            response = requests.post(
                deepai_url,
                data={'text': prompt},
                headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'},  # Free tier key
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if 'output_url' in result:
                    return f"\n\n![Generated Image]({result['output_url']})\n\n*Image generated for: \"{prompt}\"*"
        except Exception as e:
            print(f"DeepAI API failed: {e}")
        
        # Final fallback to Pollinations.ai
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            return f"\n\n![Generated Image]({image_url})\n\n*Image generated for: \"{prompt}\"*"
        except Exception as e:
            print(f"All image generation APIs failed: {e}")
            return "\n\n*(Image generation failed)*"
    
    def _extract_image_prompt(self, response: str, original_message: str) -> Optional[str]:
        """Extract a concise image prompt from the user's request."""
        # Check if user explicitly requested an image
        message_lower = original_message.lower()
        has_image_request = any(word in message_lower for word in ['image', 'picture', 'draw', 'illustrate', 'visualize', 'imagine'])
        
        # If explicit image request, use the original message (cleaned up)
        if has_image_request:
            import re
            # Remove common command phrases at the start of the message
            # e.g. "create an image of...", "draw a...", "imagine..."
            prompt = original_message
            
            # Regex to remove starting phrases (case insensitive)
            # Matches "create", "generate", "draw", "imagine" followed by optional "an image of", "a picture of", etc.
            pattern = r"^(?:can you\s+)?(?:please\s+)?(?:create|generate|make|draw|illustrate|visualize|imagine)(?:\s+(?:an?|the)\s+(?:image|picture|photo|illustration|drawing|painting)\s+of)?\s*"
            
            prompt = re.sub(pattern, "", prompt, flags=re.IGNORECASE)
            
            prompt = prompt.strip()
            
            # If prompt became empty or too short (e.g. user just said "create image"), use original or try to salvage
            if len(prompt) < 3:
                return original_message[:200]
                
            # Limit to reasonable length
            return prompt[:300]
        
        # For stories/poems without explicit image request, use the first meaningful line
        lines = response.split('\n')
        for line in lines:
            # Skip headers and empty lines
            if line.strip() and not line.startswith('#') and len(line) > 20:
                # Take first meaningful line, limit to 100 chars
                prompt = line.strip()[:100]
                return prompt
        
        # Fallback to original message
        return original_message[:200] if len(original_message) > 10 else None
    
    def should_generate_image(self, task_type: str, message: str) -> bool:
        """Determine if an image should be generated for this request."""
        # Generate images for stories, poems, and creative descriptions
        image_worthy_tasks = ['story', 'poem', 'general_creative']
        
        # Check if user explicitly asks for an image
        message_lower = message.lower()
        explicit_request = any(word in message_lower for word in ['image', 'picture', 'draw', 'illustrate', 'visualize', 'imagine'])
        
        return task_type in image_worthy_tasks or explicit_request

