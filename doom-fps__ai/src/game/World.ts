import * as THREE from 'three';
import { CollisionSystem } from './Collision';

export class World {
  scene: THREE.Scene;
  private renderer: THREE.WebGLRenderer;

  constructor(
    private collision: CollisionSystem,
    container: HTMLElement
  ) {
    // Create scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x87ceeb); // Sky blue
    this.scene.fog = new THREE.Fog(0x87ceeb, 0, 100);

    // Create renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.prepend(this.renderer.domElement);

    // Handle resize
    window.addEventListener('resize', () => {
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    });

    this.createLevel();
  }

  private createLevel(): void {
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);

    // Add directional light (sun)
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 100, 50);
    directionalLight.castShadow = true;
    directionalLight.shadow.camera.left = -50;
    directionalLight.shadow.camera.right = 50;
    directionalLight.shadow.camera.top = 50;
    directionalLight.shadow.camera.bottom = -50;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    this.scene.add(directionalLight);

    // Create ground
    const groundSize = 50;
    const groundGeometry = new THREE.BoxGeometry(groundSize, 1, groundSize);
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: 0x3a8c3a,
      roughness: 0.8
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.position.y = -0.5;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Add ground collision
    this.collision.addCollider({
      min: new THREE.Vector3(-groundSize / 2, -1, -groundSize / 2),
      max: new THREE.Vector3(groundSize / 2, 0, groundSize / 2)
    });

    // Create test walls/obstacles
    this.createWall(10, 0, -10, 4, 3, 1, 0x8b4513); // Brown wall
    this.createWall(-10, 0, 10, 1, 3, 4, 0x8b4513);
    this.createWall(5, 0, 5, 2, 2, 2, 0xdc143c); // Red cube

    // Create platform
    this.createPlatform(15, 2, 0, 6, 0.5, 6, 0x666666);

    // Create boundary walls
    const boundaryHeight = 5;
    const halfSize = groundSize / 2;

    // North wall
    this.createWall(0, 0, -halfSize, groundSize, boundaryHeight, 1, 0x808080);
    // South wall
    this.createWall(0, 0, halfSize, groundSize, boundaryHeight, 1, 0x808080);
    // East wall
    this.createWall(halfSize, 0, 0, 1, boundaryHeight, groundSize, 0x808080);
    // West wall
    this.createWall(-halfSize, 0, 0, 1, boundaryHeight, groundSize, 0x808080);
  }

  /**
   * Get enemy spawn positions in the level
   */
  getEnemySpawnPositions(): THREE.Vector3[] {
    return [
      new THREE.Vector3(10, 0, 10),
      new THREE.Vector3(-10, 0, -10),
      new THREE.Vector3(15, 0, -5),
      new THREE.Vector3(-15, 0, 5),
      new THREE.Vector3(0, 0, -15)
    ];
  }

  private createWall(
    x: number,
    y: number,
    z: number,
    width: number,
    height: number,
    depth: number,
    color: number
  ): void {
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const material = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.7
    });
    const wall = new THREE.Mesh(geometry, material);
    wall.position.set(x, y + height / 2, z);
    wall.castShadow = true;
    wall.receiveShadow = true;
    this.scene.add(wall);

    // Add collision
    this.collision.addCollider({
      min: new THREE.Vector3(x - width / 2, y, z - depth / 2),
      max: new THREE.Vector3(x + width / 2, y + height, z + depth / 2)
    });
  }

  private createPlatform(
    x: number,
    y: number,
    z: number,
    width: number,
    height: number,
    depth: number,
    color: number
  ): void {
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const material = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.7
    });
    const platform = new THREE.Mesh(geometry, material);
    platform.position.set(x, y, z);
    platform.castShadow = true;
    platform.receiveShadow = true;
    this.scene.add(platform);

    // Add collision
    this.collision.addCollider({
      min: new THREE.Vector3(x - width / 2, y - height / 2, z - depth / 2),
      max: new THREE.Vector3(x + width / 2, y + height / 2, z + depth / 2)
    });
  }

  render(camera: THREE.Camera): void {
    // Clear buffers manually (autoClear disabled for multi-pass rendering)
    this.renderer.clear(true, true, true);
    this.renderer.render(this.scene, camera);
  }

  getRenderer(): THREE.WebGLRenderer {
    return this.renderer;
  }
}
