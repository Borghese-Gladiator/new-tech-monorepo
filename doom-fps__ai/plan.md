# Browser FPS - Tech Stack & Implementation Plan

## Brief
Create a minimal, modern browser-based FPS that runs entirely client-side with focus on performance, fast iteration, and simplicity. Desktop-first (mouse + keyboard), with 3D rendering, basic physics/collision, and pointer lock.

## Recommended Stack

### Core Engine & Rendering
- **Three.js** (r160+)
  - Why: Industry standard, excellent performance, massive ecosystem, handles WebGL complexity
  - Alternatives considered: Babylon.js (heavier), raw WebGL (too low-level)

### Physics & Collision
- **Custom AABB collision**
  - Why: FPS games need fast, predictable collision for player movement (not full physics sim)
  - Why not Cannon.js/Rapier: Overkill for basic FPS movement, adds bundle size

### Build & Dev Tools
- **Vite** (v5+)
  - Why: Lightning-fast HMR, native ES modules, minimal config, excellent Three.js support
  - Why not Webpack: Slower, more complex config
  - Why not Parcel: Less Three.js ecosystem support

### Language
- **TypeScript**
  - Why: Type safety for game logic, better refactoring, modern JS features
  - Minimal tsconfig for fast iteration

### Package Manager
- **npm** (comes with Node)
  - Why: Standard, no extra installation needed

## File Structure
```
first-ai-proj/
├── src/
│   ├── main.ts              # Entry point, game loop
│   ├── game/
│   │   ├── Player.ts        # FPS player controller (movement, camera, pointer lock)
│   │   ├── World.ts         # Scene setup, level geometry
│   │   └── Collision.ts     # AABB collision detection
│   ├── utils/
│   │   └── Input.ts         # Keyboard/mouse input manager
│   └── style.css            # Minimal styles (fullscreen, no margins)
├── public/                  # Static assets (none initially)
├── index.html               # Entry HTML
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Change List
1. Initialize npm project with Vite + TypeScript + Three.js
2. Configure Vite for optimal dev experience
3. Set up TypeScript with strict mode
4. Create HTML entry point with canvas
5. Implement input manager (WASD, mouse, pointer lock)
6. Implement FPS player controller (physics-based movement)
7. Implement basic AABB collision system
8. Create initial world/level (ground plane, walls for testing)
9. Wire up game loop with delta time
10. Add basic crosshair and HUD

## Testing
### Manual Test Scripts
- [ ] Launch dev server (`npm run dev`)
- [ ] Click canvas → pointer lock activates
- [ ] Mouse look works (smooth camera rotation)
- [ ] WASD movement works (forward/back/strafe)
- [ ] Space jumps
- [ ] Collision prevents walking through walls
- [ ] ESC releases pointer lock
- [ ] No console errors
- [ ] 60fps on modern desktop browser

### Unit Tests
Not required for initial prototype - visual testing is primary validation for game feel.
