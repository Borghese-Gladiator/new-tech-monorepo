# Black Screen Bug Fix

## Problem
After implementing the animation system, the game showed a black screen with only the crosshair visible.

## Root Cause
The issue was caused by the renderer's `autoClear` property. When `autoClear` is enabled (default), Three.js automatically clears all buffers before each render call.

In a multi-pass rendering setup:
1. World.render() was called → cleared and rendered world
2. ViewModelRenderer.render() was called → **cleared again** (destroying world render) → rendered weapon

Result: Only the weapon scene was visible, but the weapon scene has no background, so it appeared black.

## Solution

### Step 1: Disable autoClear
In `ViewModelRenderer.ts` constructor:
```typescript
this.renderer.autoClear = false;
```

### Step 2: Manually clear in world render
In `World.ts` render method:
```typescript
render(camera: THREE.Camera): void {
  // Clear buffers manually (autoClear disabled for multi-pass rendering)
  this.renderer.clear(true, true, true);
  this.renderer.render(this.scene, camera);
}
```

### Step 3: Clear only depth in weapon render
In `ViewModelRenderer.ts` render method (unchanged):
```typescript
render(): void {
  // Clear only depth buffer (keep color buffer from world render)
  this.renderer.clearDepth();

  // Render weapon on top of world
  this.renderer.render(this.viewModelScene, this.viewModelCamera);
}
```

## How It Works Now

**Correct rendering order:**

1. **World.render()**
   - `renderer.clear(true, true, true)` → Clears color + depth + stencil
   - `renderer.render(worldScene, worldCamera)` → Renders world

2. **ViewModelRenderer.render()**
   - `renderer.clearDepth()` → Clears ONLY depth (keeps color/world)
   - `renderer.render(weaponScene, weaponCamera)` → Renders weapon on top

Result: World is visible with weapon rendered on top (no z-fighting).

## Why This Pattern?

### autoClear = false
Required for multi-pass rendering. Allows manual control over when buffers are cleared.

### Clear depth between passes
- Keeps the world's color data intact
- Clears depth so weapon renders in front
- Prevents weapon from being occluded by world geometry

### Clear all at start
- Ensures clean slate each frame
- Prevents artifacts from previous frames

## Testing

After fix, you should see:
- ✅ World geometry (ground, walls, platforms)
- ✅ Sky blue background
- ✅ Weapon model in bottom-right
- ✅ Crosshair overlay

## Common Pitfall

If you see black screen with weapons only:
- Check that `World.render()` calls `renderer.clear()` before rendering
- Check that `autoClear = false` is set

If you see z-fighting (weapon flickers through walls):
- Check that `ViewModelRenderer.render()` calls `renderer.clearDepth()`
- Verify near/far planes on weapon camera (0.01 / 2.0)

## Files Changed
1. `src/game/viewmodel/ViewModelRenderer.ts` - Added `autoClear = false`
2. `src/game/World.ts` - Added manual `clear()` call

## References
- Three.js docs: https://threejs.org/docs/#api/en/renderers/WebGLRenderer.autoClear
- Multi-pass rendering: https://threejs.org/examples/#webgl_depth_texture
