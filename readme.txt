GravityWell Arcade
==================

GravityWell is a fullscreen arcade-style physics game where you launch projectiles (“bullets”) into a central gravity well (the “GV Object”) and try to get them to orbit rather than crash or escape. You can tweak every physical parameter, visualize gravitational forces and trajectories, and even zoom and inspect individual objects in real time.

---

Features
--------
- **Fully configurable physics**
  - Adjust GV object radius & density (mass), bullet radius & density (mass), drag scale and friction
  - Real-time in-game settings overlay (press S) with hold-to-repeat +/- buttons
- **Trajectory preview**
  - Click & drag to aim; green trajectory line shows the expected path
- **Multiple simultaneous bullets**
  - Spawn as many projectiles as you like; each independently simulated
  - Score accumulates per second beyond 20s of orbital flight
- **Gravity & motion visualization**
  - Toggle gravity vectors on/off with G
  - Toggle head/tail arrows on bullets with D
  - Bullets color-coded white→red by mass (heat-map style)
- **Zoom & pan**
  - Mouse wheel or +/- to zoom in/out (world expands/contracts around center)
- **Object inspection & control**
  - Right-click a bullet to select it
  - Selected bullet stats show position, distance, speed, age, mass, friction
  - Adjust its speed up/down in 0.1-unit increments via on-HUD +/- buttons
- **Save & load**
  - Save current settings or game state at any time from menu or in-game
  - Load and resume exactly where you left off
- **Built-in tutorial**
  - “About” menu runs an auto-play demo with on-screen instructions

---

Installation
------------
1. Clone the repository.
2. Create and activate a Python 3 virtual environment.
3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

---

Running the Game
----------------
From your project root:

```
python main.py
```

---

Controls
--------
- **Main menu**
  - ↑/↓ or mouse hover & click
  - Enter or click “Start Game”, “About”, “Settings”, “Save/Load” or “Quit”
- **Gameplay**
  - **Click & drag (left mouse)** → aim & fire projectiles
  - **Right-click** → select a projectile for inspection
  - **Mouse wheel** or **+ / –** → zoom in/out
  - **P** → pause / resume simulation
  - **G** → toggle gravity-vector indicators
  - **D** → toggle head-tail arrows on bullets
  - **S** → toggle in-game settings overlay
  - **ESC** → if overlay open: close overlay
    otherwise: save game & return to main menu
- **In-game settings**
  - Click or hold the on-screen “–” / “+” buttons to adjust values by 1
  - Values auto-repeat if held down
- **Selected-bullet speed**
  - When a bullet is selected, click the HUD “–” / “+” next to its Speed line to decrease/increase velocity by 0.1
- **Save/Load**
  - Choose “Save Game” or “Load Game” from the menu or in-game overlay

---

File Structure
--------------
```
/GravityWell
├── main.py         # application entry point & UI
├── game.py         # projectile physics & drawing routines
├── settings.py     # user-tweakable ranges & persistence
├── about.py        # tutorial demo screen
├── savegame.json   # sample saved game state
├── settings.json   # last-saved user settings
└── requirements.txt
```

---

License
-------
MIT License

Enjoy your orbits!