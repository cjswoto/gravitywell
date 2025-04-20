import sys
import math
import json
import pygame

# ─────────────────────────────────────────────────────────────────────────────
# Orbital Shooter with Multiple Bullets & Continuous Scoring
#
# - Fullscreen
# - Menu: Start Game, Settings, Quit
# - Settings:
#     • Planet Radius & Density
#     • Bullet Radius & Density
#     • Drag Scale (1–100; drag distance → shot power)\#     • Friction (% deceleration per second)
#     • Save/Load settings
# - Click+drag to spawn bullets; multiple bullets in play
# - Scoring:
#     • After 20s of flight, each bullet adds 1 point per second it remains active
# - Continuous play (no game end on orbit)
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
DRAG_SCALE_RANGE      = (1, 100)
FRICTION_RANGE        = (0, 100)

SETTINGS_FILE = "settings.json"

# ------------------------------------------------------------------
# Settings container
# ------------------------------------------------------------------
class Settings:
    def __init__(self):
        self.planet_radius  = 30
        self.planet_density = 10
        self.bullet_radius  = 5
        self.bullet_density = 1
        self.drag_scale     = 20
        self.friction       = 0

    @property
    def planet_mass(self):
        return self.planet_density * (self.planet_radius ** 2)

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
        self.planet_radius  = max(PLANET_RADIUS_RANGE[0], min(PLANET_RADIUS_RANGE[1], data.get("planet_radius", self.planet_radius)))
        self.planet_density = max(PLANET_DENSITY_RANGE[0], min(PLANET_DENSITY_RANGE[1], data.get("planet_density", self.planet_density)))
        self.bullet_radius  = max(BULLET_RADIUS_RANGE[0], min(BULLET_RADIUS_RANGE[1], data.get("bullet_radius", self.bullet_radius)))
        self.bullet_density = max(BULLET_DENSITY_RANGE[0], min(BULLET_DENSITY_RANGE[1], data.get("bullet_density", self.bullet_density)))
        self.drag_scale     = max(DRAG_SCALE_RANGE[0], min(DRAG_SCALE_RANGE[1], data.get("drag_scale", self.drag_scale)))
        self.friction       = max(FRICTION_RANGE[0], min(FRICTION_RANGE[1], data.get("friction", self.friction)))

# ------------------------------------------------------------------
# Projectile class
# ------------------------------------------------------------------
class Projectile:
    def __init__(self, pos, vel, radius):
        self.pos         = pygame.math.Vector2(pos)
        self.vel         = pygame.math.Vector2(vel)
        self.radius      = radius
        self.active      = True
        self.arc_time    = 0.0

    def update(self, dt, planet_radius, planet_mass, friction):
        if not self.active:
            return
        self.arc_time += dt
        # gravity
        to_center = CENTER - self.pos
        dist = to_center.length()
        # crash or lost
        if dist <= planet_radius + self.radius or dist > MAX_DISTANCE:
            self.active = False
            return
        # acceleration
        acc = to_center.normalize() * (G * planet_mass / (dist * dist))
        self.vel += acc * dt
        self.vel *= max(0.0, 1 - friction/100.0 * dt)
        self.pos += self.vel * dt

    def draw(self, surf):
        pygame.draw.circle(surf, (255,255,255), (int(self.pos.x), int(self.pos.y)), self.radius)

# ------------------------------------------------------------------
# Trajectory preview
# ------------------------------------------------------------------
def simulate_trajectory(start, vel, planet_radius, planet_mass, friction, steps=200, dt=1/60.0):
    pos = pygame.math.Vector2(start)
    v   = pygame.math.Vector2(vel)
    path = []
    for _ in range(steps):
        d = CENTER - pos
        dist = d.length()
        if dist <= planet_radius or dist > MAX_DISTANCE:
            break
        v += d.normalize() * (G * planet_mass / (dist*dist)) * dt
        v *= max(0.0, 1 - friction/100.0 * dt)
        pos += v * dt
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

menu_items    = ["Start Game", "Settings", "Quit"]
settings_items= [
    "Planet Radius", "Planet Density", "Bullet Radius", "Bullet Density",
    "Drag Scale", "Friction", "Save Settings", "Load Settings", "Back"
]

settings      = Settings()
state         = STATE_MENU
menu_idx      = 0
settings_idx  = 0

# store all bullets
bullets = []
# cumulative score
total_score = 0.0

dragging   = False

