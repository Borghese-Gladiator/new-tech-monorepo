# Weapon System Documentation

## Overview
A modular, extensible weapon system built on clean abstractions with support for hitscan weapons, fire rates, damage, and spread mechanics.

## Architecture

### Core Classes

#### `Weapon` (Abstract Base)
Location: `src/game/weapons/Weapon.ts`

The base class for all weapons. Defines the weapon interface and shared behavior.

**Key Properties:**
- `fireRate`: Rounds per minute
- `damage`: Damage per shot
- `range`: Maximum effective range
- `spread`: Accuracy cone in degrees (0 = perfect accuracy)
- `maxAmmo`: Magazine capacity
- `reloadTime`: Time to reload in seconds
- `fireMode`: Semi-auto, burst, or full-auto

**Key Methods:**
- `fire()`: Abstract method - attempt to fire weapon
- `reload()`: Start reload sequence
- `canFire()`: Check if weapon can fire (cooldown, ammo, etc.)
- `update()`: Update weapon state (reloading, etc.)

**Event Callbacks:**
- `onFire`: Triggered when weapon fires
- `onReload`: Triggered when reload starts
- `onEmpty`: Triggered when trying to fire with no ammo
- `onHit`: Triggered when bullet hits surface

#### `HitscanWeapon` (Extends Weapon)
Location: `src/game/weapons/HitscanWeapon.ts`

Instant raycast-based weapons (pistols, rifles, etc.).

**How it Works:**
1. Calculates shot direction with spread applied
2. Performs Three.js raycast from camera position
3. Returns hit information (point, normal, distance)
4. Triggers callbacks for effects

**Key Features:**
- Random spread within cone angle
- Fire rate throttling
- Auto-reload when empty
- Hit detection against all scene meshes

#### `WeaponManager`
Location: `src/game/weapons/WeaponManager.ts`

Manages player's weapon inventory, firing, switching, and effects.

**Responsibilities:**
- Weapon switching (next/previous/direct)
- Fire handling (semi-auto and full-auto)
- Reload handling
- HitEffect integration
- Weapon update loop

**Usage:**
```typescript
const weaponManager = new WeaponManager(scene);
weaponManager.addWeapon(new Pistol());
weaponManager.addWeapon(new Rifle());

// In game loop
weaponManager.update(deltaTime, camera, scene);

// Fire weapon
weaponManager.fire(camera, scene);

// Switch weapons
weaponManager.switchToWeapon(1); // Switch to index 1
```

#### `HitEffect`
Location: `src/game/weapons/effects/HitEffect.ts`

Creates visual feedback for bullet impacts.

**Effects:**
- Bullet hole decals on surfaces
- Spark particles with physics
- Automatic cleanup (max 50 decals)

#### `WeaponFactory`
Location: `src/game/weapons/WeaponFactory.ts`

Factory for creating weapon instances.

**Methods:**
- `createWeapon(type)`: Create single weapon
- `createWeapons(types)`: Create multiple weapons
- `createDefaultLoadout()`: Create pistol + rifle

## Example Weapons

### Pistol
Location: `src/game/weapons/weapons/Pistol.ts`

**Stats:**
- Fire Rate: 300 RPM (5 shots/second)
- Damage: 25 (4 shots to kill)
- Range: 50 meters
- Spread: 2 degrees (accurate)
- Ammo: 12 rounds
- Reload: 1.5 seconds
- Mode: Semi-auto

### Rifle
Location: `src/game/weapons/weapons/Rifle.ts`

**Stats:**
- Fire Rate: 600 RPM (10 shots/second)
- Damage: 20 (5 shots to kill)
- Range: 100 meters
- Spread: 3 degrees (moderate)
- Ammo: 30 rounds
- Reload: 2.0 seconds
- Mode: Full-auto

## Adding a New Weapon

### Option 1: Extend HitscanWeapon (Recommended)
```typescript
// src/game/weapons/weapons/Shotgun.ts
import { HitscanWeapon } from '../HitscanWeapon';
import { FireMode } from '../Weapon';

export class Shotgun extends HitscanWeapon {
  constructor() {
    super({
      name: 'Shotgun',
      fireRate: 60,        // 1 shot per second
      damage: 15,          // Per pellet (7 pellets = 105 total)
      range: 20,           // 20 meters
      spread: 10,          // 10 degrees (wide spread)
      maxAmmo: 8,
      reloadTime: 3.0,
      fireMode: FireMode.SEMI_AUTO
    });
  }
}
```

