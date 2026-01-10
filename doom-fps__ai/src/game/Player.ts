import * as THREE from 'three';
import { InputManager } from '../utils/Input';
import { CollisionSystem } from './Collision';
import { WeaponManager } from './weapons/WeaponManager';
import { PlayerHealth } from './PlayerHealth';
import { DamageFeedback } from './DamageFeedback';
import { RecoilConfig } from './weapons/Weapon';

export class Player {
  camera: THREE.PerspectiveCamera;
  weaponManager: WeaponManager;
  health: PlayerHealth;
  damageFeedback: DamageFeedback;
  private velocity = new THREE.Vector3();
  private position: THREE.Vector3;
  private spawnPosition: THREE.Vector3;
  private rotation = { x: 0, y: 0 }; // pitch and yaw
  private onGround = false;

  // Recoil state
  private recoilOffset = { x: 0, y: 0 };  // Current recoil displacement (pitch, yaw)
  private currentRecoilConfig: RecoilConfig | null = null;

  // Player physics constants
  private readonly MOVE_SPEED = 5.0;
  private readonly JUMP_SPEED = 6.0;
  private readonly GRAVITY = -20.0;
  private readonly MOUSE_SENSITIVITY = 0.002;
  private readonly PLAYER_HEIGHT = 1.8;
  private readonly PLAYER_RADIUS = 0.4;

  // Player collision box dimensions
  private readonly collisionBox = {
    width: this.PLAYER_RADIUS * 2,
    height: this.PLAYER_HEIGHT,
    depth: this.PLAYER_RADIUS * 2
  };

