import * as THREE from 'three';
import { CollisionSystem } from './Collision';

export class World {
  scene: THREE.Scene;
  private renderer: THREE.WebGLRenderer;
  private torchLights: THREE.PointLight[] = [];

  constructor(
    private collision: CollisionSystem,
    container: HTMLElement
  ) {
    // Create scene - DOOM hellscape
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1a0000); // Dark blood red sky
    this.scene.fog = new THREE.Fog(0x0a0000, 5, 40); // Dense hellish fog

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
    // Dim red ambient light for hellish atmosphere
    const ambientLight = new THREE.AmbientLight(0x331111, 0.3);
    this.scene.add(ambientLight);

    // Dim red directional light (blood moon)
    const directionalLight = new THREE.DirectionalLight(0x992222, 0.4);
    directionalLight.position.set(50, 100, 50);
    directionalLight.castShadow = true;
    directionalLight.shadow.camera.left = -50;
    directionalLight.shadow.camera.right = 50;
    directionalLight.shadow.camera.top = 50;
    directionalLight.shadow.camera.bottom = -50;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    this.scene.add(directionalLight);

    // Create hellish ground
    const groundSize = 50;
    const groundGeometry = new THREE.BoxGeometry(groundSize, 1, groundSize);
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a0808, // Dark blood stone
      roughness: 0.9,
      metalness: 0.1
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

    // Create demonic walls/obstacles
    this.createWall(10, 0, -10, 4, 3, 1, 0x1a1a1a); // Dark metal wall
    this.createWall(-10, 0, 10, 1, 3, 4, 0x1a1a1a);
    this.createWall(5, 0, 5, 2, 2, 2, 0x2a0a0a); // Blood cube

    // Create platform
    this.createPlatform(15, 2, 0, 6, 0.5, 6, 0x222222);

    // Create boundary walls - dark demonic metal
    const boundaryHeight = 5;
    const halfSize = groundSize / 2;

    this.createWall(0, 0, -halfSize, groundSize, boundaryHeight, 1, 0x151515);
    this.createWall(0, 0, halfSize, groundSize, boundaryHeight, 1, 0x151515);
    this.createWall(halfSize, 0, 0, 1, boundaryHeight, groundSize, 0x151515);
    this.createWall(-halfSize, 0, 0, 1, boundaryHeight, groundSize, 0x151515);

    // Add hellfire torch lights
    this.createTorch(-15, 3, -15);
    this.createTorch(15, 3, -15);
    this.createTorch(-15, 3, 15);
    this.createTorch(15, 3, 15);
    this.createTorch(0, 3, 0); // Center torch

    // Add demonic pillars
    this.createDemonicPillar(-8, 0, -8);
    this.createDemonicPillar(8, 0, -8);
    this.createDemonicPillar(-8, 0, 8);
    this.createDemonicPillar(8, 0, 8);

    // Add lava pools
    this.createLavaPool(-18, 0, 0, 3);
    this.createLavaPool(18, 0, 0, 3);
    this.createLavaPool(0, 0, 18, 4);
  }

  private createTorch(x: number, y: number, z: number): void {
    // Flickering point light
    const torchLight = new THREE.PointLight(0xff4400, 1.5, 15);
    torchLight.position.set(x, y, z);
    torchLight.castShadow = true;
    this.scene.add(torchLight);
    this.torchLights.push(torchLight);

    // Torch flame visual (emissive sphere)
    const flameGeometry = new THREE.SphereGeometry(0.15, 8, 8);
    const flameMaterial = new THREE.MeshBasicMaterial({
      color: 0xff6600,
      transparent: true,
      opacity: 0.9
    });
    const flame = new THREE.Mesh(flameGeometry, flameMaterial);
    flame.position.set(x, y, z);
    this.scene.add(flame);

    // Torch base
    const baseGeometry = new THREE.CylinderGeometry(0.1, 0.15, 2, 8);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a1a0a,
      roughness: 0.9
    });
    const base = new THREE.Mesh(baseGeometry, baseMaterial);
    base.position.set(x, y - 1, z);
    this.scene.add(base);
  }

  private createDemonicPillar(x: number, y: number, z: number): void {
    // Main pillar body
    const pillarGeometry = new THREE.CylinderGeometry(0.5, 0.6, 4, 8);
    const pillarMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.7,
      metalness: 0.3
    });
    const pillar = new THREE.Mesh(pillarGeometry, pillarMaterial);
    pillar.position.set(x, y + 2, z);
    pillar.castShadow = true;
    pillar.receiveShadow = true;
    this.scene.add(pillar);

    // Glowing demonic rune ring
    const runeGeometry = new THREE.TorusGeometry(0.55, 0.05, 8, 16);
    const runeMaterial = new THREE.MeshBasicMaterial({
      color: 0xff2200,
      transparent: true,
      opacity: 0.8
    });
    const rune = new THREE.Mesh(runeGeometry, runeMaterial);
    rune.position.set(x, y + 2.5, z);
    rune.rotation.x = Math.PI / 2;
    this.scene.add(rune);

    // Skull on top
    const skullGeometry = new THREE.SphereGeometry(0.3, 8, 8);
    const skullMaterial = new THREE.MeshStandardMaterial({
      color: 0xccbbaa,
      roughness: 0.8
    });
    const skull = new THREE.Mesh(skullGeometry, skullMaterial);
    skull.position.set(x, y + 4.3, z);
    skull.scale.set(1, 0.9, 0.8);
    this.scene.add(skull);

    // Glowing eye sockets
    const eyeMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const eyeGeometry = new THREE.SphereGeometry(0.06, 6, 6);

    const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    leftEye.position.set(x - 0.1, y + 4.35, z + 0.2);
    this.scene.add(leftEye);

    const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEye.position.set(x + 0.1, y + 4.35, z + 0.2);
    this.scene.add(rightEye);

    // Add collision for pillar
    this.collision.addCollider({
      min: new THREE.Vector3(x - 0.6, y, z - 0.6),
      max: new THREE.Vector3(x + 0.6, y + 4.5, z + 0.6)
    });
  }

  private createLavaPool(x: number, y: number, z: number, radius: number): void {
    const lavaGeometry = new THREE.CircleGeometry(radius, 16);
    const lavaMaterial = new THREE.MeshBasicMaterial({
      color: 0xff4400,
      transparent: true,
      opacity: 0.9
    });
    const lava = new THREE.Mesh(lavaGeometry, lavaMaterial);
    lava.position.set(x, y + 0.01, z);
    lava.rotation.x = -Math.PI / 2;
    this.scene.add(lava);

    // Add point light for lava glow
    const lavaLight = new THREE.PointLight(0xff2200, 0.8, 8);
    lavaLight.position.set(x, y + 0.5, z);
    this.scene.add(lavaLight);
  }

  updateTorchFlicker(deltaTime: number): void {
    // Animate torch light flickering
    for (const light of this.torchLights) {
      light.intensity = 1.2 + Math.random() * 0.6;
    }
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
