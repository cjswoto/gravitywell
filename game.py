# game.py

import pygame

G = 1
gravity_indicators = True
show_head_tail    = True

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
        central = to_center.normalize() * (G * gv_mass / (r_center * r_center))
        comps.append(central)

        for other in others:
            if other is self or not other.active:
                continue
            d  = other.pos - self.pos
            r2 = d.length_squared()
            if r2 == 0:
                continue
            comps.append(d.normalize() * (G * other.mass / r2))

        self.last_acc_components = comps

        total_acc = pygame.math.Vector2(0, 0)
        for a in comps:
            total_acc += a

        self.vel += total_acc * dt
        self.vel *= max(0.0, 1 - self.friction / 100.0 * dt)
        self.pos += self.vel * dt

    def draw(self, surf, color):
        # draw gravity indicator vectors
        if gravity_indicators:
            for acc in self.last_acc_components:
                if acc.length() == 0:
                    continue
                dirn   = acc.normalize()
                length = min(acc.length() * 50, 100)
                start  = self.pos
                end    = start + dirn * length
                pygame.draw.line(surf, (0,255,0), start, end, 2)
                perp = dirn.rotate(90) * 5
                pts = [
                    (end.x, end.y),
                    (end.x - dirn.x*10 + perp.x, end.y - dirn.y*10 + perp.y),
                    (end.x - dirn.x*10 - perp.x, end.y - dirn.y*10 - perp.y)
                ]
                pygame.draw.polygon(surf, (0,255,0), pts)

        # draw head & tail indicating direction of travel
        if show_head_tail and self.vel.length() > 0:
            dirn = self.vel.normalize()
            tail = self.pos - dirn * (self.radius * 2)
            head = self.pos + dirn * (self.radius * 2)
            pygame.draw.line(surf, (255,255,0), tail, head, 2)
            # arrowhead at head
            perp = dirn.rotate(90) * 5
            pts = [
                (head.x, head.y),
                (head.x - dirn.x*5 + perp.x, head.y - dirn.y*5 + perp.y),
                (head.x - dirn.x*5 - perp.x, head.y - dirn.y*5 - perp.y)
            ]
            pygame.draw.polygon(surf, (255,255,0), pts)

        # draw the projectile itself
        pygame.draw.circle(
            surf,
            color,
            (int(self.pos.x), int(self.pos.y)),
            self.radius
        )

def simulate_trajectory(start, vel, gv_radius, gv_mass, fr, center, max_dist, steps=200, dt=1/60.0):
    pos = pygame.math.Vector2(start)
    v   = pygame.math.Vector2(vel)
    path = []
    for _ in range(steps):
        to_center = center - pos
        r_center  = to_center.length()
        if r_center <= gv_radius or r_center > max_dist:
            break
        v += to_center.normalize() * (G * gv_mass / (r_center * r_center)) * dt
        v *= max(0.0, 1 - fr / 100.0 * dt)
        pos += v * dt
        path.append((int(pos.x), int(pos.y)))
    return path
