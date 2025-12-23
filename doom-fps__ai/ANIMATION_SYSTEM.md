# First-Person Weapon Animation System

## Overview
A comprehensive animation system for first-person weapons featuring separate rendering, procedural effects, keyframe animations, and state management.

## Architecture

### Core Components

#### 1. **WeaponViewModel**
Location: `src/game/viewmodel/WeaponViewModel.ts`

Container for the weapon's 3D model with procedural animation support.

**Features:**
- Holds weapon mesh (Three.js Group)
- Procedural sway based on mouse movement
- Procedural bob based on player movement
- Muzzle flash effects
- Position/rotation offsets

**Key Methods:**
- `updateSway(mouseDeltaX, mouseDeltaY, deltaTime)` - Apply weapon lag from mouse
- `updateBob(isMoving, deltaTime)` - Apply walking animation
- `applyAnimation(animationFrame)` - Apply keyframe animation
- `showMuzzleFlash()` - Trigger muzzle flash effect

#### 2. **WeaponAnimator**
Location: `src/game/viewmodel/WeaponAnimator.ts`

State machine for managing weapon animations.

**Animation States:**
- `IDLE` - Subtle breathing animation (loops)
- `FIRE` - Recoil + recovery (0.15s)
- `RELOAD` - Magazine swap animation (weapon-dependent)

**State Transitions:**
```
Idle ──(fire)──> Fire ──(complete)──> Idle
 │                                      ▲
 └──(reload)──> Reload ──(complete)────┘
```

**Key Methods:**
- `playFire()` - Trigger fire animation
- `playReload()` - Trigger reload animation
- `getCurrentFrame()` - Get current animation offsets
- `update(deltaTime)` - Advance animation state

#### 3. **AnimationClip** (Abstract)
Location: `src/game/viewmodel/animations/AnimationClip.ts`

Base class for all animations. Defines animation behavior and evaluation.

**Properties:**
- `duration` - Animation length in seconds
- `loop` - Whether animation repeats
- `state` - Animation state identifier

**Abstract Methods:**
- `evaluate(time)` - Returns position, rotation, scale offsets at given time

**Built-in Easing:**
- `easeInCubic(t)`
- `easeOutCubic(t)`
- `easeInOutCubic(t)`

#### 4. **ViewModelRenderer**
Location: `src/game/viewmodel/ViewModelRenderer.ts`

Separate render pass for weapons to prevent z-fighting and enable different FOV.

**Technical Details:**
- Separate Three.js scene for weapons
- Dedicated camera (60° FOV vs 75° world camera)
- Near plane: 0.01 (very close)
- Far plane: 2.0 (only renders weapons)
- Renders after world with depth buffer clear

**Rendering Order:**
1. Render world scene with main camera
2. Clear depth buffer (keep color)
3. Render weapon scene with view model camera

#### 5. **WeaponModelFactory**
Location: `src/game/viewmodel/models/WeaponModelFactory.ts`

Factory for creating weapon 3D models from simple geometry.

**Models:**
- **Pistol** - Compact handgun with grip, slide, barrel, trigger
- **Rifle** - Assault rifle with stock, receiver, barrel, handguard, magazine

**Returns:**
- `model` - Three.js Group with mesh hierarchy
- `muzzlePosition` - Offset for muzzle flash placement

## Animation System

### Procedural Animations

#### Weapon Sway
Weapon lags behind camera rotation for natural feel.

**Parameters:**
- Sway amount: 0.02
- Smooth factor: 10 (exponential smoothing)

**Implementation:**
```typescript
targetSway.x = -mouseDeltaX * 0.02;
targetSway.y = mouseDeltaY * 0.02;
currentSway.lerp(targetSway, deltaTime * 10);
```

#### Weapon Bob
Weapon moves in figure-eight pattern while walking.

**Parameters:**
- Frequency: 2 Hz
- Horizontal amplitude: 0.03
- Vertical amplitude: 0.04

