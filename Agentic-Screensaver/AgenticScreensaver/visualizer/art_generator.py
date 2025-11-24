import pygame
import random
import math

class AtmosphericGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        self.particles = []
        
        # Default State
        self.sky_colors = [[10, 10, 50], [100, 50, 100]] # Top, Bottom
        self.weather = "stars"
        self.wind_speed = 0.2
        self.complexity = 0.5
        
        self.stars_cache = [] # Static stars for "stars" weather

    def update_params(self, decision):
        """Updates the internal parameters based on the agent's decision."""
        self.sky_colors = decision.get("sky_colors", [[10, 10, 50], [100, 50, 100]])
        self.weather = decision.get("weather", "stars")
        self.wind_speed = decision.get("wind_speed", 0.2)
        self.complexity = decision.get("complexity", 0.5)
        
        # Reset particles if weather changes drastically
        if len(self.particles) > 0:
             # Optional: Clear particles or let them fade. Let's keep them for smooth transition.
             pass

        if self.weather == "stars" and not self.stars_cache:
            self._generate_stars()

    def draw(self):
        """Draws the next frame."""
        # 1. Draw Gradient Background
        self._draw_gradient()

        # 2. Draw Weather/Particles
        if self.weather == "rain":
            self._draw_rain()
        elif self.weather == "snow":
            self._draw_snow()
        elif self.weather == "fireflies":
            self._draw_fireflies()
        elif self.weather == "stars":
            self._draw_stars()
        elif self.weather == "fog":
            self._draw_fog()
        else:
            self._draw_fireflies() # Default

        return self.surface

    def _draw_gradient(self):
        """Draws a vertical gradient."""
        top_color = self.sky_colors[0]
        bottom_color = self.sky_colors[1]
        
        # Optimization: Draw gradient on a smaller surface and scale up? 
        # For now, just draw lines or rects.
        # Better: Create a 1xHeight surface, fill it, and scale it.
        gradient = pygame.Surface((1, self.height))
        
        r1, g1, b1 = top_color
        r2, g2, b2 = bottom_color
        
        for y in range(self.height):
            r = r1 + (r2 - r1) * y // self.height
            g = g1 + (g2 - g1) * y // self.height
            b = b1 + (b2 - b1) * y // self.height
            gradient.set_at((0, y), (r, g, b))
            
        pygame.transform.scale(gradient, (self.width, self.height), self.surface)

    def _generate_stars(self):
        self.stars_cache = []
        for _ in range(200):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            brightness = random.randint(100, 255)
            self.stars_cache.append((x, y, brightness))

    def _draw_stars(self):
        # Draw static stars
        for x, y, b in self.stars_cache:
            # Twinkle effect
            if random.random() < 0.01:
                b = random.randint(100, 255)
            self.surface.set_at((x, y), (b, b, b))
            
        # Occasional shooting star
        if random.random() < 0.005:
            self.particles.append({
                "type": "shooting_star",
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height // 2),
                "vx": random.uniform(5, 15),
                "vy": random.uniform(1, 5),
                "life": 30
            })
        self._update_particles()

    def _draw_rain(self):
        # Spawn rain
        if len(self.particles) < 500 * self.complexity:
            self.particles.append({
                "type": "rain",
                "x": random.randint(0, self.width),
                "y": -10,
                "vx": self.wind_speed * 2,
                "vy": random.uniform(10, 20),
                "life": 100
            })
        
        for p in self.particles:
            if p["type"] == "rain":
                pygame.draw.line(self.surface, (200, 200, 255), (p["x"], p["y"]), (p["x"] + p["vx"], p["y"] + p["vy"]), 1)
        
        self._update_particles()

    def _draw_snow(self):
        if len(self.particles) < 200 * self.complexity:
            self.particles.append({
                "type": "snow",
                "x": random.randint(0, self.width),
                "y": -10,
                "vx": random.uniform(-1, 1) + self.wind_speed,
                "vy": random.uniform(1, 3),
                "life": 200
            })
            
        for p in self.particles:
            if p["type"] == "snow":
                pygame.draw.circle(self.surface, (255, 255, 255), (int(p["x"]), int(p["y"])), 2)
        
        self._update_particles()

    def _draw_fireflies(self):
        if len(self.particles) < 50 * self.complexity:
            self.particles.append({
                "type": "firefly",
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "vx": random.uniform(-1, 1),
                "vy": random.uniform(-1, 1),
                "life": random.randint(100, 300),
                "color": (255, 255, 100)
            })
            
        for p in self.particles:
            if p["type"] == "firefly":
                # Wiggle
                p["vx"] += random.uniform(-0.1, 0.1)
                p["vy"] += random.uniform(-0.1, 0.1)
                # Clamp speed
                p["vx"] = max(-2, min(2, p["vx"]))
                p["vy"] = max(-2, min(2, p["vy"]))
                
                # Glow
                alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() * 0.005))
                # Draw glow (simulated with larger circle)
                s = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p["color"], 50), (5, 5), 5)
                self.surface.blit(s, (p["x"]-5, p["y"]-5))
                pygame.draw.circle(self.surface, p["color"], (int(p["x"]), int(p["y"])), 1)
        
        self._update_particles()

    def _draw_fog(self):
        # Fog is hard in raw pygame without shaders, simulate with large transparent moving rects/circles
        pass

    def _update_particles(self):
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            
            if p["life"] <= 0 or p["y"] > self.height or p["x"] > self.width or p["x"] < 0:
                self.particles.remove(p)
