# about.py

import sys
import pygame
from settings import Settings
from game import Projectile

def run_about(screen):
    """
    Show the About/tutorial screen with an auto‑play demo.
    Press ESC to return.
    """
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont(None, 28)
    settings = Settings()

    bullets = []
    demo_timer    = 0.0
    DEMO_INTERVAL = 2.0  # seconds between demo shots

    WIDTH, HEIGHT = screen.get_size()
    CENTER = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
    MAX_DIST = max(WIDTH, HEIGHT) * 1.5

    instructions = [
        "Gravity Well — Tutorial",
        "",
        "Click & drag to shoot objects into the well.",
        "Try to catch them in orbit instead of crashing.",
        "",
        "Auto‑demo firing every 2s from bottom‑left",
        "",
        "P = pause    G = toggle gravity vectors",
        "D = toggle head/tail arrows    S = in‑game menu",
        "Mouse wheel or +/- = zoom in/out",
        "",
        "Press ESC to return to the main menu"
    ]

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        demo_timer += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False

        # auto‑fire a demo projectile every DEMO_INTERVAL
        if demo_timer >= DEMO_INTERVAL:
            demo_timer -= DEMO_INTERVAL
            start = pygame.math.Vector2(100, HEIGHT - 100)
            vel = (CENTER - start) * (settings.drag_scale / 10)
            bullets.append(Projectile(
                start, vel,
                settings.bullet_radius,
                settings.bullet_mass,
                settings.friction
            ))

        # update demo bullets
        for b in bullets[:]:
            b.update(
                dt,
                settings.gv_radius, settings.gv_mass,
                CENTER, MAX_DIST,
                bullets
            )
            if not b.active:
                bullets.remove(b)

        # draw background
        screen.fill((0, 0, 0))

        # draw GV object
        pygame.draw.circle(
            screen,
            (0, 100, 255),
            (int(CENTER.x), int(CENTER.y)),
            settings.gv_radius
        )

        # draw bullets
        for b in bullets:
            b.draw(screen, (255, 255, 255))

        # draw instructions
        y = 20
        for line in instructions:
            surf = font.render(line, True, (200, 200, 200))
            screen.blit(surf, (20, y))
            y += 30

        pygame.display.flip()

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    run_about(screen)
    pygame.quit()
