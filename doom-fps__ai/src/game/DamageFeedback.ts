import * as THREE from 'three';

export class DamageFeedback {
  private damageOverlay: HTMLDivElement;
  private shakeIntensity = 0;
  private shakeDecay = 5.0; // How fast shake fades

  constructor(container: HTMLElement) {
    // Create red damage overlay
    this.damageOverlay = document.createElement('div');
    this.damageOverlay.style.position = 'fixed';
    this.damageOverlay.style.top = '0';
    this.damageOverlay.style.left = '0';
    this.damageOverlay.style.width = '100%';
    this.damageOverlay.style.height = '100%';
    this.damageOverlay.style.backgroundColor = 'red';
    this.damageOverlay.style.opacity = '0';
    this.damageOverlay.style.pointerEvents = 'none';
    this.damageOverlay.style.transition = 'opacity 0.3s ease-out';
    this.damageOverlay.style.zIndex = '100';
    container.appendChild(this.damageOverlay);
  }

  /**
   * Flash red screen when taking damage
   */
  flashDamage(intensity: number = 0.3): void {
    this.damageOverlay.style.opacity = intensity.toString();

    // Fade out after a short delay
    setTimeout(() => {
      this.damageOverlay.style.opacity = '0';
    }, 50);
  }

  /**
   * Trigger camera shake
   */
  triggerShake(intensity: number = 0.05): void {
    this.shakeIntensity = intensity;
  }

  /**
   * Update shake effect and apply to camera
   */
  update(deltaTime: number, camera: THREE.Camera): void {
    if (this.shakeIntensity > 0.001) {
      // Random offset
      const offsetX = (Math.random() - 0.5) * this.shakeIntensity;
      const offsetY = (Math.random() - 0.5) * this.shakeIntensity;

      // Apply shake to camera rotation
      camera.rotation.z = offsetX;
      camera.position.x += offsetX * 0.1;
      camera.position.y += offsetY * 0.1;

      // Decay shake
      this.shakeIntensity -= this.shakeDecay * deltaTime;
    } else {
      this.shakeIntensity = 0;
      camera.rotation.z = 0;
    }
  }

  /**
   * Show death overlay
   */
  showDeathScreen(): void {
    this.damageOverlay.style.opacity = '0.5';
    this.damageOverlay.style.transition = 'opacity 1s ease-in';
  }

  /**
   * Hide death overlay (on respawn)
   */
  hideDeathScreen(): void {
    this.damageOverlay.style.opacity = '0';
    this.damageOverlay.style.transition = 'opacity 0.3s ease-out';
  }

  /**
   * Clean up
   */
  dispose(): void {
    this.damageOverlay.remove();
  }
}
