import * as THREE from 'three';

export enum EnemyState {
  IDLE = 'idle',
  CHASE = 'chase',
  ATTACK = 'attack'
}

export class Enemy {
  model: THREE.Group;
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
  private readonly HIT_FLASH_DURATION = 0.15;
  private bodyMaterial!: THREE.MeshStandardMaterial;
  private eyeMaterial!: THREE.MeshBasicMaterial;
  private allMaterials: THREE.Material[] = [];

  constructor(position: THREE.Vector3) {
    this.position = position.clone();

    // Create demon model group
    this.model = new THREE.Group();
    this.createDemonModel();
    this.model.position.copy(this.position);

    // Store reference to enemy in mesh userData
    this.model.userData.enemy = this;
  }

  private createDemonModel(): void {
    // Dark demonic body material
    this.bodyMaterial = new THREE.MeshStandardMaterial({
      color: 0x441111, // Dark demon red
      roughness: 0.8,
      metalness: 0.2
    });
    this.allMaterials.push(this.bodyMaterial);

    // Glowing eye material
    this.eyeMaterial = new THREE.MeshBasicMaterial({
      color: 0xff0000 // Bright red glow
    });
    this.allMaterials.push(this.eyeMaterial);

    // Main torso - muscular barrel shape
    const torsoGeometry = new THREE.CylinderGeometry(0.35, 0.4, 1.0, 8);
    const torso = new THREE.Mesh(torsoGeometry, this.bodyMaterial);
    torso.position.y = 0.9;
    torso.castShadow = true;
    torso.receiveShadow = true;
    this.model.add(torso);

    // Head - demonic skull shape
    const headGeometry = new THREE.SphereGeometry(0.28, 8, 8);
    const head = new THREE.Mesh(headGeometry, this.bodyMaterial);
    head.position.y = 1.65;
    head.scale.set(1, 0.9, 0.85);
    head.castShadow = true;
    this.model.add(head);

    // Horns
    const hornMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a0a0a,
      roughness: 0.6,
      metalness: 0.3
    });
    this.allMaterials.push(hornMaterial);

    const hornGeometry = new THREE.ConeGeometry(0.08, 0.35, 6);

    // Left horn
    const leftHorn = new THREE.Mesh(hornGeometry, hornMaterial);
    leftHorn.position.set(-0.18, 1.85, 0);
    leftHorn.rotation.z = 0.4;
    leftHorn.rotation.x = -0.2;
    leftHorn.castShadow = true;
    this.model.add(leftHorn);

    // Right horn
    const rightHorn = new THREE.Mesh(hornGeometry, hornMaterial);
    rightHorn.position.set(0.18, 1.85, 0);
    rightHorn.rotation.z = -0.4;
    rightHorn.rotation.x = -0.2;
    rightHorn.castShadow = true;
    this.model.add(rightHorn);

    // Glowing eyes
    const eyeGeometry = new THREE.SphereGeometry(0.05, 6, 6);

    const leftEye = new THREE.Mesh(eyeGeometry, this.eyeMaterial);
    leftEye.position.set(-0.1, 1.68, 0.22);
    this.model.add(leftEye);

    const rightEye = new THREE.Mesh(eyeGeometry, this.eyeMaterial);
    rightEye.position.set(0.1, 1.68, 0.22);
    this.model.add(rightEye);

    // Arms - clawed appendages
    const armGeometry = new THREE.CylinderGeometry(0.08, 0.12, 0.6, 6);

    // Left arm
    const leftArm = new THREE.Mesh(armGeometry, this.bodyMaterial);
    leftArm.position.set(-0.45, 1.0, 0);
    leftArm.rotation.z = 0.6;
    leftArm.castShadow = true;
    this.model.add(leftArm);

    // Right arm
    const rightArm = new THREE.Mesh(armGeometry, this.bodyMaterial);
    rightArm.position.set(0.45, 1.0, 0);
    rightArm.rotation.z = -0.6;
    rightArm.castShadow = true;
    this.model.add(rightArm);

    // Claws
    const clawGeometry = new THREE.ConeGeometry(0.04, 0.15, 4);
    const clawMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a1515,
      roughness: 0.5,
      metalness: 0.4
    });
    this.allMaterials.push(clawMaterial);

    // Left claws
    for (let i = 0; i < 3; i++) {
      const claw = new THREE.Mesh(clawGeometry, clawMaterial);
      claw.position.set(-0.55 - i * 0.05, 0.65, (i - 1) * 0.06);
      claw.rotation.z = 1.2;
      this.model.add(claw);
    }

    // Right claws
    for (let i = 0; i < 3; i++) {
      const claw = new THREE.Mesh(clawGeometry, clawMaterial);
      claw.position.set(0.55 + i * 0.05, 0.65, (i - 1) * 0.06);
      claw.rotation.z = -1.2;
      this.model.add(claw);
    }

    // Legs - thick stumpy legs
    const legGeometry = new THREE.CylinderGeometry(0.12, 0.15, 0.5, 6);

    const leftLeg = new THREE.Mesh(legGeometry, this.bodyMaterial);
    leftLeg.position.set(-0.18, 0.25, 0);
    leftLeg.castShadow = true;
    this.model.add(leftLeg);

    const rightLeg = new THREE.Mesh(legGeometry, this.bodyMaterial);
    rightLeg.position.set(0.18, 0.25, 0);
    rightLeg.castShadow = true;
    this.model.add(rightLeg);

    // Hooves/feet
    const hoofGeometry = new THREE.BoxGeometry(0.18, 0.08, 0.22);
    const hoofMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a0505,
      roughness: 0.9
    });
    this.allMaterials.push(hoofMaterial);

    const leftHoof = new THREE.Mesh(hoofGeometry, hoofMaterial);
    leftHoof.position.set(-0.18, 0.04, 0.02);
    this.model.add(leftHoof);

    const rightHoof = new THREE.Mesh(hoofGeometry, hoofMaterial);
    rightHoof.position.set(0.18, 0.04, 0.02);
    this.model.add(rightHoof);
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
        // Reset to base demon color
        this.bodyMaterial.color.setHex(0x441111);
        this.bodyMaterial.emissive.setHex(0x000000);
        this.eyeMaterial.color.setHex(0xff0000);
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

    // Blood-red flash on hit with emissive glow
    this.bodyMaterial.color.setHex(0x880000);
    this.bodyMaterial.emissive.setHex(0x440000);
    this.eyeMaterial.color.setHex(0xffff00); // Eyes flash yellow
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
  getModel(): THREE.Group {
    return this.model;
  }

  /**
   * Clean up resources
   */
  dispose(): void {
    // Dispose all geometries in the group
    this.model.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.geometry.dispose();
      }
    });
    // Dispose all materials
    for (const material of this.allMaterials) {
      material.dispose();
    }
  }
}
