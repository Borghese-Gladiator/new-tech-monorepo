import { InputManager } from './utils/Input';
import { CollisionSystem } from './game/Collision';
import { Player } from './game/Player';
import { World } from './game/World';
import { WeaponFactory, WeaponType } from './game/weapons/WeaponFactory';
import { ViewModelRenderer } from './game/viewmodel/ViewModelRenderer';

class Game {
  private input: InputManager;
  private collision: CollisionSystem;
  private player: Player;
  private world: World;
  private viewModelRenderer: ViewModelRenderer;
  private lastTime = 0;

  constructor() {
    const app = document.getElementById('app');
    if (!app) throw new Error('App container not found');

    // Initialize systems
    this.collision = new CollisionSystem();
    this.world = new World(this.collision, app);
    this.viewModelRenderer = new ViewModelRenderer(this.world.getRenderer());
    this.input = new InputManager(app);
    this.player = new Player(this.input, this.collision, this.world.scene);

    // Set view model scene for weapon manager
    this.player.weaponManager.setViewModelScene(this.viewModelRenderer.getScene());

    // Equip default weapons with types
    this.player.weaponManager.addWeapon(
      WeaponFactory.createWeapon(WeaponType.PISTOL),
      WeaponType.PISTOL
    );
    this.player.weaponManager.addWeapon(
      WeaponFactory.createWeapon(WeaponType.RIFLE),
      WeaponType.RIFLE
    );

    console.log('=== Browser FPS Ready ===');
    console.log('Controls:');
    console.log('  WASD - Move');
    console.log('  Space - Jump');
    console.log('  Mouse - Look');
    console.log('  Left Click - Fire');
    console.log('  R - Reload');
    console.log('  1/2 - Switch Weapons');
    console.log('========================');

    // Start game loop
    this.lastTime = performance.now();
    this.gameLoop(this.lastTime);
  }

  private gameLoop = (currentTime: number): void => {
    requestAnimationFrame(this.gameLoop);

    // Calculate delta time in seconds
    const deltaTime = Math.min((currentTime - this.lastTime) / 1000, 0.1); // Cap at 100ms
    this.lastTime = currentTime;

    // Update game state
    this.player.update(deltaTime, this.world.scene);

    // Update view model camera to match player camera
    this.viewModelRenderer.updateCamera(this.player.camera);

    // Render world first
    this.world.render(this.player.camera);

    // Render weapon on top
    this.viewModelRenderer.render();
  };
}

// Start the game
new Game();
