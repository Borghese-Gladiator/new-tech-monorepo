import * as THREE from 'three';

export enum EnemyState {
  IDLE = 'idle',
  CHASE = 'chase',
  ATTACK = 'attack'
}

export class Enemy {
  model: THREE.Mesh;
  private health = 100;
  private maxHealth = 100;
  private state = EnemyState.IDLE;
  private position: THREE.Vector3;

  // Stats
  private readonly MOVE_SPEED = 3.0;
  private readonly DETECTION_RANGE = 15;
  private readonly ATTACK_RANGE = 2;
  private readonly ATTACK_DAMAGE = 10;
  private readonly ATTACK_COOLDOWN = 1.0;

  private attackTimer = 0;
  private hitFlashTimer = 0;
  private readonly HIT_FLASH_DURATION = 0.1;
  private baseMaterial: THREE.MeshStandardMaterial;

  constructor(position: THREE.Vector3) {
    this.position = position.clone();

    // Create enemy model (red box)
    const geometry = new THREE.BoxGeometry(0.6, 1.8, 0.6);
    this.baseMaterial = new THREE.MeshStandardMaterial({
      color: 0xff4444,
      roughness: 0.7
    });
    this.model = new THREE.Mesh(geometry, this.baseMaterial);
    this.model.position.copy(this.position);
    this.model.castShadow = true;
    this.model.receiveShadow = true;

    // Store reference to enemy in mesh userData
    this.model.userData.enemy = this;
  }

  /**
   * Update enemy AI and behavior
   */
  update(deltaTime: number, playerPosition: THREE.Vector3): void {
    // Update timers
    if (this.attackTimer > 0) {
      this.attackTimer -= deltaTime;
    }
    if (this.hitFlashTimer > 0) {
      this.hitFlashTimer -= deltaTime;
      if (this.hitFlashTimer <= 0) {
        // Reset to base color
        this.baseMaterial.color.setHex(0xff4444);
      }
    }

    // Calculate distance to player
    const distanceToPlayer = this.position.distanceTo(playerPosition);

    // State machine
    switch (this.state) {
      case EnemyState.IDLE:
        this.updateIdle(distanceToPlayer);
        break;

      case EnemyState.CHASE:
        this.updateChase(deltaTime, playerPosition, distanceToPlayer);
        break;

      case EnemyState.ATTACK:
        this.updateAttack(deltaTime, distanceToPlayer);
        break;
    }

    // Update model position
    this.model.position.copy(this.position);
  }

  /**
   * Idle state: Check for player in range
   */
  private updateIdle(distanceToPlayer: number): void {
    if (distanceToPlayer <= this.DETECTION_RANGE) {
      this.state = EnemyState.CHASE;
    }
  }

  /**
   * Chase state: Move toward player
   */
  private updateChase(deltaTime: number, playerPosition: THREE.Vector3, distanceToPlayer: number): void {
    // Check if in attack range
    if (distanceToPlayer <= this.ATTACK_RANGE) {
      this.state = EnemyState.ATTACK;
      return;
    }

    // Check if player out of range
    if (distanceToPlayer > this.DETECTION_RANGE * 1.2) {
      this.state = EnemyState.IDLE;
      return;
    }

    // Move toward player
    const direction = new THREE.Vector3()
      .subVectors(playerPosition, this.position)
      .normalize();

    // Only move on XZ plane (don't fly)
    direction.y = 0;
    direction.normalize();

    this.position.add(direction.multiplyScalar(this.MOVE_SPEED * deltaTime));

    // Look at player
    this.model.lookAt(playerPosition);
  }

  /**
   * Attack state: Deal damage to player
   */
  private updateAttack(deltaTime: number, distanceToPlayer: number): void {
    // Check if player moved out of range
    if (distanceToPlayer > this.ATTACK_RANGE * 1.2) {
      this.state = EnemyState.CHASE;
      return;
    }

    // Attack on cooldown
    if (this.attackTimer <= 0) {
      this.performAttack();
      this.attackTimer = this.ATTACK_COOLDOWN;
    }
  }

  /**
   * Perform attack and return damage amount
   */
  private performAttack(): void {
    console.log(`Enemy attacks for ${this.ATTACK_DAMAGE} damage!`);
    // Emit attack event if callback is set
    if (this.onAttackCallback) {
      this.onAttackCallback(this.ATTACK_DAMAGE);
    }
  }

  private onAttackCallback?: (damage: number) => void;

  /**
   * Set attack callback (called when enemy attacks)
   */
  setOnAttack(callback: (damage: number) => void): void {
    this.onAttackCallback = callback;
  }

  /**
   * Take damage from weapon
   */
  takeDamage(amount: number): void {
    this.health -= amount;
    console.log(`Enemy takes ${amount} damage! Health: ${this.health}/${this.maxHealth}`);

    // Flash white on hit
    this.baseMaterial.color.setHex(0xffffff);
    this.hitFlashTimer = this.HIT_FLASH_DURATION;

    // Force chase state when hit
    if (this.state === EnemyState.IDLE) {
      this.state = EnemyState.CHASE;
    }
  }

  /**
   * Check if enemy is dead
   */
  isDead(): boolean {
    return this.health <= 0;
  }

  /**
   * Get current position
   */
  getPosition(): THREE.Vector3 {
    return this.position.clone();
  }

  /**
   * Get current state
   */
  getState(): EnemyState {
    return this.state;
  }

  /**
   * Get model for adding to scene
   */
  getModel(): THREE.Mesh {
    return this.model;
  }

  /**
   * Clean up resources
   */
  dispose(): void {
    this.model.geometry.dispose();
    this.baseMaterial.dispose();
  }
}
