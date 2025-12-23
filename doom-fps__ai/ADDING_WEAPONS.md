# Quick Guide: Adding New Weapons

## 1. Create Your Weapon Class

Create a new file in `src/game/weapons/weapons/YourWeapon.ts`:

```typescript
import { HitscanWeapon } from '../HitscanWeapon';
import { FireMode } from '../Weapon';

export class YourWeapon extends HitscanWeapon {
  constructor() {
    super({
      name: 'Your Weapon Name',
      fireRate: 300,           // Rounds per minute (RPM)
      damage: 25,              // Damage per shot
      range: 50,               // Effective range in meters
      spread: 2,               // Accuracy cone in degrees (0 = perfect)
      maxAmmo: 12,             // Magazine size
      reloadTime: 1.5,         // Reload time in seconds
      fireMode: FireMode.SEMI_AUTO  // or FULL_AUTO, BURST
    });
  }
}
```

## 2. Register in Factory

Edit `src/game/weapons/WeaponFactory.ts`:

```typescript
// Add to enum
export enum WeaponType {
  PISTOL = 'pistol',
  RIFLE = 'rifle',
  YOUR_WEAPON = 'your-weapon'  // Add this
}

// Add to createWeapon switch
static createWeapon(type: WeaponType): Weapon {
  switch (type) {
    case WeaponType.PISTOL:
      return new Pistol();
    case WeaponType.RIFLE:
      return new Rifle();
    case WeaponType.YOUR_WEAPON:
      return new YourWeapon();  // Add this
    // ...
  }
}
```

## 3. Add to Game (Optional)

Edit `src/main.ts` to include in default loadout:

```typescript
import { YourWeapon } from './game/weapons/weapons/YourWeapon';

// In Game constructor
this.player.weaponManager.addWeapon(new YourWeapon());
```

## Done!

Your weapon is now:
- ✅ Fully functional
- ✅ Automatically fire rate limited
- ✅ Auto-reloads when empty
- ✅ Has bullet impact effects
- ✅ Logs to console

## Fire Mode Reference

### Semi-Auto
```typescript
fireMode: FireMode.SEMI_AUTO
```
One shot per click. Must release and click again.

### Full-Auto
```typescript
fireMode: FireMode.FULL_AUTO
```
Continuous fire while mouse button held.

### Burst (Future)
```typescript
fireMode: FireMode.BURST
```
3-round burst per click (not yet implemented).

## Weapon Stat Examples

### Sniper Rifle
```typescript
fireRate: 40,      // Slow (0.67 shots/sec)
damage: 100,       // One-shot kill
range: 500,        // Long range
spread: 0,         // Perfect accuracy
maxAmmo: 5,
reloadTime: 3.0,
fireMode: FireMode.SEMI_AUTO
```

### SMG
```typescript
fireRate: 900,     // Fast (15 shots/sec)
damage: 15,        // Low damage
range: 30,         // Short range
spread: 5,         // High spread
maxAmmo: 40,
reloadTime: 1.8,
fireMode: FireMode.FULL_AUTO
```

### Shotgun
```typescript
fireRate: 60,      // Very slow (1 shot/sec)
damage: 20,        // Per pellet (fire multiple rays)
range: 15,         // Very short
spread: 12,        // Very wide
maxAmmo: 8,
reloadTime: 2.5,
fireMode: FireMode.SEMI_AUTO
```

## Advanced: Custom Fire Behavior

For non-hitscan weapons (rockets, grenades), extend `Weapon` directly:

```typescript
import * as THREE from 'three';
import { Weapon, WeaponConfig } from '../Weapon';

export class RocketLauncher extends Weapon {
  constructor() {
    super({
      name: 'Rocket Launcher',
      fireRate: 30,
      damage: 100,
      range: 200,
      spread: 0,
      maxAmmo: 4,
      reloadTime: 3.0,
      fireMode: FireMode.SEMI_AUTO
    });
  }

  fire(camera: THREE.Camera, scene: THREE.Scene, currentTime: number): boolean {
    if (!this.canFire(currentTime)) return false;

    // Spawn rocket projectile
    const direction = new THREE.Vector3();
    camera.getWorldDirection(direction);
    this.spawnRocket(camera.position, direction, scene);

    this.currentAmmo--;
    this.lastFireTime = currentTime;
    this.callbacks.onFire?.();
    return true;
  }

  private spawnRocket(pos: THREE.Vector3, dir: THREE.Vector3, scene: THREE.Scene): void {
    // Create rocket mesh
    // Add physics
    // Handle collision/explosion
  }
}
```

## Need Help?

See `WEAPON_SYSTEM.md` for full documentation.
