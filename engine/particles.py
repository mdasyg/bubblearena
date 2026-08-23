"""
engine/particles.py - Particle effects and floating score text popups for Bubble Arena.
"""
import pygame
import random
import math
from constants import COLOR_WHITE, COLOR_GOLD, COLOR_CYAN, COLOR_YELLOW, COLOR_RED, COLOR_PINK

class Particle:
    """A single visual particle."""
    def __init__(self, x, y, vx, vy, color, radius, lifespan, gravity=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.radius = float(radius)
        self.lifespan = float(lifespan)
        self.age = 0.0
        self.gravity = float(gravity)

    def update(self, dt):
        self.age += dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.age < self.lifespan

    def draw(self, surface):
        alpha = max(0.0, 1.0 - (self.age / self.lifespan))
        r = max(1, int(self.radius * alpha))
        if len(self.color) == 4:
            c = (self.color[0], self.color[1], self.color[2], int(self.color[3] * alpha))
            p_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, c, (r + 1, r + 1), r)
            surface.blit(p_surf, (int(self.x - r - 1), int(self.y - r - 1)))
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)

class FloatingText:
    """Floating score popup (e.g., +100, RESCUE!, POP!)."""
    def __init__(self, text, x, y, color=COLOR_GOLD, lifespan=1.0, font=None):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.vy = -35.0  # float upwards
        self.color = color
        self.lifespan = float(lifespan)
        self.age = 0.0
        self.font = font

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt
        return self.age < self.lifespan

    def draw(self, surface):
        if not self.font:
            return
        alpha_ratio = max(0.0, 1.0 - (self.age / self.lifespan))
        rendered = self.font.render(self.text, True, self.color)
        if alpha_ratio < 1.0:
            rendered.set_alpha(int(alpha_ratio * 255))
        rect = rendered.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rendered, rect)

class ParticleManager:
    """Manages spawning, updating, and drawing particles and floating texts."""
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        self.font = None
        try:
            self.font = pygame.font.SysFont("courier,consolas,monospace", 10, bold=True)
        except Exception:
            self.font = pygame.font.Font(None, 14)

    def spawn_pop_burst(self, x, y, color=COLOR_CYAN, count=12):
        """Spawns radial bubble explosion droplets."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 120)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            radius = random.uniform(2, 4)
            lifespan = random.uniform(0.3, 0.6)
            self.particles.append(Particle(x, y, vx, vy, color, radius, lifespan, gravity=80.0))

    def spawn_sparkles(self, x, y, color=COLOR_GOLD, count=8):
        """Spawns twinkling star sparkles upon item pickup or rescue."""
        for _ in range(count):
            vx = random.uniform(-50, 50)
            vy = random.uniform(-80, -20)
            lifespan = random.uniform(0.4, 0.8)
            self.particles.append(Particle(x, y, vx, vy, color, 2.5, lifespan, gravity=30.0))

    def spawn_jump_dust(self, x, y):
        """Spawns soft dust puffs when jumping or landing."""
        for _ in range(4):
            vx = random.uniform(-30, 30)
            vy = random.uniform(-10, 5)
            self.particles.append(Particle(x, y, vx, vy, (200, 200, 210), 2.0, 0.25))

    def add_floating_text(self, text, x, y, color=COLOR_GOLD):
        """Adds a floating score/status popup."""
        self.floating_texts.append(FloatingText(text, x, y, color=color, font=self.font))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
        for t in self.floating_texts:
            t.draw(surface)
