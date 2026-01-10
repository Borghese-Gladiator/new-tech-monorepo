import * as THREE from 'three';
import { EnemyManager } from './EnemyManager';

interface WaveConfig {
  enemyCount: number;
  spawnInterval: number; // Time between spawns in seconds
  spawnDelay: number;    // Delay before wave starts
}

export class WaveSpawner {
  private enemyManager: EnemyManager;
  private spawnPositions: THREE.Vector3[];
  private currentWave = 0;
  private enemiesSpawnedThisWave = 0;
  private enemiesKilledThisWave = 0;
  private spawnTimer = 0;
  private waveDelayTimer = 0;
  private isSpawning = false;
  private waveActive = false;

  // Difficulty scaling
  private readonly BASE_ENEMY_COUNT = 3;
  private readonly ENEMY_COUNT_INCREMENT = 2; // +2 enemies per wave
  private readonly BASE_SPAWN_INTERVAL = 2.0; // 2 seconds between spawns
  private readonly MIN_SPAWN_INTERVAL = 0.5;  // Minimum 0.5s between spawns
  private readonly SPAWN_INTERVAL_DECREASE = 0.1; // -0.1s per wave
  private readonly WAVE_DELAY = 5.0; // 5 seconds between waves

  // Callbacks
  private onWaveStartCallback?: (wave: number, enemyCount: number) => void;
  private onWaveCompleteCallback?: (wave: number) => void;
  private onEnemySpawnedCallback?: (remaining: number) => void;

  constructor(enemyManager: EnemyManager, spawnPositions: THREE.Vector3[]) {
    this.enemyManager = enemyManager;
    this.spawnPositions = spawnPositions;
  }

  /**
   * Start the spawn system
   */
  start(): void {
    this.startNextWave();
  }

  /**
   * Update spawn timers
   */
  update(deltaTime: number): void {
    // Handle wave delay
    if (this.waveDelayTimer > 0) {
      this.waveDelayTimer -= deltaTime;
      if (this.waveDelayTimer <= 0) {
        console.log(`Wave delay finished, beginning spawn for wave ${this.currentWave}`);
        this.beginSpawning();
      }
      return;
    }

    // Check if wave is complete (only after all enemies have been spawned)
    if (this.waveActive && !this.isSpawning && this.enemiesSpawnedThisWave > 0) {
      const enemiesAlive = this.enemyManager.getEnemyCount();
      if (enemiesAlive === 0) {
        this.completeWave();
      }
    }

    // Handle spawning
    if (this.isSpawning) {
      const waveConfig = this.getCurrentWaveConfig();

      // Spawn first enemy immediately, then use interval for rest
      if (this.enemiesSpawnedThisWave === 0) {
        this.spawnEnemy();
        console.log(`Spawned enemy ${this.enemiesSpawnedThisWave}/${waveConfig.enemyCount}`);
        this.spawnTimer = 0;

        // Check if only 1 enemy in wave
        if (this.enemiesSpawnedThisWave >= waveConfig.enemyCount) {
          this.isSpawning = false;
          console.log(`Wave ${this.currentWave}: All enemies spawned!`);
        }
      } else {
        // Spawn remaining enemies at intervals
        this.spawnTimer += deltaTime;

        if (this.spawnTimer >= waveConfig.spawnInterval) {
          this.spawnTimer = 0;
          this.spawnEnemy();
          console.log(`Spawned enemy ${this.enemiesSpawnedThisWave}/${waveConfig.enemyCount}`);

          // Check if all enemies spawned
          if (this.enemiesSpawnedThisWave >= waveConfig.enemyCount) {
            this.isSpawning = false;
            console.log(`Wave ${this.currentWave}: All enemies spawned!`);
          }
        }
      }
    }
  }