**Implementation:**
```typescript
bobX = sin(time * π) * 0.03
bobY = abs(sin(time * π * 2)) * 0.04
```

### Keyframe Animations

#### Idle Animation
Subtle breathing effect.

**Duration:** Infinite (loops)
**Features:**
- Slow sine wave vertical movement
- Slight rotation sway
- Always active as base layer

#### Fire Animation
Recoil impulse with spring-back recovery.

**Duration:** 0.15 seconds
**Phases:**
1. **Recoil (0-0.03s)**: Fast kick up and back
2. **Recovery (0.03-0.15s)**: Ease back to original position

**Offsets:**
- Position Y: +0.03 → 0 (upward kick)
- Position Z: +0.1 → 0 (backward push)
- Rotation X: +0.05 → 0 (muzzle rise)

#### Reload Animation
Magazine removal and insertion.

**Duration:** Matches weapon reload time
**Phases:**
1. **Lower (0-30%)**: Weapon moves down and rotates
2. **Hold (30-70%)**: Magazine swap (off-screen)
3. **Raise (70-100%)**: Return to ready position

**Offsets:**
- Position Y: 0 → -0.3 → 0
- Position Z: 0 → +0.15 → 0
- Rotation X: 0 → +0.4 → 0
- Rotation Y: 0 → +0.3 → 0

## Integration

### With WeaponManager

WeaponManager orchestrates weapons, view models, and animators:

```typescript
interface WeaponEntry {
  weapon: Weapon;           // Game logic (ammo, damage, fire rate)
  viewModel: WeaponViewModel;   // 3D model + procedural animation
  animator: WeaponAnimator;     // Keyframe animation state
  weaponType: WeaponType;   // For model selection
}
```

**On Add Weapon:**
1. Create weapon logic instance
2. Create view model from factory
3. Create animator with reload time
4. Register callbacks (fire → playFire(), reload → playReload())
5. Add to view model scene

**On Update:**
1. Update weapon logic (cooldowns, reload)
2. Update animator (advance time, check transitions)
3. Update procedural effects (sway, bob)
4. Combine and apply to view model

### With Player

Player provides animation inputs:

- Mouse delta (for sway)
- Movement state (for bob)
- Fire/reload triggers

```typescript
const mouseDelta = input.getMouseMovement();
const isMoving = input.isKeyPressed('KeyW') || ...;

weaponManager.update(
  deltaTime,
  camera,
  scene,
  mouseDelta,
  isMoving
);
```

### Rendering Pipeline

**Game Loop:**
```typescript
1. player.update(deltaTime, scene)
   └─> weaponManager.update(...)
       └─> viewModel.applyAnimation(...)

2. viewModelRenderer.updateCamera(player.camera)

3. world.render(player.camera)
   └─> renderer.render(worldScene, worldCamera)

4. viewModelRenderer.render()
   └─> renderer.clearDepth()
   └─> renderer.render(weaponScene, weaponCamera)
```

## Adding New Weapons

### Step 1: Create Weapon Model

```typescript
// src/game/viewmodel/models/ShotgunModel.ts
export function createShotgunModel(): WeaponModelConfig {
  const group = new THREE.Group();

  // Add geometry for barrel, stock, pump, etc.
  // ...

  return {
    model: group,
    muzzlePosition: new THREE.Vector3(0, 0, -0.6)
  };
}
```

### Step 2: Register in Factory

```typescript
// WeaponModelFactory.ts
case WeaponType.SHOTGUN:
  return this.createShotgunModel();
```

### Step 3: Use in Game

```typescript
weaponManager.addWeapon(
  WeaponFactory.createWeapon(WeaponType.SHOTGUN),
  WeaponType.SHOTGUN
);
```

**That's it!** The animation system automatically:
- Creates view model
- Sets up animator with reload time
- Wires fire/reload callbacks
- Handles rendering and visibility

## Custom Animations

### Creating New Animation

