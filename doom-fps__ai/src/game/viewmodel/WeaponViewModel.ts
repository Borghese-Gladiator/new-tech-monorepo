import * as THREE from 'three';

export class WeaponViewModel {
  model: THREE.Group;
  private basePosition: THREE.Vector3;
  private baseRotation: THREE.Euler;
  private muzzleFlash?: THREE.PointLight;
  private muzzleFlashMesh?: THREE.Mesh;

  // Procedural animation offsets
  private swayOffset = new THREE.Vector3();
  private bobOffset = new THREE.Vector3();
  private recoilOffset = new THREE.Vector3();

  // Sway parameters - heavier DOOM feel
  private readonly SWAY_AMOUNT = 0.025;
  private readonly SWAY_SMOOTH = 8;
  private targetSwayOffset = new THREE.Vector3();

  // Bob parameters - heavier DOOM feel
  private readonly BOB_FREQUENCY = 1.8;
  private readonly BOB_HORIZONTAL = 0.04;
  private readonly BOB_VERTICAL = 0.05;
  private bobTime = 0;

  constructor(model: THREE.Group, position = new THREE.Vector3(0.3, -0.2, -0.5)) {
    this.model = model;
    this.basePosition = position.clone();
    this.baseRotation = new THREE.Euler(0, 0, 0);

    this.model.position.copy(this.basePosition);
    this.model.rotation.copy(this.baseRotation);

    this.createMuzzleFlash();
  }

  /**
   * Create muzzle flash effect - DOOM hellfire style
   */
  private createMuzzleFlash(): void {
    // Point light for hellfire illumination (green/red mix)
    this.muzzleFlash = new THREE.PointLight(0x44ff44, 0, 8);
    this.muzzleFlash.visible = false;
    this.model.add(this.muzzleFlash);

    // Visual flash sprite - hellfire green
    const flashGeometry = new THREE.PlaneGeometry(0.15, 0.15);
    const flashMaterial = new THREE.MeshBasicMaterial({
      color: 0x44ff44, // Hellfire green
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });

    this.muzzleFlashMesh = new THREE.Mesh(flashGeometry, flashMaterial);
    this.muzzleFlashMesh.visible = false;
    this.model.add(this.muzzleFlashMesh);
  }

  /**
   * Position muzzle flash at weapon tip
   */
  setMuzzleFlashPosition(position: THREE.Vector3): void {
    if (this.muzzleFlash) {
      this.muzzleFlash.position.copy(position);
    }
    if (this.muzzleFlashMesh) {
      this.muzzleFlashMesh.position.copy(position);
    }
  }

  /**
   * Show muzzle flash
   */
  showMuzzleFlash(): void {
    if (this.muzzleFlash && this.muzzleFlashMesh) {
      this.muzzleFlash.visible = true;
      this.muzzleFlash.intensity = 2;
      this.muzzleFlashMesh.visible = true;
      (this.muzzleFlashMesh.material as THREE.MeshBasicMaterial).opacity = 1;

      // Auto-hide after short duration
      setTimeout(() => {
        this.hideMuzzleFlash();
      }, 50);
    }
  }

  /**
   * Hide muzzle flash
   */
  hideMuzzleFlash(): void {
    if (this.muzzleFlash && this.muzzleFlashMesh) {
      this.muzzleFlash.visible = false;
      this.muzzleFlashMesh.visible = false;
    }
  }

  /**
   * Update weapon sway based on mouse movement
   */
  updateSway(mouseDeltaX: number, mouseDeltaY: number, deltaTime: number): void {
    // Calculate target sway based on mouse movement
    this.targetSwayOffset.x = -mouseDeltaX * this.SWAY_AMOUNT;
    this.targetSwayOffset.y = mouseDeltaY * this.SWAY_AMOUNT;

    // Smoothly interpolate to target sway
    const lerpFactor = 1 - Math.exp(-this.SWAY_SMOOTH * deltaTime);
    this.swayOffset.lerp(this.targetSwayOffset, lerpFactor);
  }

  /**
   * Update weapon bob based on movement
   */
  updateBob(isMoving: boolean, deltaTime: number): void {
    if (isMoving) {
      this.bobTime += deltaTime * this.BOB_FREQUENCY;

      // Horizontal bob (side to side)
      this.bobOffset.x = Math.sin(this.bobTime * Math.PI) * this.BOB_HORIZONTAL;

      // Vertical bob (up and down at 2x frequency)
      this.bobOffset.y = Math.abs(Math.sin(this.bobTime * Math.PI * 2)) * this.BOB_VERTICAL;
    } else {
      // Smoothly return to center when not moving
      this.bobOffset.lerp(new THREE.Vector3(), deltaTime * 5);
      this.bobTime = 0;
    }
  }

  /**
   * Apply animation offsets to weapon
   */
  applyAnimation(animationOffset: { position: THREE.Vector3; rotation: THREE.Euler }): void {
    // Combine all offsets
    const finalPosition = this.basePosition.clone()
      .add(this.swayOffset)
      .add(this.bobOffset)
      .add(animationOffset.position);

    const finalRotation = this.baseRotation.clone();
    finalRotation.x += animationOffset.rotation.x;
    finalRotation.y += animationOffset.rotation.y;
    finalRotation.z += animationOffset.rotation.z;

    this.model.position.copy(finalPosition);
    this.model.rotation.copy(finalRotation);
  }

  /**
   * Set base position
   */
  setBasePosition(position: THREE.Vector3): void {
    this.basePosition.copy(position);
  }

  /**
   * Set base rotation
   */
  setBaseRotation(rotation: THREE.Euler): void {
    this.baseRotation.copy(rotation);
  }

  /**
   * Get the weapon model
   */
  getModel(): THREE.Group {
    return this.model;
  }

  /**
   * Dispose of resources
   */
  dispose(): void {
    // Recursively dispose of geometries and materials
    this.model.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose();
        if (Array.isArray(obj.material)) {
          obj.material.forEach(mat => mat.dispose());
        } else {
          obj.material.dispose();
        }
      }
    });
  }
}
