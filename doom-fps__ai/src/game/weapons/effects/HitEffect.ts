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
   * Create a bullet impact effect at the hit point
   */
  createImpact(point: THREE.Vector3, normal: THREE.Vector3): void {
    // Create bullet hole decal
    this.createBulletHole(point, normal);

    // Create particle spark effect
    this.createSparkParticles(point, normal);
  }

  /**
   * Create a bullet hole decal on the surface
   */
  private createBulletHole(point: THREE.Vector3, normal: THREE.Vector3): void {
    const size = 0.1 + Math.random() * 0.05;
    const geometry = new THREE.PlaneGeometry(size, size);
    const material = new THREE.MeshBasicMaterial({
      color: 0x222222,
      transparent: true,
      opacity: 0.8,
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
   * Create spark particles for bullet impact
   */
  private createSparkParticles(point: THREE.Vector3, normal: THREE.Vector3): void {
    const particleCount = 5 + Math.floor(Math.random() * 5);
    const particles: THREE.Mesh[] = [];

    for (let i = 0; i < particleCount; i++) {
      const geometry = new THREE.SphereGeometry(0.02, 4, 4);
      const material = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setHSL(0.1, 1, 0.5 + Math.random() * 0.3)
      });
      const particle = new THREE.Mesh(geometry, material);

      // Position at impact point
      particle.position.copy(point);

      // Random velocity in hemisphere direction
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 2,
        Math.random(),
        (Math.random() - 0.5) * 2
      ).normalize().multiplyScalar(2 + Math.random() * 3);

      // Bias velocity toward surface normal
      velocity.add(normal.clone().multiplyScalar(2));

      particle.userData.velocity = velocity;
      particle.userData.lifetime = 0.3 + Math.random() * 0.2;
      particle.userData.age = 0;

      this.scene.add(particle);
      particles.push(particle);
    }

    // Animate and remove particles
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
          velocity.y -= 9.8 * deltaTime;

          // Fade out
          const material = particle.material as THREE.MeshBasicMaterial;
          material.opacity = 1 - (particle.userData.age / particle.userData.lifetime);
          material.transparent = true;

          // Shrink
          const scale = 1 - (particle.userData.age / particle.userData.lifetime) * 0.5;
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
