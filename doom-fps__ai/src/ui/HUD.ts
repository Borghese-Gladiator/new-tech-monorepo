import { Weapon } from '../game/weapons/Weapon';

export class HUD {
  private container: HTMLDivElement;
  private healthBar: HTMLDivElement;
  private healthText: HTMLSpanElement;
  private ammoText: HTMLDivElement;
  private weaponNameText: HTMLDivElement;
  private crosshair: HTMLDivElement;
  private deathScreen: HTMLDivElement;
  private respawnButton: HTMLButtonElement;
  private waveDisplay: HTMLDivElement;
  private waveCountdownDisplay: HTMLDivElement;
  private waveStartTimer = 0;
  private showingWaveStart = false;

  constructor(parentContainer: HTMLElement) {
    // Create HUD container
    this.container = document.createElement('div');
    this.container.style.position = 'fixed';
    this.container.style.top = '0';
    this.container.style.left = '0';
    this.container.style.width = '100%';
    this.container.style.height = '100%';
    this.container.style.pointerEvents = 'none';
    this.container.style.fontFamily = 'monospace';
    this.container.style.color = 'white';
    this.container.style.zIndex = '10';
    parentContainer.appendChild(this.container);

    // Create health bar (top-left)
    const healthContainer = document.createElement('div');
    healthContainer.style.position = 'absolute';
    healthContainer.style.top = '20px';
    healthContainer.style.left = '20px';
    this.container.appendChild(healthContainer);

    const healthLabel = document.createElement('div');
    healthLabel.textContent = 'HEALTH';
    healthLabel.style.fontSize = '12px';
    healthLabel.style.marginBottom = '5px';
    healthLabel.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
    healthContainer.appendChild(healthLabel);

    // Health bar background
    const healthBarBg = document.createElement('div');
    healthBarBg.style.width = '200px';
    healthBarBg.style.height = '20px';
    healthBarBg.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    healthBarBg.style.border = '2px solid rgba(255, 255, 255, 0.3)';
    healthBarBg.style.position = 'relative';
    healthContainer.appendChild(healthBarBg);

    // Health bar fill
    this.healthBar = document.createElement('div');
    this.healthBar.style.width = '100%';
    this.healthBar.style.height = '100%';
    this.healthBar.style.backgroundColor = '#00ff00';
    this.healthBar.style.transition = 'width 0.2s ease-out, background-color 0.2s ease-out';
    healthBarBg.appendChild(this.healthBar);

    // Health text
    this.healthText = document.createElement('span');
    this.healthText.style.position = 'absolute';
    this.healthText.style.top = '50%';
    this.healthText.style.left = '50%';
    this.healthText.style.transform = 'translate(-50%, -50%)';
    this.healthText.style.fontSize = '14px';
    this.healthText.style.fontWeight = 'bold';
    this.healthText.style.textShadow = '1px 1px 2px rgba(0,0,0,0.9)';
    this.healthText.textContent = '100 / 100';
    healthBarBg.appendChild(this.healthText);

    // Create ammo counter (bottom-right)
    this.ammoText = document.createElement('div');
    this.ammoText.style.position = 'absolute';
    this.ammoText.style.bottom = '80px';
    this.ammoText.style.right = '20px';
    this.ammoText.style.fontSize = '36px';
    this.ammoText.style.fontWeight = 'bold';
    this.ammoText.style.textShadow = '3px 3px 6px rgba(0,0,0,0.9)';
    this.ammoText.textContent = '15';
    this.container.appendChild(this.ammoText);

    // Create weapon name (bottom-right, above ammo)
    this.weaponNameText = document.createElement('div');
    this.weaponNameText.style.position = 'absolute';
    this.weaponNameText.style.bottom = '50px';
    this.weaponNameText.style.right = '20px';
    this.weaponNameText.style.fontSize = '16px';
    this.weaponNameText.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
    this.weaponNameText.textContent = 'PISTOL';
    this.container.appendChild(this.weaponNameText);

    // Create crosshair (center)
    this.crosshair = document.createElement('div');
    this.crosshair.style.position = 'absolute';
    this.crosshair.style.top = '50%';
    this.crosshair.style.left = '50%';
    this.crosshair.style.transform = 'translate(-50%, -50%)';
    this.crosshair.style.width = '4px';
    this.crosshair.style.height = '4px';
    this.crosshair.style.backgroundColor = 'white';
    this.crosshair.style.border = '1px solid black';
    this.crosshair.style.borderRadius = '50%';
    this.container.appendChild(this.crosshair);

    // Create death screen (hidden initially)
    this.deathScreen = document.createElement('div');
    this.deathScreen.style.position = 'absolute';
    this.deathScreen.style.top = '0';
    this.deathScreen.style.left = '0';
    this.deathScreen.style.width = '100%';
    this.deathScreen.style.height = '100%';
    this.deathScreen.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    this.deathScreen.style.display = 'none';
    this.deathScreen.style.flexDirection = 'column';
    this.deathScreen.style.justifyContent = 'center';
    this.deathScreen.style.alignItems = 'center';
    this.deathScreen.style.pointerEvents = 'all';
    this.container.appendChild(this.deathScreen);

    const deathTitle = document.createElement('h1');
    deathTitle.textContent = 'YOU DIED';
    deathTitle.style.fontSize = '64px';
    deathTitle.style.color = '#ff0000';
    deathTitle.style.marginBottom = '30px';
    deathTitle.style.textShadow = '4px 4px 8px rgba(0,0,0,1)';
    this.deathScreen.appendChild(deathTitle);

    this.respawnButton = document.createElement('button');
    this.respawnButton.textContent = 'RESPAWN';
    this.respawnButton.style.fontSize = '24px';
    this.respawnButton.style.padding = '15px 40px';
    this.respawnButton.style.backgroundColor = '#333';
    this.respawnButton.style.color = 'white';
    this.respawnButton.style.border = '2px solid white';
    this.respawnButton.style.cursor = 'pointer';
    this.respawnButton.style.fontFamily = 'monospace';
    this.respawnButton.style.transition = 'background-color 0.2s';
    this.respawnButton.addEventListener('mouseenter', () => {
      this.respawnButton.style.backgroundColor = '#555';
    });
    this.respawnButton.addEventListener('mouseleave', () => {
      this.respawnButton.style.backgroundColor = '#333';
    });
    this.deathScreen.appendChild(this.respawnButton);

    // Create wave display (top-center)
    this.waveDisplay = document.createElement('div');
    this.waveDisplay.style.position = 'absolute';
    this.waveDisplay.style.top = '20px';
    this.waveDisplay.style.left = '50%';
    this.waveDisplay.style.transform = 'translateX(-50%)';
    this.waveDisplay.style.fontSize = '24px';
    this.waveDisplay.style.fontWeight = 'bold';
    this.waveDisplay.style.textShadow = '3px 3px 6px rgba(0,0,0,0.9)';
    this.waveDisplay.textContent = 'WAVE 1';
    this.container.appendChild(this.waveDisplay);

    // Create wave countdown display (center, large)
    this.waveCountdownDisplay = document.createElement('div');
    this.waveCountdownDisplay.style.position = 'absolute';
    this.waveCountdownDisplay.style.top = '40%';
    this.waveCountdownDisplay.style.left = '50%';
    this.waveCountdownDisplay.style.transform = 'translate(-50%, -50%)';
    this.waveCountdownDisplay.style.fontSize = '72px';
    this.waveCountdownDisplay.style.fontWeight = 'bold';
    this.waveCountdownDisplay.style.color = '#ffaa00';
    this.waveCountdownDisplay.style.textShadow = '4px 4px 8px rgba(0,0,0,1)';
    this.waveCountdownDisplay.style.display = 'none';
    this.container.appendChild(this.waveCountdownDisplay);
  }

