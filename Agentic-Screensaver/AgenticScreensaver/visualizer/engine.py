import pygame
import pygame.freetype
import os
from .art_generator import AtmosphericGenerator

class VisualEngine:
    def __init__(self, width, height, fullscreen=False):
        pygame.init()
        pygame.freetype.init() # Initialize freetype
        self.width = width
        self.height = height
        
        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
            
        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Agentic Screensaver")
        pygame.mouse.set_visible(False) # Hide cursor
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Font Cache
        self.fonts = {}
        self.available_fonts = []
        self.current_font_name = "PlayfairDisplay"
        self._load_fonts()
        
        self.art_gen = AtmosphericGenerator(width, height)
        self.current_poetry = ""
        self.current_theme = ""

    def _load_fonts(self):
        """Loads available fonts from assets/fonts or system."""
        font_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
        
        # Map of font names to filenames
        font_files = {
            "DancingScript": "DancingScript.ttf",
            "Merienda": "Merienda.ttf",
            "PlayfairDisplay": "PlayfairDisplay.ttf"
        }
        
        for name, filename in font_files.items():
            path = os.path.join(font_dir, filename)
            if os.path.exists(path):
                try:
                    self.fonts[name] = pygame.freetype.Font(path, 48) # Large size for quotes
                    self.available_fonts.append(name)
                    print(f"Loaded font: {name}")
                except Exception as e:
                    print(f"Failed to load font {name}: {e}")
            else:
                print(f"Font file not found: {path}")
        
        # Fallback system font (only if no custom fonts loaded)
        if not self.available_fonts:
            print("No custom fonts loaded. Trying system fallback.")
            try:
                self.fonts["default"] = pygame.freetype.SysFont("sans-serif", 32)
                self.available_fonts.append("default")
            except Exception as e:
                print(f"Failed to load system font: {e}")

    def update_state(self, decision):
        """Receives new decision from the agent."""
        self.art_gen.update_params(decision)
        self.current_poetry = decision.get("poetry", "")
        self.current_theme = decision.get("theme", "")
        self.current_font_name = decision.get("font", "PlayfairDisplay")

    def render(self):
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.running = False # Exit on any interaction
            if event.type == pygame.MOUSEMOTION:
                pass

        # Draw Art
        art_surface = self.art_gen.draw()
        self.screen.blit(art_surface, (0, 0))

        # Draw UI Overlay (Poetry & Theme)
        self._draw_overlay()

        pygame.display.flip()
        self.clock.tick(60)

    def _safe_render_text(self, font, text, color):
        """Safely renders text, catching NULL pointer errors."""
        try:
            # freetype render returns (surface, rect)
            surf, _ = font.render(text, color)
            return surf
        except Exception as e:
            print(f"Font render error: {e}")
            return None

    def _draw_overlay(self):
        # Theme Label (Bottom Left, small, semi-transparent)
        if self.available_fonts:
            theme_font = self.fonts[self.available_fonts[0]]
            # Use smaller size for theme label
            original_size = theme_font.size
            theme_font.size = 24
            theme_surf = self._safe_render_text(theme_font, f"{self.current_theme}", (255, 255, 255))
            theme_font.size = original_size # Restore size
            
            if theme_surf:
                theme_surf.set_alpha(150)
                self.screen.blit(theme_surf, (20, self.height - 40))

        # Poetry (Centered at 70% height)
        lines = self.current_poetry.split('\n')
        
        # Select font
        font_name = self.current_font_name
        if font_name not in self.fonts:
            if self.available_fonts:
                font_name = self.available_fonts[0]
            else:
                return 
        
        font = self.fonts[font_name]
        font.size = 48 # Ensure correct size
        
        total_height = len(lines) * 60 
        start_y = self.height * 0.7 - (total_height / 2)
        
        for i, line in enumerate(lines):
            # Shadow
            shadow_surf = self._safe_render_text(font, line, (0, 0, 0))
            if shadow_surf:
                shadow_rect = shadow_surf.get_rect(center=(self.width/2 + 2, start_y + i*60 + 2))
                self.screen.blit(shadow_surf, shadow_rect)
            
            # Text
            text_surf = self._safe_render_text(font, line, (255, 255, 255))
            if text_surf:
                text_rect = text_surf.get_rect(center=(self.width/2, start_y + i*60))
                self.screen.blit(text_surf, text_rect)

    def quit(self):
        pygame.quit()