  constructor(
    private input: InputManager,
    private collision: CollisionSystem,
    scene: THREE.Scene,
    container: HTMLElement,
    spawnPosition = new THREE.Vector3(0, 2, 0)
  ) {
    this.spawnPosition = spawnPosition.clone();
    this.position = spawnPosition.clone();
    this.camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.camera.position.copy(this.position);

    // Initialize weapon manager
    this.weaponManager = new WeaponManager(scene);

    // Initialize health system
    this.health = new PlayerHealth(100);

    // Initialize damage feedback
    this.damageFeedback = new DamageFeedback(container);

    window.addEventListener('resize', () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
    });
  }

  update(deltaTime: number, scene: THREE.Scene): void {
    if (!this.input.getPointerLocked()) return;

    // Don't update if dead
    if (this.health.getIsDead()) return;

    this.updateRotation();
    this.updateMovement(deltaTime);
    this.updateWeapons(deltaTime, scene);
    this.updateRecoilRecovery(deltaTime);
    this.updateDamageFeedback(deltaTime);
  }

  private updateDamageFeedback(deltaTime: number): void {
    this.damageFeedback.update(deltaTime, this.camera);
  }

  private updateWeapons(deltaTime: number, scene: THREE.Scene): void {
    // Track if we fired this frame for recoil
    let firedThisFrame = false;

    // Handle weapon firing
    if (this.input.isMouseButtonJustPressed(0)) {
      // Left click - fire weapon (semi-auto)
      firedThisFrame = this.weaponManager.fire(this.camera, scene);
    }

    if (this.input.isMouseButtonPressed(0)) {
      // Hold left click - continuous fire for full-auto weapons
      this.weaponManager.startFiring();
    } else {
      this.weaponManager.stopFiring();
    }

    // Handle reload
    if (this.input.isKeyPressed('KeyR')) {
      this.weaponManager.reload();
    }

    // Handle weapon switching
    if (this.input.isKeyPressed('Digit1')) {
      this.weaponManager.switchToWeapon(0);
    }
    if (this.input.isKeyPressed('Digit2')) {
      this.weaponManager.switchToWeapon(1);
    }

    // Get mouse movement for weapon sway
    const mouseDelta = this.input.getMouseMovement();

    // Check if player is moving for weapon bob
    const isMoving =
      this.input.isKeyPressed('KeyW') ||
      this.input.isKeyPressed('KeyS') ||
      this.input.isKeyPressed('KeyA') ||
      this.input.isKeyPressed('KeyD');

    // Update weapon manager with animation parameters
    // This also handles full-auto firing internally
    const prevAmmo = this.weaponManager.getCurrentWeapon()?.getCurrentAmmo() ?? 0;
    this.weaponManager.update(deltaTime, this.camera, scene, mouseDelta, isMoving);
    const currAmmo = this.weaponManager.getCurrentWeapon()?.getCurrentAmmo() ?? 0;

    // Check if full-auto weapon fired during update
    if (currAmmo < prevAmmo) {
      firedThisFrame = true;
    }

    // Apply recoil if weapon fired
    if (firedThisFrame) {
      this.applyRecoil();
    }

    // Update current recoil config for recovery
    const currentWeapon = this.weaponManager.getCurrentWeapon();
    if (currentWeapon) {
      this.currentRecoilConfig = currentWeapon.getRecoilConfig();
    }

    // Clear just-pressed state after processing
    this.input.clearMouseJustPressed();
  }

  private updateRotation(): void {
    const mouse = this.input.getMouseMovement();

    // Update yaw (horizontal rotation)
    this.rotation.y -= mouse.x * this.MOUSE_SENSITIVITY;

    // Update pitch (vertical rotation) with limits
    this.rotation.x -= mouse.y * this.MOUSE_SENSITIVITY;
    this.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.rotation.x));

    // Apply rotation to camera
    this.camera.rotation.order = 'YXZ';
    this.camera.rotation.y = this.rotation.y;
    this.camera.rotation.x = this.rotation.x;

    this.input.resetMouseMovement();
  }

  private updateMovement(deltaTime: number): void {
    // Get movement input
    const moveDirection = new THREE.Vector3();

    if (this.input.isKeyPressed('KeyW')) moveDirection.z -= 1;
    if (this.input.isKeyPressed('KeyS')) moveDirection.z += 1;
    if (this.input.isKeyPressed('KeyA')) moveDirection.x -= 1;
    if (this.input.isKeyPressed('KeyD')) moveDirection.x += 1;

    // Normalize to prevent faster diagonal movement
    if (moveDirection.length() > 0) {
      moveDirection.normalize();
    }

    // Transform movement direction based on camera yaw
    const yaw = this.rotation.y;
    const forward = new THREE.Vector3(
      Math.sin(yaw),
      0,
      Math.cos(yaw)
    );
    const right = new THREE.Vector3(
      Math.sin(yaw + Math.PI / 2),
      0,
      Math.cos(yaw + Math.PI / 2)
    );

    // Calculate velocity
    const targetVelocityX = (forward.x * moveDirection.z + right.x * moveDirection.x) * this.MOVE_SPEED;
    const targetVelocityZ = (forward.z * moveDirection.z + right.z * moveDirection.x) * this.MOVE_SPEED;

    // Apply horizontal velocity (instant acceleration for responsive feel)
    this.velocity.x = targetVelocityX;
    this.velocity.z = targetVelocityZ;

    // Apply gravity
    this.velocity.y += this.GRAVITY * deltaTime;

    // Jump
    if (this.input.isKeyPressed('Space') && this.onGround) {
      this.velocity.y = this.JUMP_SPEED;
      this.onGround = false;
    }

    // Calculate target position
    const targetPosition = this.position.clone();
    targetPosition.add(this.velocity.clone().multiplyScalar(deltaTime));

    // Collision detection and response
    const newPosition = this.collision.sweepTest(
      this.position,
      targetPosition,
      this.collisionBox
    );

    // Check if we're on the ground
    const groundTest = this.collision.sweepTest(
      newPosition,
      newPosition.clone().add(new THREE.Vector3(0, -0.1, 0)),
      this.collisionBox
    );

    if (groundTest.y === newPosition.y) {
      // We're on the ground
      this.onGround = true;
      if (this.velocity.y < 0) {
        this.velocity.y = 0;
      }
    } else {
      this.onGround = false;
    }

    // Update position
    this.position.copy(newPosition);
    this.camera.position.copy(this.position);
  }

  /**
   * Apply recoil kick when firing
   */
  private applyRecoil(): void {
    const weapon = this.weaponManager.getCurrentWeapon();
    if (!weapon) return;

    const recoil = weapon.getRecoilConfig();
    const pattern = recoil.pattern || 'snappy';

    // Convert degrees to radians
    const verticalRad = (recoil.vertical * Math.PI) / 180;
    const horizontalRad = (recoil.horizontal * Math.PI) / 180;

    // Calculate recoil amounts based on pattern
    let verticalKick: number;
    let horizontalKick: number;

    if (pattern === 'snappy') {
      // Pistol-style: strong instant kick with fast recovery
      verticalKick = verticalRad;
      horizontalKick = (Math.random() - 0.5) * 2 * horizontalRad;
    } else {
      // Climbing pattern: recoil accumulates during sustained fire
      // Add to existing recoil (creates climbing effect)
      const currentRecoilMagnitude = Math.abs(this.recoilOffset.x);
      const climbMultiplier = 1 + currentRecoilMagnitude * 2; // Increases as you spray

      verticalKick = verticalRad * climbMultiplier;
      // Horizontal becomes more erratic as spray continues
      horizontalKick = (Math.random() - 0.5) * 2 * horizontalRad * climbMultiplier;
    }

    // Apply recoil to rotation (negative x = look up)
    this.rotation.x -= verticalKick;
    this.rotation.y += horizontalKick;

    // Track recoil offset for recovery
    this.recoilOffset.x += verticalKick;
    this.recoilOffset.y += horizontalKick;

    // Clamp pitch
    this.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.rotation.x));

    // Apply to camera immediately
    this.camera.rotation.x = this.rotation.x;
    this.camera.rotation.y = this.rotation.y;
  }

  /**
   * Recover from recoil over time
   */
  private updateRecoilRecovery(deltaTime: number): void {
    if (!this.currentRecoilConfig) return;

    const recoveryRate = (this.currentRecoilConfig.recovery * Math.PI) / 180; // degrees to radians per second
    const pattern = this.currentRecoilConfig.pattern || 'snappy';

    // Different recovery behavior based on pattern
    if (pattern === 'snappy') {
      // Fast recovery back to original position
      const recoveryAmount = recoveryRate * deltaTime;

      // Recover vertical recoil
      if (Math.abs(this.recoilOffset.x) > 0.001) {
        const recoverX = Math.min(recoveryAmount, Math.abs(this.recoilOffset.x));
        const signX = Math.sign(this.recoilOffset.x);
        this.rotation.x += recoverX * signX;
        this.recoilOffset.x -= recoverX * signX;
      }

      // Recover horizontal recoil
      if (Math.abs(this.recoilOffset.y) > 0.001) {
        const recoverY = Math.min(recoveryAmount, Math.abs(this.recoilOffset.y));
        const signY = Math.sign(this.recoilOffset.y);
        this.rotation.y -= recoverY * signY;
        this.recoilOffset.y -= recoverY * signY;
      }
    } else {
      // Climbing pattern: slower recovery, doesn't fully reset while firing
      const isFiring = this.weaponManager.getIsFiring();
      const effectiveRecovery = isFiring ? recoveryRate * 0.3 : recoveryRate; // Slower while firing

      const recoveryAmount = effectiveRecovery * deltaTime;

      // Recover vertical
      if (Math.abs(this.recoilOffset.x) > 0.001) {
        const recoverX = Math.min(recoveryAmount, Math.abs(this.recoilOffset.x));
        const signX = Math.sign(this.recoilOffset.x);
        this.rotation.x += recoverX * signX;
        this.recoilOffset.x -= recoverX * signX;
      }

      // Recover horizontal
      if (Math.abs(this.recoilOffset.y) > 0.001) {
        const recoverY = Math.min(recoveryAmount, Math.abs(this.recoilOffset.y));
        const signY = Math.sign(this.recoilOffset.y);
        this.rotation.y -= recoverY * signY;
        this.recoilOffset.y -= recoverY * signY;
      }
    }

    // Apply recovered rotation to camera
    this.camera.rotation.x = this.rotation.x;
    this.camera.rotation.y = this.rotation.y;
  }

  getPosition(): THREE.Vector3 {
    return this.position.clone();
  }

  /**
   * Take damage (called by enemies)
   */
  takeDamage(amount: number): void {
    this.health.takeDamage(amount);
    this.damageFeedback.flashDamage(0.3);
    this.damageFeedback.triggerShake(0.05);
  }

  /**
   * Respawn player at spawn position
   */
  respawn(): void {
    this.health.respawn();
    this.position.copy(this.spawnPosition);
    this.camera.position.copy(this.position);
    this.velocity.set(0, 0, 0);
    this.damageFeedback.hideDeathScreen();
  }
}