```typescript
import { AnimationClip, AnimationState } from './AnimationClip';

export class InspectAnimation extends AnimationClip {
  constructor() {
    super(AnimationState.INSPECT, 2.0, false);
  }

  evaluate(time: number) {
    const t = time / this.duration;

    // Spin weapon 360°
    const rotY = this.easeInOutCubic(t) * Math.PI * 2;

    return {
      position: new THREE.Vector3(0, 0, 0),
      rotation: new THREE.Euler(0, rotY, 0),
      scale: new THREE.Vector3(1, 1, 1)
    };
  }
}
```

### Register in Animator

```typescript
// WeaponAnimator.ts
this.animations.set(AnimationState.INSPECT, new InspectAnimation());

// Add playback method
playInspect(): void {
  const inspectAnim = this.animations.get(AnimationState.INSPECT);
  if (inspectAnim) {
    this.transitionTo(inspectAnim);
  }
}
```

## Performance

### Optimizations

1. **Separate Rendering**
   - Weapons rendered in isolated scene
   - No raycast interference with world
   - Depth buffer prevents z-fighting

2. **Single Active Model**
   - Only current weapon visible
   - Others hidden but kept in memory
   - Fast weapon switching (no model reload)

3. **Procedural Animation**
   - Pure math (no keyframe lookup)
   - Minimal CPU overhead
   - Smooth at any framerate

4. **Simple Geometry**
   - ~10-20 meshes per weapon
   - Basic materials (Standard)
   - Easy to replace with GLTF models later

### Memory Footprint

Per weapon:
- Model: ~5-10 KB (geometry + materials)
- Animator: ~1 KB (state + clips)
- ViewModel: ~1 KB (offsets + references)

**Total:** ~10-15 KB per weapon (insignificant)

## Extending to GLTF Models

The system supports swapping simple geometry for real models:

```typescript
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

const loader = new GLTFLoader();
loader.load('/models/ak47.glb', (gltf) => {
  const model = gltf.scene;

  // Find muzzle bone for flash position
  const muzzle = model.getObjectByName('muzzle');

  return {
    model,
    muzzlePosition: muzzle.position
  };
});
```

Animation system remains unchanged - GLTF models drop right in.

## Technical Specs

### View Model Camera
- **FOV**: 60° (reduces distortion vs 75° world)
- **Near**: 0.01 (weapons very close to camera)
- **Far**: 2.0 (only render weapons)
- **Position**: Copies player camera exactly

### Weapon Position (Base)
- **X**: 0.3 (right of center)
- **Y**: -0.2 (below center)
- **Z**: -0.5 (in front of camera)

### Animation Speeds
- **Fire**: 150ms (quick snap)
- **Reload**: Weapon-dependent (1.5-2.5s)
- **Sway**: 10x smoothing per second
- **Bob**: 2 Hz frequency

## File Structure

```
src/game/viewmodel/
├── WeaponViewModel.ts        # Model container + procedural effects
├── WeaponAnimator.ts         # State machine
├── ViewModelRenderer.ts      # Separate render pass
├── animations/
│   ├── AnimationClip.ts      # Abstract base
│   ├── IdleAnimation.ts      # Breathing
│   ├── FireAnimation.ts      # Recoil
│   └── ReloadAnimation.ts    # Magazine swap
└── models/
    └── WeaponModelFactory.ts # Model creation
```

## Benefits

1. **Separation of Concerns**
   - Game logic (Weapon) separate from visuals (ViewModel)
   - Easy to test weapon balance without graphics
   - Artists can work on models independently

2. **Extensibility**
   - New weapons: just add model
   - New animations: extend AnimationClip
   - No core system changes

3. **Performance**
   - Dedicated camera prevents world interference
   - Procedural effects run efficiently
   - Minimal memory overhead

4. **Flexibility**
   - Can use simple geometry or GLTF
   - Animations blend naturally
   - Easy to tune feel (sway, bob, recoil)
