# First-Person Weapon Animation System

## Brief
Design a modular first-person animation system that displays weapon models in the player's view, animates firing/reloading, and supports easy extension for new weapons.

## Architecture

### Core Components
1. **WeaponViewModel** - 3D weapon model that follows camera
2. **WeaponAnimator** - Handles animation state machine and transitions
3. **AnimationClip** - Defines keyframe animations (fire, reload, idle, equip)
4. **ViewModelCamera** - Separate camera for weapon rendering (prevents z-fighting)
5. **WeaponModelFactory** - Creates 3D models for each weapon type

### Animation System Design
- **State Machine**: Idle → Fire → Idle / Idle → Reload → Idle
- **Procedural Animations**: Sway, bob, recoil using code (not keyframes)
- **Keyframe Animations**: Fire flash, reload sequence
- **Animation Blending**: Smooth transitions between states

### Technical Approach
- **Separate Scene**: Weapons rendered in dedicated scene with own camera
- **Layered Rendering**: Render world first, then weapons on top (higher FOV)
- **Procedural Movement**: Weapon sway based on mouse movement, bob from walking
- **Simple Geometry**: Box/cylinder primitives (can swap for GLTF models later)

## File Structure
```
src/
├── game/
│   ├── viewmodel/
│   │   ├── WeaponViewModel.ts        # 3D weapon model container
│   │   ├── WeaponAnimator.ts         # Animation state machine
│   │   ├── ViewModelRenderer.ts      # Separate render pass for weapons
│   │   ├── animations/
│   │   │   ├── AnimationClip.ts      # Keyframe animation definition
│   │   │   ├── IdleAnimation.ts      # Breathing/sway animation
│   │   │   ├── FireAnimation.ts      # Muzzle flash + recoil
│   │   │   └── ReloadAnimation.ts    # Reload sequence
│   │   └── models/
│   │       ├── WeaponModelFactory.ts # Creates weapon meshes
│   │       ├── PistolModel.ts        # Pistol geometry
│   │       └── RifleModel.ts         # Rifle geometry
│   └── ...
```

## Animation States
```
┌─────────┐
│  Idle   │ ←────────────────┐
└────┬────┘                  │
     │                       │
     │ (fire)                │
     ↓                       │
┌─────────┐                  │
│  Fire   │ ─────────────────┤
└─────────┘                  │
     │                       │
     │ (reload pressed)      │
     ↓                       │
┌─────────┐                  │
│ Reload  │ ─────────────────┘
└─────────┘
```

## Implementation Details

### WeaponViewModel
- Holds weapon mesh (Group containing multiple parts)
- Position/rotation relative to camera
- Procedural sway/bob offsets
- Muzzle flash effect

### WeaponAnimator
- Current animation state
- Animation playback time
- Transition logic
- Callbacks for sound/effects

### ViewModelRenderer
- Separate camera with higher FOV (60-70°)
- Renders after world scene
- Clear depth buffer between passes
- Maintains weapon in front of world geometry

### Procedural Effects
1. **Weapon Sway**: Mouse movement → weapon lags behind
2. **Walk Bob**: Sine wave based on movement
3. **Recoil**: Impulse on fire → spring damping back
4. **Breathing**: Subtle idle movement

## Change List
1. Create AnimationClip base class
2. Create WeaponViewModel to hold 3D model
3. Create WeaponAnimator state machine
4. Create ViewModelRenderer with separate camera
5. Implement procedural sway/bob/recoil
6. Create WeaponModelFactory for simple geometry
7. Create PistolModel and RifleModel
8. Implement Fire and Reload animation clips
9. Integrate with WeaponManager
10. Add muzzle flash effect
11. Update Player to use view models

## Testing

### Manual Tests
- [ ] Weapon appears in bottom-right of screen
- [ ] Weapon follows camera smoothly
- [ ] Weapon sways with mouse movement
- [ ] Weapon bobs when walking
- [ ] Fire animation plays on shoot
- [ ] Recoil kicks weapon up/back
- [ ] Reload animation plays
- [ ] Weapon switches show correct models
- [ ] No z-fighting with world geometry
- [ ] Muzzle flash visible on fire
- [ ] Smooth transitions between animations

## Technical Specs

### View Model Camera
- FOV: 60° (vs 75° for world camera)
- Near plane: 0.01
- Far plane: 2.0
- Position: Relative to player camera

### Weapon Position
- X: 0.3 (right of center)
- Y: -0.2 (below center)
- Z: -0.5 (in front of camera)

### Animation Timings
- Fire: 0.1s (muzzle flash + recoil)
- Reload: Matches weapon reload time
- Equip: 0.3s

### Procedural Parameters
- Sway strength: 0.02
- Bob frequency: 2 Hz
- Bob amplitude: 0.05
- Recoil strength: 0.1 (up) + 0.05 (back)
- Recoil recovery: 0.15s
