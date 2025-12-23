# Weapon Visibility Fix

## Problem
Weapon models were not visible in the viewport after implementing the animation system.

## Root Cause
Weapons were being added to the view model scene as independent objects with positions in world space (0.3, -0.2, -0.5). However, the player camera was at the player's position (e.g., (0, 2, 0)), so the weapon was left behind at the origin while the player moved around.

**The issue:** Weapon position was absolute, not relative to the camera.

## Solution
Make weapons **children of the camera** so they automatically move and rotate with the camera.

### Changes Made

#### 1. ViewModelRenderer - Attach weapons to camera
**File:** `src/game/viewmodel/ViewModelRenderer.ts`

```typescript
constructor(renderer: THREE.WebGLRenderer) {
  // ... setup code ...

  // Add camera to scene so weapons can be attached as children
  this.viewModelScene.add(this.viewModelCamera);
}

addWeaponModel(model: THREE.Group): void {
  // Add weapon as child of camera so it moves with camera
  this.viewModelCamera.add(model);
}

removeWeaponModel(model: THREE.Group): void {
  this.viewModelCamera.remove(model);
}

updateCamera(playerCamera: THREE.Camera): void {
  this.viewModelCamera.position.copy(playerCamera.position);
  this.viewModelCamera.quaternion.copy(playerCamera.quaternion);
  // Update matrix so child transforms work correctly
  this.viewModelCamera.updateMatrixWorld(true);
}
```

#### 2. WeaponManager - Use ViewModelRenderer
**File:** `src/game/weapons/WeaponManager.ts`

Changed from passing `THREE.Scene` to passing `ViewModelRenderer`:

```typescript
// Before
private viewModelScene?: THREE.Scene;
setViewModelScene(scene: THREE.Scene): void {
  this.viewModelScene = scene;
}

// After
private viewModelRenderer?: ViewModelRenderer;
setViewModelRenderer(renderer: ViewModelRenderer): void {
  this.viewModelRenderer = renderer;
}
```

When adding weapons:
```typescript
// Before
if (this.viewModelScene) {
  this.viewModelScene.add(viewModel.getModel());
}

// After
if (this.viewModelRenderer) {
  this.viewModelRenderer.addWeaponModel(viewModel.getModel());
}
```

#### 3. Main.ts - Pass ViewModelRenderer
**File:** `src/main.ts`

```typescript
// Before
this.player.weaponManager.setViewModelScene(this.viewModelRenderer.getScene());

// After
this.player.weaponManager.setViewModelRenderer(this.viewModelRenderer);
```

## How It Works Now

### Parent-Child Hierarchy
```
ViewModelScene
  └─ ViewModelCamera (position: player position)
      └─ WeaponModel (position: (0.3, -0.2, -0.5) relative to camera)
```

### Position Calculation
With the weapon as a child of the camera:
- **Weapon local position:** (0.3, -0.2, -0.5)
- **Camera world position:** (0, 2, 5) [example player position]
- **Weapon world position:** (0.3, 1.8, 4.5) [automatically calculated]

When the camera moves/rotates, Three.js automatically transforms all children.

### Transform Chain
1. Player camera updates position/rotation
2. ViewModelRenderer copies to its camera
3. Camera's matrix updates with `updateMatrixWorld(true)`
4. Weapon (as child) inherits camera's transforms
5. Weapon appears at correct position **relative to view**

## Benefits of This Approach

1. **Automatic Following**
   - Weapon always moves with camera
   - No manual position updates needed
   - Rotation handled automatically

2. **Correct Relative Positioning**
   - (0.3, -0.2, -0.5) means:
     - 0.3 units right
     - 0.2 units down
     - 0.5 units forward
   - Relative to wherever the camera is looking

3. **Procedural Effects Work**
   - Sway/bob offsets still apply to model position
   - They're relative to the base (camera-relative) position

4. **Clean Architecture**
   - ViewModelRenderer encapsulates weapon attachment
   - WeaponManager doesn't need to know about parent-child relationships
   - Separation of concerns maintained

## Testing

After fix, you should see:
- ✅ Weapon model in bottom-right of viewport
- ✅ Weapon moves with camera (WASD movement)
- ✅ Weapon rotates with camera (mouse look)
- ✅ Weapon always in view regardless of player position

## Common Issues & Solutions

### Weapon appears at wrong position
**Check:** Weapon's local position should be relative to camera, not world.
- Right: `(0.3, -0.2, -0.5)` in camera space
- Wrong: `(0, 2, 5)` in world space

### Weapon doesn't rotate with camera
**Check:** Ensure `updateMatrixWorld(true)` is called after updating camera transform.

### Weapon visible but static
**Check:** Verify weapon is child of camera, not added directly to scene.

### Multiple weapons all visible
**Check:** Weapon visibility switching in WeaponManager (hide non-current weapons).

## Files Modified
1. `src/game/viewmodel/ViewModelRenderer.ts` - Attach weapons to camera
2. `src/game/weapons/WeaponManager.ts` - Use ViewModelRenderer API
3. `src/main.ts` - Pass ViewModelRenderer instead of scene

## Reference
Three.js parent-child transforms: https://threejs.org/docs/#manual/en/introduction/Matrix-transformations
