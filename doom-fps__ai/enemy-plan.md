# Simple Enemy System

## Brief
Implement a basic enemy AI system with spawning, health, simple movement toward player, and a state machine (idle → chase → attack).

## Architecture

### Core Components
1. **Enemy** - Main enemy class with health, state, and behavior
2. **EnemyState** - Enum for idle/chase/attack states
3. **EnemyManager** - Spawns and updates all enemies
4. **Simple 3D Model** - Box geometry with color

### State Machine
```
┌──────┐
│ Idle │ (no player in range)
└───┬──┘
    │ (player detected)
    ↓
┌───────┐
│ Chase │ (move toward player)
└───┬───┘
    │ (within attack range)
    ↓
┌────────┐
│ Attack │ (deal damage)
└────────┘
```

### Behavior
- **Idle**: Stand still, check for player in detection range (15m)
- **Chase**: Move toward player at constant speed (3 m/s)
- **Attack**: Stop moving, attack every 1 second

### Health System
- Start with 100 HP
- Take damage from weapon hits
- Die at 0 HP (removed from scene)
- Visual feedback (flash red on hit)

## File Structure
```
src/game/enemies/
├── Enemy.ts           # Enemy class with state machine
├── EnemyManager.ts    # Spawns and updates enemies
└── EnemyModel.ts      # 3D model creation
```

## Implementation Details

### Enemy Class
```typescript
class Enemy {
  - health: number (100)
  - state: EnemyState
  - position: Vector3
  - model: Mesh (box)
  - detectionRange: 15
  - attackRange: 2
  - moveSpeed: 3

  + update(deltaTime, playerPos)
  + takeDamage(amount)
  + isDead(): boolean
}
```

### EnemyManager
```typescript
class EnemyManager {
  - enemies: Enemy[]
  - scene: Scene

  + spawnEnemy(position)
  + update(deltaTime, playerPos)
  + checkHit(rayOrigin, rayDir): Enemy | null
  + removeDeadEnemies()
}
```

## Integration with Weapon System

Update HitscanWeapon to check enemy hits:
1. Perform raycast
2. Check if hit object is enemy
3. Apply damage to enemy

## Change List
1. Create EnemyState enum
2. Create Enemy class with state machine
3. Create EnemyModel helper
4. Create EnemyManager
5. Integrate with WeaponManager for damage
6. Add enemy spawning in World
7. Update Player to pass position to enemy updates

## Testing

### Manual Tests
- [ ] Enemy spawns in world
- [ ] Enemy idle when player far away
- [ ] Enemy chases when player approaches
- [ ] Enemy follows player smoothly
- [ ] Enemy attacks when in range
- [ ] Enemy takes damage from shots
- [ ] Enemy flashes red when hit
- [ ] Enemy dies and disappears at 0 HP
- [ ] Multiple enemies work independently

## Technical Specs

### Enemy Stats
- Health: 100 HP
- Move Speed: 3 m/s
- Detection Range: 15 meters
- Attack Range: 2 meters
- Attack Damage: 10 HP
- Attack Cooldown: 1 second

### Model
- Box geometry: 0.6 x 1.8 x 0.6 (human-sized)
- Base color: Red (0xff4444)
- Hit flash: White
- Position: Y offset by 0.9 (half height)
