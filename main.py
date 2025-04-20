# main.py

import sys
import json
import pygame
import game
from settings import (
    Settings,
    GV_RADIUS_RANGE, GV_DENSITY_RANGE,
    BULLET_RADIUS_RANGE, BULLET_DENSITY_RANGE,
    DRAG_SCALE_RANGE, FRICTION_RANGE,
    GAME_SAVE_FILE
)
from game import Projectile, simulate_trajectory

STATE_MENU     = "MENU"
STATE_SETTINGS = "SETTINGS"
STATE_SAVELOAD = "SAVELOAD"
STATE_PLAY     = "PLAY"
FPS            = 60

pygame.init()
screen        = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
CENTER        = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
MAX_DISTANCE  = max(WIDTH, HEIGHT) * 1.5

clock = pygame.time.Clock()
font  = pygame.font.SysFont(None, 36)
small = pygame.font.SysFont(None, 24)

menu_items       = ["Start Game", "Settings", "Save/Load", "Quit"]
save_items       = ["Save Game", "Load Game", "Back"]
settings_options = [
    ("GV Radius",      "gv_radius"),
    ("GV Density",     "gv_density"),
    ("Bullet Radius",  "bullet_radius"),
    ("Bullet Density", "bullet_density"),
    ("Drag Scale",     "drag_scale"),
    ("Friction",       "friction"),
    ("Save Settings",  None),
    ("Load Settings",  None),
    ("Back",           None),
]

settings        = Settings()
state           = STATE_MENU
menu_idx        = save_idx = settings_idx = 0
bullets         = []
total_score     = 0.0
paused          = False
dragging        = False
drag_start      = pygame.math.Vector2(0, 0)
in_game_menu    = False
selected_bullet = None

gv_min  = GV_DENSITY_RANGE[0] * (GV_RADIUS_RANGE[0]**2)
gv_max  = GV_DENSITY_RANGE[1] * (GV_RADIUS_RANGE[1]**2)
bul_min = BULLET_DENSITY_RANGE[0] * (BULLET_RADIUS_RANGE[0]**2)
bul_max = BULLET_DENSITY_RANGE[1] * (BULLET_RADIUS_RANGE[1]**2)

# camera / zoom
zoom      = 1.0
ZOOM_STEP = 0.1
game.camera_center = CENTER
game.camera_zoom   = zoom

def mass_to_color(m, mn, mx):
    t = max(0.0, min(1.0, (m - mn)/(mx - mn)))
    g = int(255 * (1 - t))
    return (255, g, g)

def to_screen(wp):
    return (wp - CENTER) * zoom + CENTER

