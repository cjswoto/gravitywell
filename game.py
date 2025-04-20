# game.py

import pygame

G = 1
gravity_indicators = True
show_head_tail    = True

# how many world‐units back the tail goes, and ahead the head goes
TAIL_SCALE = 3
HEAD_SCALE = 5
# arrowhead width in world‐units
ARROWHEAD_SCALE = 5

# these will be set by main.py
camera_center = pygame.math.Vector2(0, 0)
camera_zoom   = 1.0

class Projectile:
    def __init__(self, pos, vel, radius, mass, friction):
        self.pos                 = pygame.math.Vector2(pos)
        self.vel                 = pygame.math.Vector2(vel)
        self.radius              = radius
        self.mass                = mass
        self.friction            = friction
        self.active              = True
        self.arc_time            = 0.0
        self.last_acc_components = []
        self.distance            = 0.0

    def update(self, dt, gv_radius, gv_mass, center, max_dist, others):
        if not self.active:
            return
        self.arc_time += dt

        to_center = center - self.pos
        r_center  = to_center.length()
        self.distance = r_center

        if r_center <= gv_radius + self.radius or r_center > max_dist:
            self.active = False
            return

        comps = []
        comps.append(to_center.normalize() * (G * gv_mass / (r_center*r_center)))
        for other in others:
            if other is self or not other.active:
                continue
            d  = other.pos - self.pos
            r2 = d.length_squared()
            if r2 == 0:
                continue
            comps.append(d.normalize() * (G * other.mass / r2))

        self.last_acc_components = comps

        total_acc = pygame.math.Vector2()
        for a in comps:
            total_acc += a

        self.vel += total_acc * dt
        self.vel *= max(0.0, 1 - self.friction/100.0*dt)
        self.pos += self.vel * dt

    def draw(self, surf, color):
        # helper to map world→screen
        def to_screen(wv):
            return (wv - camera_center) * camera_zoom + camera_center

        # draw gravity vectors (in screen‐space)
        if gravity_indicators:
            for acc in self.last_acc_components:
                if acc.length() == 0: continue
                dirn = acc.normalize()
                length = min(acc.length() * 50, 100)
                start_w = self.pos
                end_w   = self.pos + dirn * length
                start_s = to_screen(start_w)
                end_s   = to_screen(end_w)
                pygame.draw.line(surf, (0,255,0), start_s, end_s, 2)
                # arrowhead in world coords, then to screen
                perp_w = dirn.rotate(90) * 5
                pts_w = [
                    end_w,
                    end_w - dirn*10 + perp_w,
                    end_w - dirn*10 - perp_w
                ]
                pts_s = [to_screen(p) for p in pts_w]
                pygame.draw.polygon(surf, (0,255,0), pts_s)

        # draw head & tail
        if show_head_tail and self.vel.length() > 0:
            dirn = self.vel.normalize()
            tail_w = self.pos - dirn * (self.radius * TAIL_SCALE)
            head_w = self.pos + dirn * (self.radius * HEAD_SCALE)
            tail_s = to_screen(tail_w)
            head_s = to_screen(head_w)
            pygame.draw.line(surf, (255,255,0), tail_s, head_s, 2)

            perp_w = dirn.rotate(90) * ARROWHEAD_SCALE
            pts_w = [
                head_w,
                head_w - dirn*ARROWHEAD_SCALE + perp_w,
                head_w - dirn*ARROWHEAD_SCALE - perp_w
            ]
            pts_s = [to_screen(p) for p in pts_w]
            pygame.draw.polygon(surf, (255,255,0), pts_s)

        # draw circle
        center_s = to_screen(self.pos)
        radius_s = int(self.radius * camera_zoom)
        if radius_s > 0:
            pygame.draw.circle(surf, color,
                               (int(center_s.x), int(center_s.y)),
                               radius_s)

def simulate_trajectory(start, vel, gv_radius, gv_mass, fr, center, max_dist,
                        steps=200, dt=1/60.0):
    pos = pygame.math.Vector2(start)
    v   = pygame.math.Vector2(vel)
    path = []
    for _ in range(steps):
        to_center = center - pos
        r_center  = to_center.length()
        if r_center <= gv_radius or r_center > max_dist:
            break
        v += to_center.normalize() * (G * gv_mass / (r_center*r_center)) * dt
        v *= max(0.0, 1 - fr/100.0*dt)
        pos += v * dt
        path.append(pos.xy)
    return path
