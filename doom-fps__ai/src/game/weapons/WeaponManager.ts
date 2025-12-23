import * as THREE from 'three';
import { Weapon, FireMode } from './Weapon';
import { HitEffect } from './effects/HitEffect';
import { WeaponViewModel } from '../viewmodel/WeaponViewModel';
import { WeaponAnimator } from '../viewmodel/WeaponAnimator';
import { WeaponModelFactory } from '../viewmodel/models/WeaponModelFactory';
import { WeaponType } from './WeaponFactory';

interface WeaponEntry {
  weapon: Weapon;
  viewModel: WeaponViewModel;
  animator: WeaponAnimator;
  weaponType: WeaponType;
}

export class WeaponManager {
  private weaponEntries: WeaponEntry[] = [];
  private currentWeaponIndex = 0;
  private hitEffect: HitEffect;
  private isFiring = false;
  private viewModelScene?: THREE.Scene;

  constructor(scene: THREE.Scene) {
    this.hitEffect = new HitEffect(scene);
  }

  /**
   * Set the view model scene (for rendering weapons)
   */
  setViewModelScene(scene: THREE.Scene): void {
    this.viewModelScene = scene;
  }

  /**
   * Add a weapon to the inventory
   */
  addWeapon(weapon: Weapon, weaponType: WeaponType): void {
    // Create view model and animator
    const modelConfig = WeaponModelFactory.createModel(weaponType);
    const viewModel = new WeaponViewModel(modelConfig.model);
    viewModel.setMuzzleFlashPosition(modelConfig.muzzlePosition);

    const animator = new WeaponAnimator(weapon.getReloadTime());

    // Add to view model scene if available
    if (this.viewModelScene) {
      this.viewModelScene.add(viewModel.getModel());
      // Hide initially (show only current weapon)
      if (this.weaponEntries.length > 0) {
        viewModel.getModel().visible = false;
      }
    }

    // Setup weapon callbacks
    weapon.setCallbacks({
      onFire: () => {
        console.log(`${weapon.getName()} fired! Ammo: ${weapon.getCurrentAmmo()}/${weapon.getMaxAmmo()}`);
        animator.playFire();
        viewModel.showMuzzleFlash();
      },
      onReload: () => {
        console.log(`${weapon.getName()} reloading...`);
        animator.playReload();
      },
      onEmpty: () => {
        console.log(`${weapon.getName()} is empty! Press R to reload.`);
      },
      onHit: (point, normal) => {
        this.hitEffect.createImpact(point, normal);
      }
    });

    this.weaponEntries.push({ weapon, viewModel, animator, weaponType });
  }

  /**
   * Switch to next weapon
   */
  nextWeapon(): void {
    if (this.weaponEntries.length <= 1) return;
    this.hideCurrentWeapon();
    this.currentWeaponIndex = (this.currentWeaponIndex + 1) % this.weaponEntries.length;
    this.showCurrentWeapon();
    console.log(`Switched to ${this.getCurrentWeapon()?.getName()}`);
  }

  /**
   * Switch to previous weapon
   */
  previousWeapon(): void {
    if (this.weaponEntries.length <= 1) return;
    this.hideCurrentWeapon();
    this.currentWeaponIndex = (this.currentWeaponIndex - 1 + this.weaponEntries.length) % this.weaponEntries.length;
    this.showCurrentWeapon();
    console.log(`Switched to ${this.getCurrentWeapon()?.getName()}`);
  }

  /**
   * Switch to specific weapon by index
   */
  switchToWeapon(index: number): void {
    if (index >= 0 && index < this.weaponEntries.length && index !== this.currentWeaponIndex) {
      this.hideCurrentWeapon();
      this.currentWeaponIndex = index;
      this.showCurrentWeapon();
      console.log(`Switched to ${this.getCurrentWeapon()?.getName()}`);
    }
  }

  /**
   * Hide current weapon model
   */
  private hideCurrentWeapon(): void {
    const entry = this.weaponEntries[this.currentWeaponIndex];
    if (entry) {
      entry.viewModel.getModel().visible = false;
    }
  }

  /**
   * Show current weapon model
   */
  private showCurrentWeapon(): void {
    const entry = this.weaponEntries[this.currentWeaponIndex];
    if (entry) {
      entry.viewModel.getModel().visible = true;
    }
  }

  /**
   * Get current weapon
   */
  getCurrentWeapon(): Weapon | null {
    const entry = this.weaponEntries[this.currentWeaponIndex];
    return entry ? entry.weapon : null;
  }

  /**
   * Get current weapon entry (with view model and animator)
   */
  getCurrentWeaponEntry(): WeaponEntry | null {
    return this.weaponEntries[this.currentWeaponIndex] || null;
  }

  /**
   * Attempt to fire current weapon
   */
  fire(camera: THREE.Camera, scene: THREE.Scene): boolean {
    const weapon = this.getCurrentWeapon();
    if (!weapon) return false;

    const currentTime = performance.now();
    const fired = weapon.fire(camera, scene, currentTime);

    return fired;
  }

  /**
   * Start firing (for full-auto weapons)
   */
  startFiring(): void {
    this.isFiring = true;
  }

  /**
   * Stop firing
   */
  stopFiring(): void {
    this.isFiring = false;
  }

  /**
   * Check if currently firing
   */
  getIsFiring(): boolean {
    return this.isFiring;
  }

  /**
   * Reload current weapon
   */
  reload(): boolean {
    const weapon = this.getCurrentWeapon();
    if (!weapon) return false;
    return weapon.reload();
  }

  /**
   * Update weapons (handles reloading, animation, procedural effects)
   */
  update(
    deltaTime: number,
    camera: THREE.Camera,
    scene: THREE.Scene,
    mouseDelta: { x: number; y: number },
    isMoving: boolean
  ): void {
    const currentTime = performance.now();
    const entry = this.getCurrentWeaponEntry();

    if (entry) {
      const { weapon, viewModel, animator } = entry;

      // Update weapon logic
      weapon.update(deltaTime, currentTime);

      // Handle full-auto firing
      if (this.isFiring && weapon.getFireMode() === FireMode.FULL_AUTO) {
        weapon.fire(camera, scene, currentTime);
      }

      // Update view model animator
      animator.update(deltaTime);

      // Update procedural effects (sway, bob)
      viewModel.updateSway(mouseDelta.x, mouseDelta.y, deltaTime);
      viewModel.updateBob(isMoving, deltaTime);

      // Apply animation to view model
      const animationFrame = animator.getCurrentFrame();
      viewModel.applyAnimation(animationFrame);
    }
  }

  /**
   * Get all weapons
   */
  getWeapons(): Weapon[] {
    return this.weaponEntries.map(entry => entry.weapon);
  }

  /**
   * Get current weapon index
   */
  getCurrentWeaponIndex(): number {
    return this.currentWeaponIndex;
  }

  /**
   * Clear all bullet holes
   */
  clearEffects(): void {
    this.hitEffect.clearDecals();
  }
}
