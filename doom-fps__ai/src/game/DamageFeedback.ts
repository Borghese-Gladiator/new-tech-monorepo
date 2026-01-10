import * as THREE from 'three';

export class DamageFeedback {
  private damageOverlay: HTMLDivElement;
  private vignetteOverlay: HTMLDivElement;
  private shakeIntensity = 0;
  private shakeDecay = 4.0; // How fast shake fades - slower for DOOM feel

  constructor(container: HTMLElement) {
    // Create dark blood red damage overlay - DOOM style
    this.damageOverlay = document.createElement('div');
    this.damageOverlay.style.position = 'fixed';
    this.damageOverlay.style.top = '0';
    this.damageOverlay.style.left = '0';
    this.damageOverlay.style.width = '100%';
    this.damageOverlay.style.height = '100%';
    this.damageOverlay.style.backgroundColor = '#440000'; // Darker blood red
    this.damageOverlay.style.opacity = '0';
    this.damageOverlay.style.pointerEvents = 'none';
    this.damageOverlay.style.transition = 'opacity 0.2s ease-out';
    this.damageOverlay.style.zIndex = '100';
    container.appendChild(this.damageOverlay);

    // Create permanent vignette overlay for DOOM atmosphere (subtle for visibility)
    this.vignetteOverlay = document.createElement('div');
    this.vignetteOverlay.style.position = 'fixed';
    this.vignetteOverlay.style.top = '0';
    this.vignetteOverlay.style.left = '0';
    this.vignetteOverlay.style.width = '100%';
    this.vignetteOverlay.style.height = '100%';
    this.vignetteOverlay.style.pointerEvents = 'none';
    this.vignetteOverlay.style.zIndex = '99';
    this.vignetteOverlay.style.background = `
      radial-gradient(ellipse at center,
        transparent 0%,
        transparent 60%,
        rgba(10, 0, 0, 0.15) 85%,
        rgba(10, 0, 0, 0.3) 100%
      )
    `;
    container.appendChild(this.vignetteOverlay);
  }

  /**
   * Flash dark red screen when taking damage - DOOM style visceral feedback
   */
  flashDamage(intensity: number = 0.5): void {
    // Higher opacity for more visceral feel
    this.damageOverlay.style.opacity = intensity.toString();

    // Quick flash followed by fade
    setTimeout(() => {
      this.damageOverlay.style.opacity = (intensity * 0.3).toString();
    }, 80);

    setTimeout(() => {
      this.damageOverlay.style.opacity = '0';
    }, 200);
  }

  /**
   * Trigger camera shake - more intense for DOOM feel
   */
  triggerShake(intensity: number = 0.15): void {
    this.shakeIntensity = intensity;
  }

  /**
   * Update shake effect and apply to camera
   */
  update(deltaTime: number, camera: THREE.Camera): void {
    if (this.shakeIntensity > 0.001) {
      // Random offset - more pronounced
      const offsetX = (Math.random() - 0.5) * this.shakeIntensity * 2;
      const offsetY = (Math.random() - 0.5) * this.shakeIntensity * 2;

      // Apply shake to camera rotation and position
      camera.rotation.z = offsetX * 0.5;
      camera.position.x += offsetX * 0.15;
      camera.position.y += offsetY * 0.15;

      // Decay shake
      this.shakeIntensity *= Math.pow(0.1, deltaTime * this.shakeDecay);
    } else {
      this.shakeIntensity = 0;
      camera.rotation.z = 0;
    }
  }

  /**
   * Show death overlay - DOOM style
   */
  showDeathScreen(): void {
    this.damageOverlay.style.backgroundColor = '#220000';
    this.damageOverlay.style.opacity = '0.7';
    this.damageOverlay.style.transition = 'opacity 0.8s ease-in';
  }

  /**
   * Hide death overlay (on respawn)
   */
  hideDeathScreen(): void {
    this.damageOverlay.style.backgroundColor = '#440000';
    this.damageOverlay.style.opacity = '0';
    this.damageOverlay.style.transition = 'opacity 0.3s ease-out';
  }

  /**
   * Intensify vignette when low health (still allows visibility)
   */
  setLowHealthVignette(active: boolean): void {
    if (active) {
      this.vignetteOverlay.style.background = `
        radial-gradient(ellipse at center,
          transparent 0%,
          transparent 40%,
          rgba(40, 0, 0, 0.25) 70%,
          rgba(20, 0, 0, 0.5) 100%
        )
      `;
    } else {
      this.vignetteOverlay.style.background = `
        radial-gradient(ellipse at center,
          transparent 0%,
          transparent 60%,
          rgba(10, 0, 0, 0.15) 85%,
          rgba(10, 0, 0, 0.3) 100%
        )
      `;
    }
  }

  /**
   * Clean up
   */
  dispose(): void {
    this.damageOverlay.remove();
    this.vignetteOverlay.remove();
  }
}
