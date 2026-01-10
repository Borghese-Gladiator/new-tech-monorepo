# DOOM-Style Arcade Visual Overhaul Plan

## Brief
Transform the current Three.js FPS game from a clean, modern aesthetic into a classic DOOM-style arcade experience with hellish environments, demonic enemies, retro HUD elements, and visceral combat feedback.

## Change List

### 1. World & Environment (`src/game/World.ts`)
- [ ] **Sky/Background**: Change from sky blue (0x87ceeb) to hellish dark red (0x1a0000)
- [ ] **Fog**: Darken fog color to match hellscape, reduce visibility for claustrophobic feel
- [ ] **Lighting**:
  - Change ambient light to dim red/orange tint
  - Add flickering point lights for hellfire torches effect
  - Darken overall scene significantly
- [ ] **Ground**: Replace green (0x3a8c3a) with dark blood-red stone texture (0x2a0a0a)
- [ ] **Walls**: Replace brown with dark metallic/demonic colors (0x1a1a1a, 0x2a1515)
- [ ] **Add Hell Props**: Create demonic pillars, skull decorations, lava pools (emissive materials)

### 2. Enemy Visuals (`src/game/enemies/Enemy.ts`)
- [ ] **Replace Box Geometry**: Create demon-like shapes using combined geometries:
  - Horned head (sphere + cone horns)
  - Muscular torso (box/cylinder)
  - Clawed arms
- [ ] **Color Palette**: Dark red/purple body (0x661111) with glowing eyes (0xff0000 emissive)
- [ ] **Hit Feedback**: Change white flash to blood-red burst with brief emissive glow
- [ ] **Death Effect**: Add dissolve/explosion effect when killed
- [ ] **State Visuals**: Subtle visual changes between IDLE/CHASE/ATTACK states

### 3. HUD Overhaul (`src/ui/HUD.ts`)
- [ ] **Health Bar**:
  - Replace green fill with blood-red gradient
  - Add skull icon beside health
  - Use pixelated/retro font styling
  - Add "pulsing" effect when low health
- [ ] **Ammo Counter**:
  - Style with demonic red text
  - Add bullet/shell icon
- [ ] **Crosshair**:
  - Replace dot with aggressive cross or demonic symbol
  - Add red tint
- [ ] **Wave Display**:
  - Change to "DEMON WAVE X"
  - Blood-red color with heavy shadow
- [ ] **Death Screen**:
  - Change "YOU DIED" to "SLAUGHTERED" or "RIPPED APART"
  - Darker red overlay with blood drip effect
- [ ] **Add DOOM Face**: Optional - add player face icon that reacts to health

### 4. Weapon Visuals (`src/game/viewmodel/models/WeaponModelFactory.ts`, `src/game/viewmodel/WeaponViewModel.ts`)
- [ ] **Pistol Redesign**:
  - Bulkier, more aggressive shape
  - Add glowing demonic runes (emissive material accents)
  - Darker metals with red/orange highlights
- [ ] **Rifle Redesign**:
  - Transform into plasma/demonic rifle aesthetic
  - Add glowing barrel element
  - More angular, aggressive silhouette
- [ ] **Muzzle Flash**: Change orange/yellow to hellfire green (0x44ff44) or demonic purple (0xff44ff)
- [ ] **Increase Bob/Sway**: Make weapon movement feel heavier and more impactful
- [ ] **Add Idle Animation**: Subtle breathing/pulsing glow on weapons

### 5. Combat Effects (`src/game/weapons/effects/HitEffect.ts`, `src/game/DamageFeedback.ts`)
- [ ] **Bullet Holes**: Darken decals, add slight red tint for blood splatter look
- [ ] **Spark Particles**:
  - Change to hellfire colors (green/purple or blood red)
  - Increase particle count and spread
  - Longer trails