  /**
   * Update health bar
   */
  updateHealth(current: number, max: number): void {
    const percent = (current / max) * 100;
    this.healthBar.style.width = `${percent}%`;
    this.healthText.textContent = `${Math.ceil(current)} / ${max}`;

    // Change color based on health
    if (percent > 60) {
      this.healthBar.style.backgroundColor = '#00ff00'; // Green
    } else if (percent > 30) {
      this.healthBar.style.backgroundColor = '#ffaa00'; // Orange
    } else {
      this.healthBar.style.backgroundColor = '#ff0000'; // Red
    }
  }

  /**
   * Update ammo display
   */
  updateAmmo(current: number, max: number, isReloading: boolean): void {
    if (isReloading) {
      this.ammoText.textContent = 'RELOADING...';
      this.ammoText.style.color = '#ffaa00';
    } else {
      this.ammoText.textContent = `${current}`;
      this.ammoText.style.color = current === 0 ? '#ff0000' : 'white';
    }
  }

  /**
   * Update weapon name
   */
  updateWeaponName(name: string): void {
    this.weaponNameText.textContent = name.toUpperCase();
  }

  /**
   * Show death screen
   */
  showDeathScreen(): void {
    this.deathScreen.style.display = 'flex';
  }

  /**
   * Hide death screen
   */
  hideDeathScreen(): void {
    this.deathScreen.style.display = 'none';
  }

  /**
   * Set respawn button callback
   */
  onRespawn(callback: () => void): void {
    this.respawnButton.addEventListener('click', callback);
  }

  /**
   * Update wave number
   */
  updateWave(wave: number, enemyCount: number): void {
    this.waveDisplay.textContent = `WAVE ${wave}`;
  }

  /**
   * Show wave countdown
   */
  showWaveCountdown(seconds: number): void {
    // Don't show countdown if showing wave start
    if (this.showingWaveStart) return;

    if (seconds > 0 && seconds <= 5) {
      this.waveCountdownDisplay.textContent = `Next Wave: ${Math.ceil(seconds)}`;
      this.waveCountdownDisplay.style.display = 'block';
      this.waveCountdownDisplay.style.color = '#ffaa00';
    } else {
      this.waveCountdownDisplay.style.display = 'none';
    }
  }

  /**
   * Show wave start message
   */
  showWaveStart(wave: number): void {
    this.waveCountdownDisplay.textContent = `WAVE ${wave}`;
    this.waveCountdownDisplay.style.display = 'block';
    this.waveCountdownDisplay.style.color = '#ff0000';
    this.showingWaveStart = true;
    this.waveStartTimer = 2.0; // Show for 2 seconds
  }

  /**
   * Update HUD timers (call every frame)
   */
  update(deltaTime: number): void {
    if (this.showingWaveStart && this.waveStartTimer > 0) {
      this.waveStartTimer -= deltaTime;
      if (this.waveStartTimer <= 0) {
        this.waveCountdownDisplay.style.display = 'none';
        this.waveCountdownDisplay.style.color = '#ffaa00';
        this.showingWaveStart = false;
      }
    }
  }

  /**
   * Clean up
   */
  dispose(): void {
    this.container.remove();
  }
}
