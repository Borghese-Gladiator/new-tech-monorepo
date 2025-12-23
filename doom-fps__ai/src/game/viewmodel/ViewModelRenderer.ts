import * as THREE from 'three';

export class ViewModelRenderer {
  private viewModelScene: THREE.Scene;
  private viewModelCamera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;

  constructor(renderer: THREE.WebGLRenderer) {
    this.renderer = renderer;

    // Create separate scene for weapon
    this.viewModelScene = new THREE.Scene();

    // Create camera for weapon (lower FOV for less distortion)
    this.viewModelCamera = new THREE.PerspectiveCamera(
      60,  // FOV (less than main camera to reduce distortion)
      window.innerWidth / window.innerHeight,
      0.01,  // Very close near plane
      2.0    // Short far plane (only render weapon)
    );

    // Handle window resize
    window.addEventListener('resize', () => {
      this.viewModelCamera.aspect = window.innerWidth / window.innerHeight;
      this.viewModelCamera.updateProjectionMatrix();
    });
  }

  /**
   * Add weapon model to view model scene
   */
  addWeaponModel(model: THREE.Group): void {
    this.viewModelScene.add(model);
  }

  /**
   * Remove weapon model from view model scene
   */
  removeWeaponModel(model: THREE.Group): void {
    this.viewModelScene.remove(model);
  }

  /**
   * Update view model camera to match player camera
   */
  updateCamera(playerCamera: THREE.Camera): void {
    // Copy position and rotation from player camera
    this.viewModelCamera.position.copy(playerCamera.position);
    this.viewModelCamera.quaternion.copy(playerCamera.quaternion);
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