- [ ] **Damage Feedback**:
  - Intensify red flash (darker red: 0x440000, higher opacity: 0.5)
  - Increase camera shake intensity (0.15 vs current 0.05)
  - Add screen vignette darkening on damage
- [ ] **Enemy Hit Sparks**: Add blood particle burst when hitting enemies

### 6. CSS & Global Styling (`src/style.css`)
- [ ] **Background**: Change from pure black to very dark red (#0a0000)
- [ ] **Font**: Add retro/aggressive font import (or use system fonts that feel retro)
- [ ] **Crosshair CSS**: Update to match new demonic design
- [ ] **Add Scanline Effect**: Optional subtle CRT scanline overlay for retro feel
- [ ] **Add Vignette**: Permanent subtle edge darkening

### 7. New Visual Systems (New Files)
- [ ] **Create `src/game/effects/BloodParticles.ts`**: Reusable blood spray system for enemy hits
- [ ] **Create `src/game/effects/HellAmbience.ts`**: Flickering lights, ambient particle effects
- [ ] **Update `src/game/enemies/WaveSpawner.ts`**: Add demonic portal visual when spawning enemies

## Testing

### Visual Verification
- [ ] Environment looks like a hellscape (dark reds, no bright colors)
- [ ] Enemies are visually distinct and demonic
- [ ] Weapons have aggressive, hellish appearance
- [ ] HUD is readable but styled retro/demonic
- [ ] Combat feels visceral with strong feedback
- [ ] Performance remains smooth (target 60fps)

### Manual Test Scripts

**Test 1: Environment Check**
1. Launch game
2. Verify sky is dark red, not blue
3. Verify ground is dark/bloody, not green
4. Verify lighting has red/orange tint
5. Verify fog creates oppressive atmosphere

**Test 2: Enemy Visuals**
1. Wait for enemies to spawn
2. Verify enemies have demonic appearance (horns, claws, etc.)
3. Shoot enemy - verify blood-red hit effect (not white)
4. Kill enemy - verify death effect plays

**Test 3: HUD Check**
1. Verify health bar is red-themed
2. Verify ammo counter has demonic styling
3. Take damage - verify health bar updates with correct colors
4. Die - verify death screen shows new text and styling

**Test 4: Weapon Visuals**
1. Verify pistol has new demonic design
2. Verify rifle has new demonic design
3. Fire weapon - verify hellfire muzzle flash (green/purple)
4. Walk around - verify weapon bob feels heavier

**Test 5: Combat Feedback**
1. Take damage from enemy
2. Verify screen flash is darker/more intense red
3. Verify camera shake is more pronounced
4. Shoot walls - verify spark effects are hellfire colored
5. Shoot enemies - verify blood particle effects

## Implementation Order (Recommended)

1. **World.ts** - Environment sets the tone for everything else
2. **Enemy.ts** - Core visual element players interact with
3. **HUD.ts** - Player-facing UI needs to match theme
4. **WeaponModelFactory.ts** - Weapons are always visible
5. **HitEffect.ts / DamageFeedback.ts** - Combat feedback
6. **style.css** - Final polish
7. **New effect systems** - Optional enhancements

## Color Palette Reference

| Element | Current | DOOM Style |
|---------|---------|------------|
| Sky | 0x87ceeb (blue) | 0x1a0000 (dark red) |
| Ground | 0x3a8c3a (green) | 0x2a0a0a (blood stone) |
| Walls | 0x8b4513 (brown) | 0x1a1a1a (dark metal) |
| Enemy Body | 0xff4444 (red) | 0x661111 (dark demon red) |
| Enemy Eyes | - | 0xff0000 (emissive red) |
| Muzzle Flash | 0xffaa00 (orange) | 0x44ff44 (hellfire green) |
| Health Bar | 0x00ff00 (green) | 0xaa0000 (blood red) |
| Damage Flash | 0xff0000 | 0x440000 (darker) |
| Sparks | 0xffaa00 (orange) | 0x44ff44 (hellfire) |
