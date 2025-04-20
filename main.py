import sys
import math
import json
import pygame

# ─────────────────────────────────────────────────────────────────────────────
# Orbital Shooter with JSON‑Saveable Mouse & Physics Settings + Scoring
#
# - Fullscreen
# - Menu: Start, Settings, Quit (hover/click or ↑↓+Enter)
# - Settings:
#     • Planet Radius & Density
#     • Bullet Radius & Density
#     • Drag Scale (drag distance → shot power)
#     • Friction (% deceleration per second)
#     • Save Settings → settings.json
#     • Load Settings ← settings.json
# - Click+drag to launch; live trajectory preview
# - Scoring: base score = distance from planet at launch; display at launch spot
#   + orbit bonus: double the score if orbit achieved
# - Goal: complete one full orbit without crashing or escaping
# ─────────────────────────────────────────────────────────────────────────────

# ------------------------------------------------------------------
# Game States
# ------------------------------------------------------------------
STATE_MENU     = "MENU"
STATE_SETTINGS = "SETTINGS"
STATE_PLAY     = "PLAY"

# ------------------------------------------------------------------
# Physics & Ranges
# ------------------------------------------------------------------
FPS = 60
G   = 1  # gravity constant

PLANET_RADIUS_RANGE   = (10, 200)
PLANET_DENSITY_RANGE  = (1, 100)
BULLET_RADIUS_RANGE   = (2, 20)
BULLET_DENSITY_RANGE  = (1, 50)
DRAG_SCALE_RANGE      = (1, 10)    # multiplier on drag
FRICTION_RANGE        = (0, 100)   # percent per second

SETTINGS_FILE = "settings.json"

# ------------------------------------------------------------------
# Settings container with JSON save/load
# ------------------------------------------------------------------
class Settings:
    def __init__(self):
        # defaults
        self.planet_radius  = 30
        self.planet_density = 10
        self.bullet_radius  = 5
        self.bullet_density = 1
        self.drag_scale     = 2
        self.friction       = 0  # percent per second

    @property
    def planet_mass(self):
        # mass ∝ density × area (radius²)
        return self.planet_density * (self.planet_radius ** 2)

    @property
    def bullet_mass(self):
        return self.bullet_density * (self.bullet_radius ** 2)

    def to_dict(self):
        return {
            "planet_radius":  self.planet_radius,
            "planet_density": self.planet_density,
            "bullet_radius":  self.bullet_radius,
            "bullet_density": self.bullet_density,
            "drag_scale":     self.drag_scale,
            "friction":       self.friction
        }

    def save(self, filename=SETTINGS_FILE):
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def load(self, filename=SETTINGS_FILE):
        with open(filename, "r") as f:
            data = json.load(f)
        # clamp loaded values
        self.planet_radius  = max(PLANET_RADIUS_RANGE[0], min(PLANET_RADIUS_RANGE[1], data.get("planet_radius",  self.planet_radius)))
        self.planet_density = max(PLANET_DENSITY_RANGE[0], min(PLANET_DENSITY_RANGE[1], data.get("planet_density", self.planet_density)))
        self.bullet_radius  = max(BULLET_RADIUS_RANGE[0], min(BULLET_RADIUS_RANGE[1], data.get("bullet_radius",  self.bullet_radius)))
        self.bullet_density = max(BULLET_DENSITY_RANGE[0], min(BULLET_DENSITY_RANGE[1], data.get("bullet_density", self.bullet_density)))
        self.drag_scale     = max(DRAG_SCALE_RANGE[0],   min(DRAG_SCALE_RANGE[1],   data.get("drag_scale",     self.drag_scale)))
        self.friction       = max(FRICTION_RANGE[0],     min(FRICTION_RANGE[1],     data.get("friction",       self.friction)))

