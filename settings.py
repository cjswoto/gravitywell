import json

PLANET_RADIUS_RANGE = (10, 200)
PLANET_DENSITY_RANGE = (1, 100)
BULLET_RADIUS_RANGE = (2, 20)
BULLET_DENSITY_RANGE = (1, 50)
DRAG_SCALE_RANGE = (1, 100)
FRICTION_RANGE = (0, 100)

SETTINGS_FILE = "settings.json"
GAME_SAVE_FILE = "savegame.json"


class Settings:
    def __init__(self):
        self.planet_radius = 30
        self.planet_density = 10
        self.bullet_radius = 5
        self.bullet_density = 1
        self.drag_scale = 20
        self.friction = 0

    @property
    def planet_mass(self):
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
        for k, v in data.items():
            if hasattr(self, k):
                rng = globals().get(k.upper() + "_RANGE")
                if rng:
                    lo, hi = rng
                    setattr(self, k, max(lo, min(hi, v)))
                else:
                    setattr(self, k, v)
