import * as THREE from 'three';
import { Weapon, WeaponConfig } from './Weapon';

export interface HitResult {
  hit: boolean;
  point?: THREE.Vector3;
  normal?: THREE.Vector3;
  distance?: number;
  object?: THREE.Object3D;
}

export class HitscanWeapon extends Weapon {
  private raycaster: THREE.Raycaster;

  constructor(config: WeaponConfig) {
    super(config);
    this.raycaster = new THREE.Raycaster();
    this.raycaster.far = config.range;
  }

  fire(camera: THREE.Camera, scene: THREE.Scene, currentTime: number): boolean {
    if (!this.canFire(currentTime)) {
      if (this.currentAmmo <= 0 && !this.isReloading) {
        this.callbacks.onEmpty?.();
      }
      return false;
    }

    // Consume ammo
    this.currentAmmo--;
    this.lastFireTime = currentTime;

    // Calculate shot direction with spread
    const direction = this.calculateShotDirection(camera);

    // Perform raycast
    const hitResult = this.performRaycast(camera.position, direction, scene);

    // Trigger callbacks
    this.callbacks.onFire?.();
    if (hitResult.hit && hitResult.point && hitResult.normal) {
      // Check if hit an enemy (traverse up parent chain to find enemy group)
      const enemyObject = this.findEnemyInParents(hitResult.object);
      if (enemyObject) {
        this.callbacks.onEnemyHit?.(enemyObject);
      }
      // Always create impact effect
      this.callbacks.onHit?.(hitResult.point, hitResult.normal);
    }

    // Auto-reload when empty
    if (this.currentAmmo === 0) {
      this.reload();
    }

    return true;
  }

  /**
   * Calculate shot direction with spread applied
   */
  private calculateShotDirection(camera: THREE.Camera): THREE.Vector3 {
    const direction = new THREE.Vector3();
    camera.getWorldDirection(direction);

    // Apply spread (convert degrees to radians)
    if (this.config.spread > 0) {
      const spreadRad = (this.config.spread * Math.PI) / 180;

      // Random offset within cone
      const spreadX = (Math.random() - 0.5) * spreadRad;
      const spreadY = (Math.random() - 0.5) * spreadRad;

      // Get camera's right and up vectors
      const right = new THREE.Vector3();
      const up = new THREE.Vector3();

      if (camera instanceof THREE.PerspectiveCamera) {
        right.setFromMatrixColumn(camera.matrixWorld, 0);
        up.setFromMatrixColumn(camera.matrixWorld, 1);
      }

      // Apply spread offset
      direction.add(right.multiplyScalar(spreadX));
      direction.add(up.multiplyScalar(spreadY));
      direction.normalize();
    }

    return direction;
  }

  /**
   * Perform raycast and return hit information
   */
  private performRaycast(
    origin: THREE.Vector3,
    direction: THREE.Vector3,
    scene: THREE.Scene
  ): HitResult {
    this.raycaster.set(origin, direction);

    // Raycast against all meshes in scene
    const intersects = this.raycaster.intersectObjects(scene.children, true);

    if (intersects.length > 0) {
      const hit = intersects[0];
      return {
        hit: true,
        point: hit.point.clone(),
        normal: hit.face ? hit.face.normal.clone() : new THREE.Vector3(0, 1, 0),
        distance: hit.distance,
        object: hit.object
      };
    }

    return { hit: false };
  }

  /**
   * Find enemy object by traversing up the parent chain
   */
  private findEnemyInParents(object?: THREE.Object3D): THREE.Object3D | null {
    let current: THREE.Object3D | null = object || null;
    while (current) {
      if (current.userData.enemy) {
        return current;
      }
      current = current.parent;
    }
    return null;
  }

  /**
   * Get the current shot direction for debugging/visualization
   */
  getShotDirection(camera: THREE.Camera): THREE.Vector3 {
    return this.calculateShotDirection(camera);
  }
}
