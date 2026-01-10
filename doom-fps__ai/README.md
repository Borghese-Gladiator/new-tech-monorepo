# Browser FPS

A minimal, high-performance first-person shooter built entirely in the browser.

## Tech Stack

- **Three.js** - 3D rendering and WebGL abstraction
- **TypeScript** - Type-safe game logic
- **Vite** - Lightning-fast dev server and build tool
- **Custom AABB Collision** - Lightweight collision detection optimized for FPS movement

## Features

- ✅ First-person camera with pointer lock
- ✅ WASD movement with proper sliding collision
- ✅ Space to jump with gravity
- ✅ Mouse look (pitch/yaw)
- ✅ 3D world with platforms and obstacles
- ✅ **Modular weapon system** (hitscan, fire rate, damage, spread)
- ✅ **First-person weapon animations** (fire, reload, sway, bob)
- ✅ Pistol and Rifle with animated 3D models
- ✅ Procedural weapon sway and walk bobbing
- ✅ Muzzle flash effects on fire
- ✅ Bullet impact effects (decals + particles)
- ✅ Separate weapon rendering (no z-fighting)
- ✅ 60fps on modern desktop browsers

## Getting Started

```bash
# Install dependencies
npm install

# Start dev server (opens at http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Controls

- **Click** - Activate pointer lock
- **WASD** - Move
- **Space** - Jump
- **Mouse** - Look around
- **Left Click** - Fire weapon
- **Hold Left Click** - Full-auto fire (rifle)
- **R** - Reload
- **1 / 2** - Switch weapons
- **ESC** - Release pointer lock

## Project Structure

```
src/
├── main.ts              # Entry point, game loop
├── game/
│   ├── Player.ts        # FPS player controller
│   ├── World.ts         # Scene setup, level geometry
│   ├── Collision.ts     # AABB collision system
│   ├── viewmodel/
│   │   ├── WeaponViewModel.ts       # Weapon model container
│   │   ├── WeaponAnimator.ts        # Animation state machine
│   │   ├── ViewModelRenderer.ts     # Separate weapon rendering
│   │   ├── animations/
│   │   │   ├── AnimationClip.ts     # Abstract animation base
│   │   │   ├── IdleAnimation.ts     # Breathing animation
│   │   │   ├── FireAnimation.ts     # Recoil animation
│   │   │   └── ReloadAnimation.ts   # Reload animation
│   │   └── models/
│   │       └── WeaponModelFactory.ts # 3D model creation
│   └── weapons/
│       ├── Weapon.ts           # Abstract base class
│       ├── HitscanWeapon.ts    # Raycast weapon implementation
│       ├── WeaponManager.ts    # Player weapon state
│       ├── WeaponFactory.ts    # Weapon instantiation
│       ├── weapons/
│       │   ├── Pistol.ts       # Semi-auto pistol
│       │   └── Rifle.ts        # Full-auto rifle
│       └── effects/
│           └── HitEffect.ts    # Bullet impact visuals
├── utils/
│   └── Input.ts         # Keyboard/mouse input manager
└── style.css            # Minimal fullscreen styles
```

## Architecture Decisions

### Why Three.js?
- Industry standard with excellent WebGL performance
- Massive ecosystem and community support
- Handles rendering complexity while staying lightweight

### Why Custom Collision?
- FPS games need fast, predictable box collision (not full physics)
- Sliding collision allows smooth wall movement
- Saves ~100KB+ compared to full physics engines

### Why Vite?
- Sub-second hot module replacement
- Zero-config Three.js support
- Modern ES modules with optimal tree-shaking

## Performance

- Target: 60fps on desktop browsers
- Bundle size: ~600KB (Three.js + game code)
- No backend required - runs entirely client-side

## Systems Documentation

### Weapon System
Modular weapon architecture with hitscan mechanics, fire rates, and damage models.

- **[WEAPON_SYSTEM.md](./WEAPON_SYSTEM.md)** - Full system documentation
- **[ADDING_WEAPONS.md](./ADDING_WEAPONS.md)** - Quick guide to adding new weapons

### Animation System
First-person weapon animations with procedural effects and keyframe sequences.

- **[ANIMATION_SYSTEM.md](./ANIMATION_SYSTEM.md)** - Complete animation system documentation

### Adding a New Weapon (3 steps)

1. Create weapon class extending `HitscanWeapon`
2. Register in `WeaponFactory` enum + switch
3. Done! Weapon has automatic fire rate, reload, effects

Example:
```typescript
export class Sniper extends HitscanWeapon {
  constructor() {
    super({
      name: 'Sniper Rifle',
      fireRate: 40,      // Slow fire
      damage: 100,       // One-shot kill
      range: 500,
      spread: 0,         // Perfect accuracy
      maxAmmo: 5,
      reloadTime: 3.0,
      fireMode: FireMode.SEMI_AUTO
    });
  }
}
```

## Next Steps

To extend this foundation:
- ✅ ~~Add weapons and shooting mechanics~~ (Done!)
- Implement enemy AI with health system
- Add sound effects (Web Audio API)
- Add textures and materials
- Create multiple levels
- Add weapon models/animations
- Implement multiplayer via WebRTC or WebSockets
