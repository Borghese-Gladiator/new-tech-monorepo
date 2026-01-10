import * as THREE from 'three';

export class HitEffect {
  private scene: THREE.Scene;
  private bulletHoleTexture?: THREE.Texture;
  private decals: THREE.Mesh[] = [];
  private readonly MAX_DECALS = 50; // Limit decals to prevent memory leak

  constructor(scene: THREE.Scene) {
    this.scene = scene;
  }

  /**
   * Create a bullet impact effect at the hit point - DOOM style hellfire
   */
  createImpact(point: THREE.Vector3, normal: THREE.Vector3): void {
    // Create bullet hole decal
    this.createBulletHole(point, normal);

    // Create hellfire particle spark effect
    this.createHellfireParticles(point, normal);
  }

  /**
   * Create a bullet hole decal on the surface - blood splatter style
   */
  private createBulletHole(point: THREE.Vector3, normal: THREE.Vector3): void {
    const size = 0.12 + Math.random() * 0.08;
    const geometry = new THREE.PlaneGeometry(size, size);

    // Darker, blood-tinted decal
    const material = new THREE.MeshBasicMaterial({
      color: 0x1a0505, // Very dark red/black
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
      side: THREE.DoubleSide
    });

    const decal = new THREE.Mesh(geometry, material);

    // Position slightly offset from surface to prevent z-fighting
    decal.position.copy(point).add(normal.clone().multiplyScalar(0.01));

    // Orient to surface normal
    decal.lookAt(point.clone().add(normal));

    // Random rotation around normal
    decal.rotateZ(Math.random() * Math.PI * 2);

    this.scene.add(decal);
    this.decals.push(decal);

    // Remove oldest decal if limit reached
    if (this.decals.length > this.MAX_DECALS) {
      const oldDecal = this.decals.shift();
      if (oldDecal) {
        this.scene.remove(oldDecal);
        oldDecal.geometry.dispose();
        (oldDecal.material as THREE.Material).dispose();
      }
    }
  }

  /**
   * Create hellfire spark particles for bullet impact - DOOM style
   */
  private createHellfireParticles(point: THREE.Vector3, normal: THREE.Vector3): void {
    const particleCount = 8 + Math.floor(Math.random() * 7); // More particles
    const particles: THREE.Mesh[] = [];

    for (let i = 0; i < particleCount; i++) {
      const geometry = new THREE.SphereGeometry(0.025, 4, 4);

      // Hellfire colors - mix of green, yellow, and orange
      const colorChoice = Math.random();
      let color: THREE.Color;
      if (colorChoice < 0.4) {
        // Hellfire green
        color = new THREE.Color().setHSL(0.33, 1, 0.5 + Math.random() * 0.3);
      } else if (colorChoice < 0.7) {
        // Demonic orange/red
        color = new THREE.Color().setHSL(0.05 + Math.random() * 0.05, 1, 0.5 + Math.random() * 0.3);
      } else {
        // Yellow sparks
        color = new THREE.Color().setHSL(0.15, 1, 0.6 + Math.random() * 0.2);
      }

      const material = new THREE.MeshBasicMaterial({ color });
      const particle = new THREE.Mesh(geometry, material);

      // Position at impact point
      particle.position.copy(point);

      // Random velocity in hemisphere direction - faster spread
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 2.5,
        Math.random() * 1.5,
        (Math.random() - 0.5) * 2.5
      ).normalize().multiplyScalar(3 + Math.random() * 4);

      // Bias velocity toward surface normal
      velocity.add(normal.clone().multiplyScalar(2.5));

      particle.userData.velocity = velocity;
      particle.userData.lifetime = 0.4 + Math.random() * 0.3; // Longer lifetime
      particle.userData.age = 0;

      this.scene.add(particle);
      particles.push(particle);
    }

    // Animate and remove particles
    this.animateParticles(particles);
  }

  /**
   * Create blood particles when hitting enemy
   */
  createBloodEffect(point: THREE.Vector3, direction: THREE.Vector3): void {
    const particleCount = 10 + Math.floor(Math.random() * 8);
    const particles: THREE.Mesh[] = [];

    for (let i = 0; i < particleCount; i++) {
      const geometry = new THREE.SphereGeometry(0.03 + Math.random() * 0.02, 4, 4);

      // Blood red colors
      const color = new THREE.Color().setHSL(0, 0.9, 0.2 + Math.random() * 0.2);

      const material = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.9
      });
      const particle = new THREE.Mesh(geometry, material);

      // Position at impact point
      particle.position.copy(point);

      // Random velocity biased in direction of shot
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 3,
        Math.random() * 2,
        (Math.random() - 0.5) * 3
      );
      velocity.add(direction.clone().multiplyScalar(2));

      particle.userData.velocity = velocity;
      particle.userData.lifetime = 0.5 + Math.random() * 0.3;
      particle.userData.age = 0;

      this.scene.add(particle);
      particles.push(particle);
    }

    this.animateParticles(particles);
  }

  /**
   * Animate particle lifetime
   */
  private animateParticles(particles: THREE.Mesh[]): void {
    const animate = () => {
      const deltaTime = 0.016; // ~60fps
      let allDead = true;

      for (const particle of particles) {
        particle.userData.age += deltaTime;

        if (particle.userData.age < particle.userData.lifetime) {
          allDead = false;

          // Update position
          const velocity = particle.userData.velocity as THREE.Vector3;
          particle.position.add(velocity.clone().multiplyScalar(deltaTime));

          // Apply gravity
          velocity.y -= 12 * deltaTime; // Slightly stronger gravity

          // Fade out
          const material = particle.material as THREE.MeshBasicMaterial;
          material.opacity = 1 - (particle.userData.age / particle.userData.lifetime);
          material.transparent = true;

          // Shrink
          const scale = 1 - (particle.userData.age / particle.userData.lifetime) * 0.6;
          particle.scale.set(scale, scale, scale);
        }
      }

      if (!allDead) {
        requestAnimationFrame(animate);
      } else {
        // Clean up
        for (const particle of particles) {
          this.scene.remove(particle);
          particle.geometry.dispose();
          (particle.material as THREE.Material).dispose();
        }
      }
    };

    animate();
  }

  /**
   * Clear all decals from the scene
   */
  clearDecals(): void {
    for (const decal of this.decals) {
      this.scene.remove(decal);
      decal.geometry.dispose();
      (decal.material as THREE.Material).dispose();
    }
    this.decals = [];
  }
}
