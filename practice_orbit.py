import sys
import math
import pygame

# ─────────────────────────────────────────────────────────────────────────────
# Orbital Shooter with Full Mouse & Keyboard Controls
#
# - Fullscreen mode
# - Menu: Start, Settings, Quit (click or ↑↓+Enter)
# - Settings: adjust planet/bullet radius & density (click left/right of item or ←→, or ↑↓+Enter)
# - In‑game: click+drag to launch, click “Menu” or “Retry” buttons, or use keyboard
# - Trajectory preview while dragging
# - Goal: one full orbit without crashing or escaping
# ─────────────────────────────────────────────────────────────────────────────

# ------------------------------------------------------------------
# States
# ------------------------------------------------------------------
STATE_MENU     = "MENU"
STATE_SETTINGS = "SETTINGS"
STATE_PLAY     = "PLAY"

# ------------------------------------------------------------------
# Defaults & Ranges
# ------------------------------------------------------------------
FPS = 60
G   = 1  # gravity constant

PLANET_RADIUS_RANGE  = (10, 200)
PLANET_DENSITY_RANGE = (1, 100)
BULLET_RADIUS_RANGE  = (2, 20)
BULLET_DENSITY_RANGE = (1, 50)

# ------------------------------------------------------------------
# Settings container
# ------------------------------------------------------------------
class Settings:
    def __init__(self):
        self.planet_radius  = 30
        self.planet_density = 10
        self.bullet_radius  = 5
        self.bullet_density = 1

    @property
    def planet_mass(self):
        return self.planet_density * (self.planet_radius ** 2)

    @property
    def bullet_mass(self):
        return self.bullet_density * (self.bullet_radius ** 2)

# ------------------------------------------------------------------
# Projectile with adjustable radius
# ------------------------------------------------------------------
class Projectile:
    def __init__(self, pos, vel, radius):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.radius = radius
        self.active = True
        self.crashed = False
        self.lost = False
        self.orbit_achieved = False

        # orbit detection
        dx = self.pos.x - CENTER.x
        dy = self.pos.y - CENTER.y
        self.prev_angle = math.atan2(dy, dx)
        self.accum_angle = 0.0

    def update(self, dt, planet_radius, planet_mass):
        if not self.active:
            return

        dir_vec = CENTER - self.pos
        dist = dir_vec.length()

        # crash
        if dist <= planet_radius + self.radius:
            self.active = False
            self.crashed = True
            return

        # gravity accel
        acc = dir_vec.normalize() * (G * planet_mass / (dist * dist))
        self.vel += acc * dt
        self.pos += self.vel * dt

        # orbit tracking
        cur_ang = math.atan2(self.pos.y - CENTER.y, self.pos.x - CENTER.x)
        delta = cur_ang - self.prev_angle
        if delta > math.pi:    delta -= 2*math.pi
        if delta < -math.pi:   delta += 2*math.pi
        self.accum_angle += delta
        self.prev_angle = cur_ang
        if abs(self.accum_angle) >= 2*math.pi:
            self.active = False
            self.orbit_achieved = True
            return

        # lost
        if dist > MAX_DISTANCE:
            self.active = False
            self.lost = True

    def draw(self, surf):
        pygame.draw.circle(
            surf, (255,255,255),
            (int(self.pos.x), int(self.pos.y)),
            self.radius
        )

# ------------------------------------------------------------------
# Simulate preview trajectory
# ------------------------------------------------------------------
def simulate_trajectory(start_pos, init_vel, planet_radius, planet_mass,
                        steps=200, dt=1/60.0):
    pos = pygame.math.Vector2(start_pos)
    vel = pygame.math.Vector2(init_vel)
    path = []
    for _ in range(steps):
        dir_vec = CENTER - pos
        dist = dir_vec.length()
        if dist <= planet_radius or dist > MAX_DISTANCE:
            break
        acc = dir_vec.normalize() * (G * planet_mass / (dist*dist))
        vel += acc * dt
        pos += vel * dt
        path.append((int(pos.x), int(pos.y)))
    return path

# ------------------------------------------------------------------
# Initialize
# ------------------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
CENTER = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
MAX_DISTANCE = max(WIDTH, HEIGHT) * 1.5

clock = pygame.time.Clock()
font  = pygame.font.SysFont(None, 36)
small = pygame.font.SysFont(None, 24)

settings = Settings()
state = STATE_MENU

