# Weapon System Design

## Brief
Design a modular, extensible weapon system with base abstractions and hitscan implementation. Focus on clean separation of concerns, easy extensibility, and performance.

## Architecture

### Core Abstractions
1. **Weapon (abstract base)** - Defines weapon interface and shared behavior
2. **HitscanWeapon (extends Weapon)** - Instant raycast-based weapons (pistol, rifle)
3. **WeaponManager** - Handles weapon switching, ammo, current weapon state
4. **HitEffect** - Visual feedback for bullet impacts (decals, particles)

### Weapon Properties
- Fire rate (rounds per minute)
- Damage per shot
- Accuracy/spread (cone angle)
- Ammo capacity
- Range
- Recoil pattern

### Design Patterns
- **Strategy Pattern**: Different fire modes (semi-auto, burst, full-auto)
- **Factory Pattern**: Easy weapon instantiation
- **Observer Pattern**: Events for animations/audio (fire, reload, empty)

## File Structure
```
src/
├── game/
│   ├── weapons/
│   │   ├── Weapon.ts              # Abstract base class
│   │   ├── HitscanWeapon.ts       # Raycast weapon implementation
│   │   ├── WeaponManager.ts       # Current weapon, switching, ammo
│   │   ├── WeaponFactory.ts       # Create weapon instances
│   │   ├── weapons/
│   │   │   ├── Pistol.ts          # Example hitscan weapon
│   │   │   └── Rifle.ts           # Example hitscan weapon
│   │   └── effects/
│   │       └── HitEffect.ts       # Bullet impact visuals
│   └── ...
```

## Implementation Details

### Weapon Interface
```typescript
abstract class Weapon {
  - fireRate: number (RPM)
  - damage: number
  - range: number
  - currentAmmo: number
  - maxAmmo: number

  + fire(camera, scene): boolean
  + reload(): void
  + update(deltaTime): void
  + canFire(): boolean
}
```

### HitscanWeapon
- Uses Three.js Raycaster for instant hit detection
- Spread calculation using cone angle
- Fire rate throttling with cooldown timer
- Hit detection against collision geometry
- Event emission for effects

### Extensibility
Adding a new weapon requires:
1. Extend Weapon or HitscanWeapon
2. Override fire behavior if needed
3. Register in WeaponFactory
4. Done - no core system changes

## Change List
1. Create abstract Weapon base class
2. Implement HitscanWeapon with raycast logic
3. Create WeaponManager for player weapon state
4. Implement HitEffect for visual feedback
5. Create example weapons (Pistol, Rifle)
6. Create WeaponFactory for easy instantiation
7. Integrate with Player class
8. Update World to handle hit detection

## Testing

### Manual Tests
- [ ] Fire pistol - single shots with cooldown
- [ ] Fire rifle - automatic fire when holding mouse
- [ ] Spread increases at range
- [ ] Fire rate limits correctly (no spam)
- [ ] Ammo decreases per shot
- [ ] Can't fire with 0 ammo
- [ ] Reload refills ammo
- [ ] Hit effects appear on walls
- [ ] Damage calculation works
- [ ] Multiple weapons switch correctly
