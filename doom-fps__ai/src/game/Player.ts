import * as THREE from 'three';
import { InputManager } from '../utils/Input';
import { CollisionSystem } from './Collision';
import { WeaponManager } from './weapons/WeaponManager';

export class Player {
  camera: THREE.PerspectiveCamera;
  weaponManager: WeaponManager;
  private velocity = new THREE.Vector3();
  private position: THREE.Vector3;
  private rotation = { x: 0, y: 0 }; // pitch and yaw
  private onGround = false;

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
    spawnPosition = new THREE.Vector3(0, 2, 0)
  ) {
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

    window.addEventListener('resize', () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
    });
  }

  update(deltaTime: number, scene: THREE.Scene): void {
    if (!this.input.getPointerLocked()) return;

    this.updateRotation();
    this.updateMovement(deltaTime);
    this.updateWeapons(deltaTime, scene);
  }

  private updateWeapons(deltaTime: number, scene: THREE.Scene): void {
    // Handle weapon firing
    if (this.input.isMouseButtonJustPressed(0)) {
      // Left click - fire weapon (semi-auto)
      this.weaponManager.fire(this.camera, scene);
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
    this.weaponManager.update(deltaTime, this.camera, scene, mouseDelta, isMoving);

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

  getPosition(): THREE.Vector3 {
    return this.position.clone();
  }
}
