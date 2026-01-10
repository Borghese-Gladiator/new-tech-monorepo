import * as THREE from 'three';

export class ViewModelRenderer {
  private viewModelScene: THREE.Scene;
  private viewModelCamera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;

  constructor(renderer: THREE.WebGLRenderer) {
    this.renderer = renderer;

    // Disable auto clear so we can render multiple scenes
    this.renderer.autoClear = false;

    // Create separate scene for weapon
    this.viewModelScene = new THREE.Scene();

    // Create camera for weapon (lower FOV for less distortion)
    this.viewModelCamera = new THREE.PerspectiveCamera(
      60,  // FOV (less than main camera to reduce distortion)
      window.innerWidth / window.innerHeight,
      0.01,  // Very close near plane
      2.0    // Short far plane (only render weapon)
    );

    // Add camera to scene so weapons can be attached as children
    this.viewModelScene.add(this.viewModelCamera);

    // Handle window resize
    window.addEventListener('resize', () => {
      this.viewModelCamera.aspect = window.innerWidth / window.innerHeight;
      this.viewModelCamera.updateProjectionMatrix();
    });
  }

  /**
   * Add weapon model to view model scene (as child of camera)
   */
  addWeaponModel(model: THREE.Group): void {
    // Add weapon as child of camera so it moves with camera
    this.viewModelCamera.add(model);
  }

  /**
   * Remove weapon model from camera
   */
  removeWeaponModel(model: THREE.Group): void {
    this.viewModelCamera.remove(model);
  }

  /**
   * Update view model camera to match player camera
   */
  updateCamera(playerCamera: THREE.Camera): void {
    // Copy position and rotation from player camera
    this.viewModelCamera.position.copy(playerCamera.position);
    this.viewModelCamera.quaternion.copy(playerCamera.quaternion);

    // Update view model camera matrix
    this.viewModelCamera.updateMatrixWorld(true);
  }

  /**
   * Render the view model
   * Called after world rendering
   */
  render(): void {
    // Clear only depth buffer (keep color buffer from world render)
    this.renderer.clearDepth();

    // Render weapon on top of world
    this.renderer.render(this.viewModelScene, this.viewModelCamera);
  }

  /**
   * Get the view model scene
   */
  getScene(): THREE.Scene {
    return this.viewModelScene;
  }

  /**
   * Get the view model camera
   */
  getCamera(): THREE.PerspectiveCamera {
    return this.viewModelCamera;
  }
}
