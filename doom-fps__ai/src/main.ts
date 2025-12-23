import { InputManager } from './utils/Input';
import { CollisionSystem } from './game/Collision';
import { Player } from './game/Player';
import { World } from './game/World';
import { WeaponFactory, WeaponType } from './game/weapons/WeaponFactory';
import { ViewModelRenderer } from './game/viewmodel/ViewModelRenderer';
import { EnemyManager } from './game/enemies/EnemyManager';
import { HUD } from './ui/HUD';

class Game {
  private input: InputManager;
  private collision: CollisionSystem;
  private player: Player;
  private world: World;
  private viewModelRenderer: ViewModelRenderer;
  private enemyManager: EnemyManager;
  private hud: HUD;
  private lastTime = 0;

  constructor() {
    const app = document.getElementById('app');
    if (!app) throw new Error('App container not found');

    // Initialize systems
    this.collision = new CollisionSystem();
    this.world = new World(this.collision, app);
    this.viewModelRenderer = new ViewModelRenderer(this.world.getRenderer());
    this.input = new InputManager(app);
    this.player = new Player(this.input, this.collision, this.world.scene, app);

    // Initialize HUD
    this.hud = new HUD(app);

    // Set view model renderer for weapon manager
    this.player.weaponManager.setViewModelRenderer(this.viewModelRenderer);

    // Initialize enemy manager
    this.enemyManager = new EnemyManager(this.world.scene);
    this.player.weaponManager.setEnemyManager(this.enemyManager);

    // Connect enemy damage to player
    this.enemyManager.setOnPlayerDamage((damage: number) => {
      this.player.takeDamage(damage);
    });

    // Setup health callbacks
    this.player.health.setCallbacks({
      onDamage: (health, maxHealth) => {
        this.hud.updateHealth(health, maxHealth);
      },
      onDeath: () => {
        console.log('Player died!');
        this.hud.showDeathScreen();
        this.player.damageFeedback.showDeathScreen();
      }
    });

    // Setup respawn button
    this.hud.onRespawn(() => {
      this.handleRespawn();
    });

    // Equip default weapons with types
    this.player.weaponManager.addWeapon(
      WeaponFactory.createWeapon(WeaponType.PISTOL),
      WeaponType.PISTOL
    );
    this.player.weaponManager.addWeapon(
      WeaponFactory.createWeapon(WeaponType.RIFLE),
      WeaponType.RIFLE
    );

    // Spawn test enemies
    const spawnPositions = this.world.getEnemySpawnPositions();
    this.enemyManager.spawnEnemies(spawnPositions);

    // Initialize HUD with current values
    this.hud.updateHealth(this.player.health.getHealth(), this.player.health.getMaxHealth());
    this.updateHUDWeaponInfo();

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

  private handleRespawn(): void {
    this.player.respawn();
    this.hud.hideDeathScreen();
    this.hud.updateHealth(this.player.health.getHealth(), this.player.health.getMaxHealth());

    // Respawn enemies
    this.enemyManager.clearAll();
    const spawnPositions = this.world.getEnemySpawnPositions();
    this.enemyManager.spawnEnemies(spawnPositions);

    console.log('Player respawned!');
  }

  private updateHUDWeaponInfo(): void {
    const weapon = this.player.weaponManager.getCurrentWeapon();
    if (weapon) {
      this.hud.updateWeaponName(weapon.getName());
      this.hud.updateAmmo(
        weapon.getCurrentAmmo(),
        weapon.getMaxAmmo(),
        weapon.getIsReloading()
      );
    }
  }

  private gameLoop = (currentTime: number): void => {
    requestAnimationFrame(this.gameLoop);

    // Calculate delta time in seconds
    const deltaTime = Math.min((currentTime - this.lastTime) / 1000, 0.1); // Cap at 100ms
    this.lastTime = currentTime;

    // Update game state
    this.player.update(deltaTime, this.world.scene);

    // Update enemies
    this.enemyManager.update(deltaTime, this.player.getPosition());

    // Update HUD with weapon info
    this.updateHUDWeaponInfo();

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