def save_game():
    data = {
        "settings": settings.to_dict(),
        "bullets": [
            {
                "pos": [b.pos.x, b.pos.y],
                "vel": [b.vel.x, b.vel.y],
                "radius": b.radius,
                "mass": b.mass,
                "friction": b.friction,
                "arc_time": b.arc_time
            } for b in bullets
        ],
        "score": total_score
    }
    with open(GAME_SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_game():
    global bullets, total_score
    with open(GAME_SAVE_FILE, "r") as f:
        data = json.load(f)
    if "settings" in data:
        settings.load()
    total_score = data.get("score", 0.0)
    bullets = []
    for rec in data.get("bullets", []):
        b = Projectile(
            rec["pos"], rec["vel"],
            rec["radius"], rec.get("mass", settings.bullet_mass),
            rec.get("friction", settings.friction)
        )
        b.arc_time = rec.get("arc_time", 0.0)
        bullets.append(b)

while True:
    dt = clock.tick(FPS) / 1000.0
    mx, my = pygame.mouse.get_pos()

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Zoom controls
        if state == STATE_PLAY:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                    zoom = min(3.0, zoom + ZOOM_STEP)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    zoom = max(0.2, zoom - ZOOM_STEP)
                game.camera_zoom = zoom
            elif ev.type == pygame.MOUSEWHEEL:
                zoom = max(0.2, min(3.0, zoom + ev.y * ZOOM_STEP))
                game.camera_zoom = zoom

        # Play‑state toggles
        if state == STATE_PLAY and ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_p:
                paused = not paused
            elif ev.key == pygame.K_g:
                game.gravity_indicators = not game.gravity_indicators
            elif ev.key == pygame.K_d:
                game.show_head_tail = not game.show_head_tail
            elif ev.key == pygame.K_s:
                in_game_menu = not in_game_menu

        # Main menu
        if state == STATE_MENU:
            if ev.type == pygame.MOUSEMOTION:
                for i, it in enumerate(menu_items):
                    surf = font.render(it, True, (255,255,255))
                    if surf.get_rect(center=(CENTER.x, 200+i*50)).collidepoint(mx, my):
                        menu_idx = i
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                c = menu_items[menu_idx]
                if c == "Start Game":
                    state = STATE_PLAY; bullets.clear(); total_score = 0.0; paused = False
                elif c == "Settings":
                    state = STATE_SETTINGS
                elif c == "Save/Load":
                    state = STATE_SAVELOAD
                elif c == "Quit":
                    pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_DOWN):
                    menu_idx = (menu_idx + (1 if ev.key==pygame.K_DOWN else -1)) % len(menu_items)
                elif ev.key == pygame.K_RETURN:
                    c = menu_items[menu_idx]
                    if c == "Start Game":
                        state = STATE_PLAY; bullets.clear(); total_score = 0.0; paused = False
                    elif c == "Settings":
                        state = STATE_SETTINGS
                    elif c == "Save/Load":
                        state = STATE_SAVELOAD
                    elif c == "Quit":
                        pygame.quit(); sys.exit()
                elif ev.key == pygame.K_ESCAPE:
                    # Return to play instead of quitting
                    state = STATE_PLAY
                    paused = False

        # Settings screen
        elif state == STATE_SETTINGS:
            if ev.type == pygame.MOUSEMOTION:
                for i,(disp,attr) in enumerate(settings_options):
                    text = disp if attr is None else f"{disp}: {getattr(settings,attr)}"
                    surf = font.render(text, True, (255,255,255))
                    if surf.get_rect(topleft=(100,150+i*50)).collidepoint(mx, my):
                        settings_idx = i
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                disp, attr = settings_options[settings_idx]
                if attr is None:
                    if disp=="Back":
                        state = STATE_MENU
                    elif disp=="Save Settings":
                        settings.save()
                    elif disp=="Load Settings":
                        settings.load()
                else:
                    cur = getattr(settings, attr)
                    surf = font.render(f"{disp}: {cur}", True, (255,255,255))
                    r = surf.get_rect(topleft=(100,150+settings_idx*50))
                    delta = -1 if mx < r.centerx else 1
                    lo, hi = globals()[attr.upper()+"_RANGE"]
                    setattr(settings, attr, max(lo, min(hi, cur+delta)))
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_DOWN):
                    settings_idx = (settings_idx + (1 if ev.key==pygame.K_DOWN else -1)) % len(settings_options)
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    disp, attr = settings_options[settings_idx]
                    if attr:
                        cur = getattr(settings, attr)
                        delta = -1 if ev.key==pygame.K_LEFT else 1
                        lo, hi = globals()[attr.upper()+"_RANGE"]
                        setattr(settings, attr, max(lo, min(hi, cur+delta)))
                elif ev.key == pygame.K_RETURN and settings_options[settings_idx][0]=="Back":
                    state = STATE_MENU
                elif ev.key == pygame.K_ESCAPE:
                    state = STATE_MENU

        # Save/Load screen
        elif state == STATE_SAVELOAD:
            if ev.type == pygame.MOUSEMOTION:
                for i, it in enumerate(save_items):
                    surf = font.render(it, True, (255,255,255))
                    if surf.get_rect(center=(CENTER.x,200+i*50)).collidepoint(mx, my):
                        save_idx = i
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                c = save_items[save_idx]
                if c == "Save Game":
                    save_game()
                elif c == "Load Game":
                    load_game(); state = STATE_PLAY; paused = False
                elif c == "Back":
                    state = STATE_MENU
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_DOWN):
                    save_idx = (save_idx + (1 if ev.key==pygame.K_DOWN else -1)) % len(save_items)
                elif ev.key == pygame.K_RETURN:
                    c = save_items[save_idx]
                    if c == "Save Game":
                        save_game()
                    elif c == "Load Game":
                        load_game(); state = STATE_PLAY; paused = False
                    elif c == "Back":
                        state = STATE_MENU
                elif ev.key == pygame.K_ESCAPE:
                    state = STATE_MENU

        # Play state
        elif state == STATE_PLAY:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                if in_game_menu:
                    in_game_menu = False
                else:
                    save_game()
                    state = STATE_MENU
                    paused = False

            if in_game_menu and ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i,(disp,attr) in enumerate(settings_options):
                    if attr is None: continue
                    y = 60 + i*40
                    if pygame.Rect(60,y,30,30).collidepoint(ev.pos):
                        lo, hi = globals()[attr.upper()+"_RANGE"]
                        setattr(settings, attr, max(lo, getattr(settings,attr)-1))
                    elif pygame.Rect(310,y,30,30).collidepoint(ev.pos):
                        lo, hi = globals()[attr.upper()+"_RANGE"]
                        setattr(settings, attr, min(hi, getattr(settings,attr)+1))
                continue

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 3:
                click = pygame.math.Vector2(ev.pos)
                selected_bullet = None
                for b in bullets:
                    if (b.pos - click).length() <= b.radius*2:
                        selected_bullet = b
                        break

            if not paused:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    dragging   = True
                    drag_start = pygame.math.Vector2(ev.pos)
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and dragging:
                    dragging = False
                    drag_end = pygame.math.Vector2(ev.pos)
                    vel      = (drag_start - drag_end) * (settings.drag_scale/10)
                    bullets.append(Projectile(
                        drag_start, vel,
                        settings.bullet_radius,
                        settings.bullet_mass,
                        settings.friction
                    ))

    if state == STATE_PLAY and not paused:
        for b in bullets[:]:
            b.update(
                dt,
                settings.gv_radius, settings.gv_mass,
                CENTER, MAX_DISTANCE,
                bullets
            )
            if b.active and b.arc_time > 20:
                total_score += dt
            if not b.active:
                bullets.remove(b)

    screen.fill((0,0,0))

    if state == STATE_PLAY:
        # draw gravity well
        gv_color = mass_to_color(settings.gv_mass, gv_min, gv_max)
        center_s = to_screen(CENTER)
        pygame.draw.circle(
            screen, gv_color,
            (int(center_s.x), int(center_s.y)),
            int(settings.gv_radius * zoom)
        )

        # trajectory preview
        if not paused and dragging:
            de  = pygame.mouse.get_pos()
            vel = (drag_start - pygame.math.Vector2(de)) * (settings.drag_scale/10)
            path = simulate_trajectory(
                drag_start, vel,
                settings.gv_radius, settings.gv_mass,
                settings.friction, CENTER, MAX_DISTANCE
            )
            if len(path) > 1:
                pts = [to_screen(pygame.math.Vector2(p)) for p in path]
                pygame.draw.lines(screen, (100,255,100), False, pts, max(1,int(2*zoom)))
            pygame.draw.line(
                screen, (200,200,200),
                to_screen(drag_start),
                to_screen(pygame.math.Vector2(de)),
                max(1,int(2*zoom))
            )

        for b in bullets:
            col = mass_to_color(b.mass, bul_min, bul_max)
            b.draw(screen, col)

        screen.blit(font.render(f"Score: {int(total_score)}", True, (255,255,255)), (10,10))
        screen.blit(small.render(f"Objects: {len(bullets)}", True, (255,255,255)), (10,40))
        if bullets:
            oldest = max(b.arc_time for b in bullets)
            screen.blit(small.render(f"Oldest: {oldest:.1f}s", True, (255,255,255)), (10,65))

        if selected_bullet:
            info = [
                f"Pos:   {selected_bullet.pos.x:.1f},{selected_bullet.pos.y:.1f}",
                f"Dist:  {selected_bullet.distance:.1f}",
                f"Speed: {selected_bullet.vel.length():.1f}",
                f"Age:   {selected_bullet.arc_time:.1f}s",
                f"Mass:  {selected_bullet.mass:.1f}",
                f"Fric:  {selected_bullet.friction:.1f}%"
            ]
            for i, line in enumerate(info):
                screen.blit(small.render(line, True, (255,255,0)), (10,90+i*20))

        if in_game_menu:
            overlay = pygame.Surface((380, len(settings_options)*40 + 40), pygame.SRCALPHA)
            overlay.fill((0,0,0,200))
            screen.blit(overlay, (50,50))
            for i, (disp, attr) in enumerate(settings_options):
                y = 60 + i*40
                text = disp if attr is None else f"{disp}: {getattr(settings, attr)}"
                color = (255,255,0) if i==settings_idx else (200,200,200)
                screen.blit(font.render(text, True, color), (100, y))
                if attr:
                    pygame.draw.rect(screen, (180,180,180), (60, y, 30, 30))
                    screen.blit(small.render("-", True, (0,0,0)), (68, y+2))
                    pygame.draw.rect(screen, (180,180,180), (310, y, 30, 30))
                    screen.blit(small.render("+", True, (0,0,0)), (318, y+2))

    elif state == STATE_MENU:
        for i, it in enumerate(menu_items):
            color = (255,255,0) if i==menu_idx else (200,200,200)
            surf  = font.render(it, True, color)
            screen.blit(surf, surf.get_rect(center=(CENTER.x,200+i*50)))

    elif state == STATE_SETTINGS:
        for i,(disp,attr) in enumerate(settings_options):
            text  = disp if attr is None else f"{disp}: {getattr(settings, attr)}"
            color = (255,255,0) if i==settings_idx else (200,200,200)
            surf  = font.render(text, True, color)
            screen.blit(surf, surf.get_rect(topleft=(100,150+i*50)))

    elif state == STATE_SAVELOAD:
        for i, it in enumerate(save_items):
            color = (255,255,0) if i==save_idx else (200,200,200)
            surf  = font.render(it, True, color)
            screen.blit(surf, surf.get_rect(center=(CENTER.x,200+i*50)))

    pygame.display.flip()