# ------------------------------------------------------------------
# Projectile class
# ------------------------------------------------------------------
class Projectile:
    def __init__(self, pos, vel, radius):
        self.pos         = pygame.math.Vector2(pos)
        self.vel         = pygame.math.Vector2(vel)
        self.radius      = radius
        self.active      = True
        self.crashed     = False
        self.lost        = False
        self.orbit_done  = False

        # for orbit detection
        dx, dy = self.pos.x - CENTER.x, self.pos.y - CENTER.y
        self.prev_angle = math.atan2(dy, dx)
        self.accum_angle = 0.0

    def update(self, dt, planet_radius, planet_mass, friction_percent):
        if not self.active:
            return

        # gravity vector
        to_center = CENTER - self.pos
        dist = to_center.length()

        # crash into planet?
        if dist <= planet_radius + self.radius:
            self.active  = False
            self.crashed = True
            return

        # gravitational acceleration = G*M / r²
        acc = to_center.normalize() * (G * planet_mass / (dist * dist))
        self.vel += acc * dt

        # apply friction (% deceleration per second)
        friction_coef = friction_percent / 100.0
        self.vel *= max(0.0, 1 - friction_coef * dt)

        self.pos += self.vel * dt

        # track angle swept
        curr_ang = math.atan2(self.pos.y - CENTER.y, self.pos.x - CENTER.x)
        delta    = curr_ang - self.prev_angle
        if delta > math.pi:    delta -= 2*math.pi
        if delta < -math.pi:   delta += 2*math.pi
        self.accum_angle += delta
        self.prev_angle    = curr_ang

        # full orbit?
        if abs(self.accum_angle) >= 2*math.pi:
            self.active     = False
            self.orbit_done = True
            return

        # lost in space?
        if dist > MAX_DISTANCE:
            self.active = False
            self.lost   = True

    def draw(self, surf):
        pygame.draw.circle(
            surf, (255,255,255),
            (int(self.pos.x), int(self.pos.y)),
            self.radius
        )

# ------------------------------------------------------------------
# Trajectory preview with friction
# ------------------------------------------------------------------
def simulate_trajectory(start_pos, init_vel,
                        planet_radius, planet_mass,
                        friction_percent,
                        steps=200, dt=1/60.0):
    pos = pygame.math.Vector2(start_pos)
    vel = pygame.math.Vector2(init_vel)
    path = []
    for _ in range(steps):
        to_center = CENTER - pos
        dist = to_center.length()
        if dist <= planet_radius or dist > MAX_DISTANCE:
            break
        acc = to_center.normalize() * (G * planet_mass / (dist * dist))
        vel += acc * dt
        # friction
        friction_coef = friction_percent / 100.0
        vel *= max(0.0, 1 - friction_coef * dt)
        pos += vel * dt
        path.append((int(pos.x), int(pos.y)))
    return path

# ------------------------------------------------------------------
# Pygame init & globals
# ------------------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
CENTER = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
MAX_DISTANCE = max(WIDTH, HEIGHT) * 1.5

clock = pygame.time.Clock()
font  = pygame.font.SysFont(None, 36)
small = pygame.font.SysFont(None, 24)

# menu / settings items
menu_items = ["Start Game", "Settings", "Quit"]
settings_items = [
    "Planet Radius", "Planet Density",
    "Bullet Radius", "Bullet Density",
    "Drag Scale",    "Friction",
    "Save Settings","Load Settings",
    "Back"
]

# state
settings     = Settings()
state        = STATE_MENU
menu_idx     = 0
settings_idx = 0

projectile = None
dragging   = False
drag_start = None

