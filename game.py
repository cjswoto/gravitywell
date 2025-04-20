import pygame, math

G = 1
gravity_indicators = True

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

    def update(self, dt, gv_radius, gv_mass, center, max_dist, others):
        if not self.active:
            return
        self.arc_time += dt
        to_center = center - self.pos
        r_center = to_center.length()
        if r_center <= gv_radius + self.radius or r_center > max_dist:
            self.active = False
            return

        comps = []
        # gravity well pull
        central = to_center.normalize() * (G * gv_mass / (r_center * r_center))
        comps.append(central)
        # mutual pulls
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
        r_center = to_center.length()
        if r_center <= gv_radius or r_center > max_dist:
            break
        v += to_center.normalize() * (G * gv_mass / (r_center * r_center)) * dt
        v *= max(0.0, 1 - fr / 100.0 * dt)
        pos += v * dt
        path.append((int(pos.x), int(pos.y)))
    return path