running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    mx, my = pygame.mouse.get_pos()
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

        # MENU
        if state == STATE_MENU:
            if ev.type == pygame.MOUSEMOTION:
                for i,item in enumerate(menu_items):
                    txt=font.render(item,True,(255,255,255))
                    if txt.get_rect(center=(CENTER.x,200+i*50)).collidepoint(mx,my):
                        menu_idx = i
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                choice = menu_items[menu_idx]
                if choice == "Start Game":
                    state = STATE_PLAY
                    bullets.clear()
                    total_score = 0.0
                elif choice == "Settings": state = STATE_SETTINGS
                elif choice == "Quit": running = False
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP,pygame.K_DOWN):
                    menu_idx=(menu_idx+(1 if ev.key==pygame.K_DOWN else -1))%len(menu_items)
                elif ev.key==pygame.K_RETURN:
                    choice=menu_items[menu_idx]
                    if choice=="Start Game": state,bullets,total_score = STATE_PLAY,[],0.0
                    elif choice=="Settings": state=STATE_SETTINGS
                    elif choice=="Quit": running=False
                elif ev.key==pygame.K_ESCAPE: running=False

        # SETTINGS
        elif state == STATE_SETTINGS:
            if ev.type == pygame.MOUSEMOTION:
                for i,item in enumerate(settings_items):
                    text=item if item in ("Save Settings","Load Settings","Back") else f"{item}: {getattr(settings,item.lower().replace(' ','_'))}"
                    if font.render(text,True,(255,255,255)).get_rect(topleft=(100,150+i*50)).collidepoint(mx,my): settings_idx=i
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                key=settings_items[settings_idx]
                if key=="Back": state=STATE_MENU
                elif key=="Save Settings": settings.save()
                elif key=="Load Settings": settings.load()
                else:
                    text=f"{key}: {getattr(settings,key.lower().replace(' ','_'))}"
                    rect=font.render(text,True,(255,255,255)).get_rect(topleft=(100,150+settings_idx*50))
                    delta=-1 if mx<rect.centerx else 1
                    attr=key.lower().replace(' ','_')
                    lo,hi=globals()[attr.upper()+"_RANGE"]
                    setattr(settings,attr,max(lo,min(hi,getattr(settings,attr)+delta)))
            if ev.type==pygame.KEYDOWN:
                if ev.key in (pygame.K_UP,pygame.K_DOWN): settings_idx=(settings_idx+(1 if ev.key==pygame.K_DOWN else -1))%len(settings_items)
                elif ev.key in (pygame.K_LEFT,pygame.K_RIGHT):
                    key=settings_items[settings_idx]
                    if key not in ("Save Settings","Load Settings","Back"):
                        attr=key.lower().replace(' ','_'); lo,hi=globals()[attr.upper()+"_RANGE"]
                        change=-1 if ev.key==pygame.K_LEFT else 1
                        setattr(settings,attr,max(lo,min(hi,getattr(settings,attr)+change)))
                elif ev.key==pygame.K_RETURN and settings_items[settings_idx]=="Back": state=STATE_MENU
                elif ev.key==pygame.K_ESCAPE: state=STATE_MENU

        # PLAY
        elif state == STATE_PLAY:
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                dragging=True; drag_start=pygame.math.Vector2(ev.pos)
            if ev.type==pygame.MOUSEBUTTONUP and ev.button==1 and dragging:
                dragging=False; drag_end=pygame.math.Vector2(ev.pos)
                vel=(drag_start-drag_end)*(settings.drag_scale/10)
                bullets.append(Projectile(drag_start,vel,settings.bullet_radius))
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: state=STATE_MENU

    # update bullets and scoring
    for b in bullets[:]:
        b.update(dt,settings.planet_radius,settings.planet_mass,settings.friction)
        if b.active and b.arc_time>20.0:
            total_score += dt
        if not b.active:
            bullets.remove(b)

    # draw
    screen.fill((0,0,0))
    if state==STATE_MENU:
        screen.blit(font.render("Orbital Shooter",True,(255,255,255)),font.render("Orbital Shooter",True,(255,255,255)).get_rect(center=(CENTER.x,100)))
        for i,item in enumerate(menu_items): color=(255,255,0) if i==menu_idx else (200,200,200); screen.blit(font.render(item,True,color),font.render(item,True,color).get_rect(center=(CENTER.x,200+i*50)))
    elif state==STATE_SETTINGS:
        screen.blit(font.render("Settings",True,(255,255,255)),font.render("Settings",True,(255,255,255)).get_rect(center=(CENTER.x,60)))
        for i,item in enumerate(settings_items): text=item if item in ("Save Settings","Load Settings","Back") else f"{item}: {getattr(settings,item.lower().replace(' ','_'))}"; color=(255,255,0) if i==settings_idx else (200,200,200); screen.blit(font.render(text,True,color),font.render(text,True,color).get_rect(topleft=(100,150+i*50)))
    elif state==STATE_PLAY:
        pygame.draw.circle(screen,(0,100,255),(int(CENTER.x),int(CENTER.y)),settings.planet_radius)
        if 'dragging' in locals() and dragging:
            drag_end=pygame.mouse.get_pos(); vel=(pygame.math.Vector2(drag_start)-pygame.math.Vector2(drag_end))*(settings.drag_scale/10); path=simulate_trajectory(drag_start,vel,settings.planet_radius,settings.planet_mass,settings.friction)
            if len(path)>1: pygame.draw.lines(screen,(100,255,100),False,path,2)
            pygame.draw.line(screen,(200,200,200),drag_start,drag_end,2)
        for b in bullets: b.draw(screen)
        screen.blit(font.render(f"Score: {int(total_score)}",True,(255,255,255)),(10,10))
        screen.blit(small.render("Menu",True,(255,255,255)),small.render("Menu",True,(255,255,255)).get_rect(topright=(WIDTH-10,10)))
    pygame.display.flip()
pygame.quit()
sys.exit()
