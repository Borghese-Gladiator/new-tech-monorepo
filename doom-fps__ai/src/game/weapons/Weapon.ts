import * as THREE from 'three';

export enum FireMode {
  SEMI_AUTO = 'semi-auto',    // One shot per click
  BURST = 'burst',             // 3-round burst
  FULL_AUTO = 'full-auto'      // Continuous fire while held
}

export interface RecoilConfig {
  vertical: number;        // Upward kick in degrees
  horizontal: number;      // Random horizontal deviation in degrees
  recovery: number;        // How fast recoil recovers (degrees per second)
  pattern?: 'snappy' | 'climbing';  // Recoil behavior pattern
}

export interface WeaponConfig {
  name: string;
  fireRate: number;        // Rounds per minute
  damage: number;          // Damage per shot
  range: number;           // Maximum effective range
  spread: number;          // Accuracy cone in degrees (0 = perfect accuracy)
  maxAmmo: number;         // Magazine capacity
  reloadTime: number;      // Time to reload in seconds
  fireMode: FireMode;
  recoil: RecoilConfig;    // Recoil behavior
}

export interface WeaponEventCallbacks {
  onFire?: () => void;
  onReload?: () => void;
  onEmpty?: () => void;
  onHit?: (point: THREE.Vector3, normal: THREE.Vector3) => void;
  onEnemyHit?: (object: THREE.Object3D) => void;
}

export abstract class Weapon {
  protected config: WeaponConfig;
  protected currentAmmo: number;
  protected lastFireTime = 0;
  protected isReloading = false;
  protected reloadStartTime = 0;
  protected callbacks: WeaponEventCallbacks = {};

  constructor(config: WeaponConfig) {
    this.config = config;
    this.currentAmmo = config.maxAmmo;
  }

  /**
   * Attempt to fire the weapon
   * @returns true if weapon fired successfully
   */
  abstract fire(camera: THREE.Camera, scene: THREE.Scene, currentTime: number): boolean;

  /**
   * Update weapon state (reloading, etc.)
   */
  update(deltaTime: number, currentTime: number): void {
    if (this.isReloading) {
      if (currentTime - this.reloadStartTime >= this.config.reloadTime * 1000) {
        this.currentAmmo = this.config.maxAmmo;
        this.isReloading = false;
      }
    }
  }

  /**
   * Start reload
   */
  reload(): boolean {
    if (this.isReloading || this.currentAmmo === this.config.maxAmmo) {
      return false;
    }

    this.isReloading = true;
    this.reloadStartTime = performance.now();
    this.callbacks.onReload?.();
    return true;
  }

  /**
   * Check if weapon can fire right now
   */
  canFire(currentTime: number): boolean {
    if (this.isReloading) return false;
    if (this.currentAmmo <= 0) return false;

    // Check fire rate cooldown
    const fireInterval = (60 / this.config.fireRate) * 1000; // Convert RPM to ms
    return currentTime - this.lastFireTime >= fireInterval;
  }

  /**
   * Register event callbacks
   */
  setCallbacks(callbacks: WeaponEventCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  // Getters
  getName(): string {
    return this.config.name;
  }

  getCurrentAmmo(): number {
    return this.currentAmmo;
  }

  getMaxAmmo(): number {
    return this.config.maxAmmo;
  }

  getIsReloading(): boolean {
    return this.isReloading;
  }

  getFireMode(): FireMode {
    return this.config.fireMode;
  }

  getDamage(): number {
    return this.config.damage;
  }

  getRange(): number {
    return this.config.range;
  }

  getReloadProgress(currentTime: number): number {
    if (!this.isReloading) return 1;
    return Math.min(1, (currentTime - this.reloadStartTime) / (this.config.reloadTime * 1000));
  }

  getReloadTime(): number {
    return this.config.reloadTime;
  }

  getRecoilConfig(): RecoilConfig {
    return this.config.recoil;
  }
}