menu_items     = ["Start Game", "Settings", "Quit"]
settings_items = ["Planet Radius", "Planet Density",
                  "Bullet Radius", "Bullet Density",
                  "Back"]
menu_idx     = 0
settings_idx = 0

projectile = None
dragging   = False
drag_start = None
message    = ""

# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    mx, my = pygame.mouse.get_pos()

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

        # mouse navigation for MENU
        if state == STATE_MENU:
            # hover
            if ev.type == pygame.MOUSEMOTION:
                for i, item in enumerate(menu_items):
                    txt = font.render(item, True, (255,255,255))
                    rect = txt.get_rect(center=(CENTER.x, 200 + i*50))
                    if rect.collidepoint(mx, my):
                        menu_idx = i
            # click
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                choice = menu_items[menu_idx]
                if choice == "Start Game":
                    state = STATE_PLAY
                    projectile = None
                    message = ""
                elif choice == "Settings":
                    state = STATE_SETTINGS
                elif choice == "Quit":
                    running = False

        # keyboard navigation for MENU
        if state == STATE_MENU and ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_UP:
                menu_idx = (menu_idx - 1) % len(menu_items)
            elif ev.key == pygame.K_DOWN:
                menu_idx = (menu_idx + 1) % len(menu_items)
            elif ev.key == pygame.K_RETURN:
                choice = menu_items[menu_idx]
                if choice == "Start Game":
                    state = STATE_PLAY
                    projectile = None
                    message = ""
                elif choice == "Settings":
                    state = STATE_SETTINGS
                elif choice == "Quit":
                    running = False
            elif ev.key == pygame.K_ESCAPE:
                running = False

        # SETTINGS
        if state == STATE_SETTINGS:
            # hover
            if ev.type == pygame.MOUSEMOTION:
                for i, item in enumerate(settings_items):
                    text = item + (f": {getattr(settings, item.lower().replace(' ', '_'))}"
                                   if item != "Back" else "")
                    txt = font.render(text, True, (255,255,255))
                    rect = txt.get_rect(topleft=(100, 150 + i*50))
                    if rect.collidepoint(mx, my):
                        settings_idx = i
            # click
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                i = settings_idx
                if settings_items[i] == "Back":
                    state = STATE_MENU
                else:
                    # adjust based on click side
                    rect = font.render("", True, (0,0,0)).get_rect()  # placeholder
                    txt = font.render("", True, (0,0,0))
                    # re-render to get rect
                    text = settings_items[i] + f": {getattr(settings, settings_items[i].lower().replace(' ', '_'))}"
                    txt = font.render(text, True, (255,255,255))
                    rect = txt.get_rect(topleft=(100, 150 + i*50))
                    if mx < rect.centerx:
                        delta = -1
                    else:
                        delta = 1
                    attr = settings_items[i].lower().replace(' ', '_')
                    lo, hi = {
                        "planet_radius": PLANET_RADIUS_RANGE,
                        "planet_density": PLANET_DENSITY_RANGE,
                        "bullet_radius": BULLET_RADIUS_RANGE,
                        "bullet_density": BULLET_DENSITY_RANGE
                    }[attr]
                    new = max(lo, min(hi, getattr(settings, attr) + delta))
                    setattr(settings, attr, new)
            # keyboard
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    settings_idx = (settings_idx - 1) % len(settings_items)
                elif ev.key == pygame.K_DOWN:
                    settings_idx = (settings_idx + 1) % len(settings_items)
                elif ev.key == pygame.K_LEFT:
                    i = settings_idx
                    if settings_items[i] != "Back":
                        attr = settings_items[i].lower().replace(' ', '_')
                        lo, hi = {
                            "planet_radius": PLANET_RADIUS_RANGE,
                            "planet_density": PLANET_DENSITY_RANGE,
                            "bullet_radius": BULLET_RADIUS_RANGE,
                            "bullet_density": BULLET_DENSITY_RANGE
                        }[attr]
                        setattr(settings, attr, max(lo, getattr(settings, attr)-1))
                elif ev.key == pygame.K_RIGHT:
                    i = settings_idx
                    if settings_items[i] != "Back":
                        attr = settings_items[i].lower().replace(' ', '_')
                        lo, hi = {
                            "planet_radius": PLANET_RADIUS_RANGE,
                            "planet_density": PLANET_DENSITY_RANGE,
                            "bullet_radius": BULLET_RADIUS_RANGE,
                            "bullet_density": BULLET_DENSITY_RANGE
                        }[attr]
                        setattr(settings, attr, min(hi, getattr(settings, attr)+1))
                elif ev.key == pygame.K_RETURN and settings_items[settings_idx] == "Back":
                    state = STATE_MENU
                elif ev.key == pygame.K_ESCAPE:
                    state = STATE_MENU

        # PLAY
        if state == STATE_PLAY:
            # menu & retry buttons
            # click
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Menu button
                menu_txt = small.render("Menu", True, (255,255,255))
                menu_rect = menu_txt.get_rect(topright=(WIDTH-10, 10))
                if menu_rect.collidepoint(ev.pos):
                    state = STATE_MENU
                    continue
                # Retry button
                if message:
                    retry_txt = small.render("Retry", True, (255,255,255))
                    retry_rect = retry_txt.get_rect(topleft=(20, 100))
                    if retry_rect.collidepoint(ev.pos):
                        projectile = None
                        message = ""
                        continue

                # dragging to set launch
                dragging = True
                drag_start = pygame.math.Vector2(ev.pos)

            # release
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and dragging:
                dragging = False
                drag_end = pygame.math.Vector2(ev.pos)
                vel = (drag_start - drag_end) * 2.0
                projectile = Projectile(drag_start, vel, settings.bullet_radius)
                message = ""

            # keyboard restart/menu
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    projectile = None
                    message = ""
                elif ev.key == pygame.K_ESCAPE:
                    state = STATE_MENU

    # update physics
    if state == STATE_PLAY and projectile:
        projectile.update(dt, settings.planet_radius, settings.planet_mass)
        if not projectile.active:
            if projectile.crashed:
                message = "💥 Crashed!"
            elif projectile.lost:
                message = "🌌 Lost!"
            elif projectile.orbit_achieved:
                message = "✅ Orbit!"

    # draw
    screen.fill((0,0,0))

    if state == STATE_MENU:
        title = font.render("Orbital Shooter", True, (255,255,255))
        screen.blit(title, title.get_rect(center=(CENTER.x, 100)))
        for i, item in enumerate(menu_items):
            color = (255,255,0) if i == menu_idx else (200,200,200)
            txt = font.render(item, True, color)
            screen.blit(txt, txt.get_rect(center=(CENTER.x, 200 + i*50)))

    elif state == STATE_SETTINGS:
        title = font.render("Settings", True, (255,255,255))
        screen.blit(title, title.get_rect(center=(CENTER.x, 50)))
        for i, item in enumerate(settings_items):
            color = (255,255,0) if i == settings_idx else (200,200,200)
            if item != "Back":
                val = getattr(settings, item.lower().replace(' ', '_'))
                text = f"{item}: {val}"
            else:
                text = "Back"
            txt = font.render(text, True, color)
            screen.blit(txt, txt.get_rect(topleft=(100, 150 + i*50)))

    elif state == STATE_PLAY:
        # planet
        pygame.draw.circle(screen, (0,100,255),
                           (int(CENTER.x), int(CENTER.y)),
                           settings.planet_radius)

        # preview
        if dragging and drag_start:
            drag_end = pygame.mouse.get_pos()
            vel = (pygame.math.Vector2(drag_start) - pygame.math.Vector2(drag_end)) * 2.0
            path = simulate_trajectory(drag_start, vel,
                                       settings.planet_radius,
                                       settings.planet_mass)
            if path:
                pygame.draw.lines(screen, (100,255,100), False, path, 2)
            pygame.draw.line(screen, (200,200,200),
                             drag_start, drag_end, 2)

        # projectile
        if projectile:
            projectile.draw(screen)

        # UI hints
        if not projectile and not dragging:
            instr = "Click+drag to launch; or ▶︎ Menu/Retry"
            txt = small.render(instr, True, (255,255,255))
            screen.blit(txt, (20, 20))

        # message + Retry
        if message:
            msg_txt = font.render(message, True, (255,255,255))
            screen.blit(msg_txt, (20, 60))
            retry_txt = small.render("Retry", True, (255,255,255))
            screen.blit(retry_txt, retry_txt.get_rect(topleft=(20, 100)))

        # Menu button
        menu_txt = small.render("Menu", True, (255,255,255))
        screen.blit(menu_txt, menu_txt.get_rect(topright=(WIDTH-10, 10)))

    pygame.display.flip()

pygame.quit()
sys.exit()