  /**
   * Start next wave
   */
  private startNextWave(): void {
    this.currentWave++;
    this.enemiesSpawnedThisWave = 0;
    this.enemiesKilledThisWave = 0;
    this.spawnTimer = 0;
    this.waveActive = true;

    const waveConfig = this.getCurrentWaveConfig();

    console.log(`\n=== WAVE ${this.currentWave} ===`);
    console.log(`Enemies: ${waveConfig.enemyCount}`);
    console.log(`Spawn Rate: ${waveConfig.spawnInterval.toFixed(1)}s`);
    console.log(`Starting in ${this.WAVE_DELAY}s...`);

    this.onWaveStartCallback?.(this.currentWave, waveConfig.enemyCount);

    // Start wave delay
    this.waveDelayTimer = waveConfig.spawnDelay;
  }

  /**
   * Begin spawning enemies
   */
  private beginSpawning(): void {
    this.isSpawning = true;
    this.spawnTimer = 0; // Reset spawn timer
    console.log(`Wave ${this.currentWave} spawning started! isSpawning=${this.isSpawning}`);
  }

  /**
   * Spawn a single enemy
   */
  private spawnEnemy(): void {
    // Pick random spawn position
    const spawnPos = this.spawnPositions[
      Math.floor(Math.random() * this.spawnPositions.length)
    ];

    this.enemyManager.spawnEnemy(spawnPos.clone());
    this.enemiesSpawnedThisWave++;

    const waveConfig = this.getCurrentWaveConfig();
    const remaining = waveConfig.enemyCount - this.enemiesSpawnedThisWave;
    this.onEnemySpawnedCallback?.(remaining);
  }

  /**
   * Complete current wave
   */
  private completeWave(): void {
    this.waveActive = false;
    console.log(`\n=== WAVE ${this.currentWave} COMPLETE ===\n`);
    this.onWaveCompleteCallback?.(this.currentWave);

    // Start next wave after delay
    this.startNextWave();
  }

  /**
   * Get configuration for current wave (with difficulty scaling)
   */
  private getCurrentWaveConfig(): WaveConfig {
    // Scale enemy count: 3, 5, 7, 9, 11...
    const enemyCount = this.BASE_ENEMY_COUNT + (this.currentWave - 1) * this.ENEMY_COUNT_INCREMENT;

    // Scale spawn interval: 2.0, 1.9, 1.8... (min 0.5)
    const spawnInterval = Math.max(
      this.MIN_SPAWN_INTERVAL,
      this.BASE_SPAWN_INTERVAL - (this.currentWave - 1) * this.SPAWN_INTERVAL_DECREASE
    );

    return {
      enemyCount,
      spawnInterval,
      spawnDelay: this.WAVE_DELAY
    };
  }

  /**
   * Set callbacks
   */
  setCallbacks(callbacks: {
    onWaveStart?: (wave: number, enemyCount: number) => void;
    onWaveComplete?: (wave: number) => void;
    onEnemySpawned?: (remaining: number) => void;
  }): void {
    this.onWaveStartCallback = callbacks.onWaveStart;
    this.onWaveCompleteCallback = callbacks.onWaveComplete;
    this.onEnemySpawnedCallback = callbacks.onEnemySpawned;
  }

  /**
   * Get current wave number
   */
  getCurrentWave(): number {
    return this.currentWave;
  }

  /**
   * Get time until next wave starts
   */
  getWaveDelayRemaining(): number {
    return Math.max(0, this.waveDelayTimer);
  }

  /**
   * Check if currently between waves
   */
  isInWaveDelay(): boolean {
    return this.waveDelayTimer > 0;
  }

  /**
   * Get enemies remaining to spawn this wave
   */
  getEnemiesRemainingToSpawn(): number {
    const waveConfig = this.getCurrentWaveConfig();
    return waveConfig.enemyCount - this.enemiesSpawnedThisWave;
  }

  /**
   * Reset spawn system
   */
  reset(): void {
    this.currentWave = 0;
    this.enemiesSpawnedThisWave = 0;
    this.spawnTimer = 0;
    this.waveDelayTimer = 0;
    this.isSpawning = false;
    this.waveActive = false;
  }
}