message      = ""           # for PLAY state
settings_msg = ""           # for SETTINGS state
# scoring marker\marker_pos = None
marker_score = 0
marker_active = False

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

        # ─────────── MENU state ───────────────────────────────────────────
        if state == STATE_MENU:
            # hover highlight
            if ev.type == pygame.MOUSEMOTION:
                for i, item in enumerate(menu_items):
                    txt = font.render(item, True, (255,255,255))
                    rect = txt.get_rect(center=(CENTER.x, 200 + i*50))
                    if rect.collidepoint(mx, my):
                        menu_idx = i
            # click selection
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                choice = menu_items[menu_idx]
                if choice == "Start Game":
                    state     = STATE_PLAY
                    projectile = None
                    message   = ""
                elif choice == "Settings":
                    state        = STATE_SETTINGS
                    settings_msg = ""
                elif choice == "Quit":
                    running = False
            # keyboard nav
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    menu_idx = (menu_idx - 1) % len(menu_items)
                elif ev.key == pygame.K_DOWN:
                    menu_idx = (menu_idx + 1) % len(menu_items)
                elif ev.key == pygame.K_RETURN:
                    choice = menu_items[menu_idx]
                    if choice == "Start Game":
                        state     = STATE_PLAY
                        projectile = None
                        message   = ""
                    elif choice == "Settings":
                        state        = STATE_SETTINGS
                        settings_msg = ""
                    elif choice == "Quit":
                        running = False
                elif ev.key == pygame.K_ESCAPE:
                    running = False

        # ───────── SETTINGS state ─────────────────────────────────────────
        elif state == STATE_SETTINGS:
            # hover
            if ev.type == pygame.MOUSEMOTION:
                for i, item in enumerate(settings_items):
                    if item not in ("Save Settings","Load Settings","Back"):
                        val = getattr(settings, item.lower().replace(' ', '_'))
                        text = f"{item}: {val}"
                    else:
                        text = item
                    txt = font.render(text, True, (255,255,255))
                    rect = txt.get_rect(topleft=(100, 150 + i*50))
                    if rect.collidepoint(mx, my):
                        settings_idx = i
            # click
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                i = settings_idx
                key = settings_items[i]
                if key == "Back":
                    state = STATE_MENU
                elif key == "Save Settings":
                    try:
                        settings.save()
                        settings_msg = f"Saved → {SETTINGS_FILE}"
                    except Exception as e:
                        settings_msg = f"Save error: {e}"
                elif key == "Load Settings":
                    try:
                        settings.load()
                        settings_msg = f"Loaded ← {SETTINGS_FILE}"
                    except Exception as e:
                        settings_msg = f"Load error: {e}"
                else:
                    text = f"{key}: {getattr(settings, key.lower().replace(' ', '_'))}"
                    txt = font.render(text, True, (255,255,255))
                    rect = txt.get_rect(topleft=(100, 150 + i*50))
                    delta = -1 if mx < rect.centerx else 1
                    attr = key.lower().replace(' ', '_')
                    lo, hi = {
                        "planet_radius":  PLANET_RADIUS_RANGE,
                        "planet_density": PLANET_DENSITY_RANGE,
                        "bullet_radius":  BULLET_RADIUS_RANGE,
                        "bullet_density": BULLET_DENSITY_RANGE,
                        "drag_scale":     DRAG_SCALE_RANGE,
                        "friction":       FRICTION_RANGE
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
                    key = settings_items[i]
                    if key not in ("Save Settings","Load Settings","Back"):
                        attr = key.lower().replace(' ', '_')
                        lo, hi = {
                            "planet_radius":  PLANET_RADIUS_RANGE,
                            "planet_density": PLANET_DENSITY_RANGE,
                            "bullet_radius":  BULLET_RADIUS_RANGE,
                            "bullet_density": BULLET_DENSITY_RANGE,
                            "drag_scale":     DRAG_SCALE_RANGE,
                            "friction":       FRICTION_RANGE
                        }[attr]
                        setattr(settings, attr, max(lo, getattr(settings, attr)-1))
                elif ev.key == pygame.K_RIGHT:
                    i = settings_idx
                    key = settings_items[i]
                    if key not in ("Save Settings","Load Settings","Back"):
                        attr = key.lower().replace(' ', '_')
                        lo, hi = {
                            "planet_radius":  PLANET_RADIUS_RANGE,
                            "planet_density": PLANET_DENSITY_RANGE,
                            "bullet_radius":  BULLET_RADIUS_RANGE,
                            "bullet_density": BULLET_DENSITY_RANGE,
                            "drag_scale":     DRAG_SCALE_RANGE,
                            "friction":       FRICTION_RANGE
                        }[attr]
                        setattr(settings, attr, min(hi, getattr(settings, attr)+1))
                elif ev.key == pygame.K_RETURN:
                    if settings_items[settings_idx] == "Save Settings":
                        try:
                            settings.save()
                            settings_msg = f"Saved → {SETTINGS_FILE}"
                        except Exception as e:
                            settings_msg = f"Save error: {e}"
                    elif settings_items[settings_idx] == "Load Settings":
                        try:
                            settings.load()
                            settings_msg = f"Loaded ← {SETTINGS_FILE}"
                        except Exception as e:
                            settings_msg = f"Load error: {e}"
                    elif settings_items[settings_idx] == "Back":
                        state = STATE_MENU
                elif ev.key == pygame.K_ESCAPE:
                    state = STATE_MENU

        # ───────── PLAY state ───────────────────────────────────────────────
        elif state == STATE_PLAY:
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
                        message    = ""
                        marker_active = False
                        continue
                # start drag
                dragging   = True
                drag_start = pygame.math.Vector2(ev.pos)
                # scoring marker: base score = distance from center
                marker_pos    = pygame.math.Vector2(ev.pos)
                base_dist      = (CENTER - marker_pos).length()
                marker_score   = int(base_dist)
                marker_active  = True

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and dragging:
                dragging = False
                drag_end = pygame.math.Vector2(ev.pos)
                vel      = (drag_start - drag_end) * settings.drag_scale
                projectile = Projectile(drag_start, vel, settings.bullet_radius)
                message    = ""

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    projectile = None
                    message    = ""
                    marker_active = False
                elif ev.key == pygame.K_ESCAPE:
                    state = STATE_MENU

    # Physics update
    if state == STATE_PLAY and projectile:
        projectile.update(
            dt,
            settings.planet_radius,
            settings.planet_mass,
            settings.friction
        )
        if not projectile.active:
            if projectile.crashed:
                message = "💥 Crashed!"
            elif projectile.lost:
                message = "🌌 Lost!"
            elif projectile.orbit_done:
                message = "✅ Orbit!"
                # apply orbit bonus: double score
                marker_score *= 2

    # Drawing
    screen.fill((0,0,0))

    if state == STATE_MENU:
        title = font.render("Orbital Shooter", True, (255,255,255))
        screen.blit(title, title.get_rect(center=(CENTER.x, 100)))
        for i, item in enumerate(menu_items):
            color = (255,255,0) if i == menu_idx else (200,200,200)
            txt   = font.render(item, True, color)
            screen.blit(txt, txt.get_rect(center=(CENTER.x, 200 + i*50)))

    elif state == STATE_SETTINGS:
        title = font.render("Settings", True, (255,255,255))
        screen.blit(title, title.get_rect(center=(CENTER.x, 60)))
        for i, item in enumerate(settings_items):
            color = (255,255,0) if i == settings_idx else (200,200,200)
            if item not in ("Save Settings","Load Settings","Back"):
                val  = getattr(settings, item.lower().replace(' ', '_'))
                text = f"{item}: {val}"
            else:
                text = item
            txt = font.render(text, True, color)
            screen.blit(txt, txt.get_rect(topleft=(100, 150 + i*50)))
        if settings_msg:
            msg = small.render(settings_msg, True, (180,180,180))
            screen.blit(msg, (100, 150 + len(settings_items)*50))

    elif state == STATE_PLAY:
        # draw planet
        pygame.draw.circle(
            screen, (0,100,255),
            (int(CENTER.x), int(CENTER.y)),
            settings.planet_radius
        )

        # draw score marker
        if marker_active and marker_pos is not None:
            txt = small.render(str(marker_score), True, (255,255,0))
            rect = txt.get_rect(center=(int(marker_pos.x), int(marker_pos.y)))
            screen.blit(txt, rect)

        # trajectory preview
        if dragging and drag_start:
            drag_end = pygame.mouse.get_pos()
            vel      = (pygame.math.Vector2(drag_start) - pygame.math.Vector2(drag_end)) * settings.drag_scale
            path     = simulate_trajectory(
                drag_start, vel,
                settings.planet_radius, settings.planet_mass,
                settings.friction
            )
            if len(path) > 1:
                pygame.draw.lines(screen, (100,255,100), False, path, 2)
            pygame.draw.line(screen, (200,200,200), drag_start, drag_end, 2)

        # draw projectile
        if projectile:
            projectile.draw(screen)

        # hints
        if not projectile and not dragging:
            instr = "Click+drag to launch; or use Menu/SPACE"
            txt   = small.render(instr, True, (255,255,255))
            screen.blit(txt, (20, 20))

        # result & Retry
        if message:
            msg_txt   = font.render(message, True, (255,255,255))
            retry_txt = small.render("Retry", True, (255,255,255))
            screen.blit(msg_txt, (20, 60))
            screen.blit(retry_txt, retry_txt.get_rect(topleft=(20, 100)))

        # Menu button
        menu_txt = small.render("Menu", True, (255,255,255))
        screen.blit(menu_txt, menu_txt.get_rect(topright=(WIDTH-10, 10)))

    pygame.display.flip()

pygame.quit()
sys.exit()
