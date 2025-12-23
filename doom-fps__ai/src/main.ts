import { InputManager } from './utils/Input';
import { CollisionSystem } from './game/Collision';
import { Player } from './game/Player';
import { World } from './game/World';
import { WeaponFactory, WeaponType } from './game/weapons/WeaponFactory';
import { ViewModelRenderer } from './game/viewmodel/ViewModelRenderer';
import { EnemyManager } from './game/enemies/EnemyManager';
import { WaveSpawner } from './game/enemies/WaveSpawner';
import { HUD } from './ui/HUD';

class Game {
  private input: InputManager;
  private collision: CollisionSystem;
  private player: Player;
  private world: World;
  private viewModelRenderer: ViewModelRenderer;
  private enemyManager: EnemyManager;
  private waveSpawner: WaveSpawner;
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

    // Setup wave spawner
    const spawnPositions = this.world.getEnemySpawnPositions();
    this.waveSpawner = new WaveSpawner(this.enemyManager, spawnPositions);

    // Setup wave callbacks
    this.waveSpawner.setCallbacks({
      onWaveStart: (wave, enemyCount) => {
        console.log(`Wave ${wave} starting with ${enemyCount} enemies!`);
        this.hud.updateWave(wave, enemyCount);
        this.hud.showWaveStart(wave);
      },
      onWaveComplete: (wave) => {
        console.log(`Wave ${wave} completed!`);
      }
    });

    // Start wave spawning
    this.waveSpawner.start();

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

    // Reset wave spawner and restart
    this.enemyManager.clearAll();
    this.waveSpawner.reset();
    this.waveSpawner.start();

    console.log('Player respawned! Restarting waves...');
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

    // Update wave spawner
    this.waveSpawner.update(deltaTime);

    // Update HUD with weapon info
    this.updateHUDWeaponInfo();

    // Update HUD timers (for wave start text fadeout)
    this.hud.update(deltaTime);

    // Update wave countdown display (always call to handle hiding)
    this.hud.showWaveCountdown(this.waveSpawner.getWaveDelayRemaining());

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
