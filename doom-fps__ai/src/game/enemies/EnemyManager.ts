import * as THREE from 'three';
import { Enemy } from './Enemy';

export class EnemyManager {
  private enemies: Enemy[] = [];
  private scene: THREE.Scene;
  private onPlayerDamageCallback?: (damage: number) => void;

  constructor(scene: THREE.Scene) {
    this.scene = scene;
  }

  /**
   * Set callback for when enemies damage the player
   */
  setOnPlayerDamage(callback: (damage: number) => void): void {
    this.onPlayerDamageCallback = callback;
  }

  /**
   * Spawn an enemy at position
   */
  spawnEnemy(position: THREE.Vector3): Enemy {
    const enemy = new Enemy(position);

    // Set attack callback to damage player
    if (this.onPlayerDamageCallback) {
      enemy.setOnAttack(this.onPlayerDamageCallback);
    }

    this.enemies.push(enemy);
    this.scene.add(enemy.getModel());
    console.log(`Enemy spawned at (${position.x.toFixed(1)}, ${position.y.toFixed(1)}, ${position.z.toFixed(1)})`);
    return enemy;
  }

  /**
   * Spawn multiple enemies
   */
  spawnEnemies(positions: THREE.Vector3[]): void {
    positions.forEach(pos => this.spawnEnemy(pos));
  }

  /**
   * Update all enemies
   */
  update(deltaTime: number, playerPosition: THREE.Vector3): void {
    // Update all enemies
    for (const enemy of this.enemies) {
      enemy.update(deltaTime, playerPosition);
    }

    // Remove dead enemies
    this.removeDeadEnemies();
  }

  /**
   * Remove dead enemies from scene
   */
  private removeDeadEnemies(): void {
    const deadEnemies = this.enemies.filter(enemy => enemy.isDead());

    for (const enemy of deadEnemies) {
      console.log('Enemy killed!');
      this.scene.remove(enemy.getModel());
      enemy.dispose();
    }

    // Remove from array
    this.enemies = this.enemies.filter(enemy => !enemy.isDead());
  }

  /**
   * Check if raycast hit an enemy
   */
  checkHit(rayOrigin: THREE.Vector3, rayDirection: THREE.Vector3): Enemy | null {
    const raycaster = new THREE.Raycaster(rayOrigin, rayDirection);

    // Get all enemy models
    const enemyModels = this.enemies.map(enemy => enemy.getModel());

    // Check intersections
    const intersects = raycaster.intersectObjects(enemyModels);

    if (intersects.length > 0) {
      const hitMesh = intersects[0].object as THREE.Mesh;
      return hitMesh.userData.enemy as Enemy;
    }

    return null;
  }

  /**
   * Get all enemies
   */
  getEnemies(): Enemy[] {
    return this.enemies;
  }

  /**
   * Get enemy count
   */
  getEnemyCount(): number {
    return this.enemies.length;
  }

  /**
   * Clear all enemies
   */
  clearAll(): void {
    for (const enemy of this.enemies) {
      this.scene.remove(enemy.getModel());
      enemy.dispose();
    }
    this.enemies = [];
  }
}