### Option 2: Extend Weapon for Custom Behavior
```typescript
import * as THREE from 'three';
import { Weapon, WeaponConfig, FireMode } from '../Weapon';

export class ProjectileWeapon extends Weapon {
  constructor(config: WeaponConfig) {
    super(config);
  }

  fire(camera: THREE.Camera, scene: THREE.Scene, currentTime: number): boolean {
    if (!this.canFire(currentTime)) return false;

    // Custom projectile logic here
    this.spawnProjectile(camera.position, camera.getWorldDirection(new THREE.Vector3()));

    this.currentAmmo--;
    this.lastFireTime = currentTime;
    this.callbacks.onFire?.();
    return true;
  }

  private spawnProjectile(position: THREE.Vector3, direction: THREE.Vector3): void {
    // Implement projectile physics
  }
}
```

### Register in Factory
```typescript
// WeaponFactory.ts
export enum WeaponType {
  PISTOL = 'pistol',
  RIFLE = 'rifle',
  SHOTGUN = 'shotgun' // Add new type
}

static createWeapon(type: WeaponType): Weapon {
  switch (type) {
    case WeaponType.PISTOL:
      return new Pistol();
    case WeaponType.RIFLE:
      return new Rifle();
    case WeaponType.SHOTGUN:
      return new Shotgun(); // Add case
    default:
      throw new Error(`Unknown weapon type: ${type}`);
  }
}
```

## Fire Modes

### Semi-Auto
One shot per trigger pull. Requires releasing and pressing again.

**Implementation:** Fire triggered by `isMouseButtonJustPressed()`

### Full-Auto
Continuous fire while trigger held.

**Implementation:** Fire triggered by `isMouseButtonPressed()` + `WeaponManager.startFiring()`

### Burst (Future)
Fixed number of rounds per trigger pull (e.g., 3-round burst).

**Implementation:** Would require burst counter and delay between rounds in Weapon.update()

## Integration with Player

The weapon system integrates with the Player class:

**src/game/Player.ts:**
```typescript
private updateWeapons(deltaTime: number, scene: THREE.Scene): void {
  // Fire on click
  if (this.input.isMouseButtonJustPressed(0)) {
    this.weaponManager.fire(this.camera, scene);
  }

  // Hold for full-auto
  if (this.input.isMouseButtonPressed(0)) {
    this.weaponManager.startFiring();
  } else {
    this.weaponManager.stopFiring();
  }

  // Reload
  if (this.input.isKeyPressed('KeyR')) {
    this.weaponManager.reload();
  }

  // Weapon switching
  if (this.input.isKeyPressed('Digit1')) {
    this.weaponManager.switchToWeapon(0);
  }

  // Update
  this.weaponManager.update(deltaTime, this.camera, scene);
  this.input.clearMouseJustPressed();
}
```

## Performance Considerations

- **Raycasting:** Efficient Three.js raycaster with far plane culling
- **Decals:** Limited to 50 max (oldest removed first)
- **Particles:** Short-lived (0.3-0.5s), auto-cleanup
- **Fire Rate:** Throttled by timestamp comparison (no setTimeout/setInterval)

## Future Extensions

### Easy Additions:
- Sniper rifle (low fire rate, high damage, no spread)
- SMG (high fire rate, low damage, high spread)
- Burst rifle (3-round burst mode)
- Different ammo types

### Advanced Features:
- Weapon recoil/camera shake
- Muzzle flash effects
- Tracer rounds
- Sound effects (Web Audio API)
- Weapon models/animations
- Different damage per body part
- Penetration through thin walls

### Projectile Weapons:
Extend Weapon base class with physics-based projectiles:
- Rocket launchers
- Grenade launchers
- Bows/crossbows

## File Structure
```
src/game/weapons/
├── Weapon.ts              # Abstract base class
├── HitscanWeapon.ts       # Raycast weapon implementation
├── WeaponManager.ts       # Player weapon state
├── WeaponFactory.ts       # Weapon instantiation
├── weapons/
│   ├── Pistol.ts          # Semi-auto pistol
│   └── Rifle.ts           # Full-auto rifle
└── effects/
    └── HitEffect.ts       # Bullet impact visuals
```

## Controls

- **Left Click**: Fire weapon
- **Hold Left Click**: Continuous fire (full-auto weapons)
- **R**: Reload
- **1**: Switch to weapon slot 1 (Pistol)
- **2**: Switch to weapon slot 2 (Rifle)

## Console Output

Weapon actions log to console:
- "Pistol fired! Ammo: 11/12"
- "Rifle reloading..."
- "Pistol is empty! Press R to reload."
- "Switched to Assault Rifle"
