import { Weapon } from '../game/weapons/Weapon';

export class HUD {
  private container: HTMLDivElement;
  private healthBar: HTMLDivElement;
  private healthText: HTMLSpanElement;
  private healthIcon: HTMLDivElement;
  private ammoText: HTMLDivElement;
  private weaponNameText: HTMLDivElement;
  private crosshair: HTMLDivElement;
  private deathScreen: HTMLDivElement;
  private respawnButton: HTMLButtonElement;
  private waveDisplay: HTMLDivElement;
  private waveCountdownDisplay: HTMLDivElement;
  private waveStartTimer = 0;
  private showingWaveStart = false;
  private lowHealthPulse = 0;

  constructor(parentContainer: HTMLElement) {
    // Create HUD container - DOOM style
    this.container = document.createElement('div');
    this.container.style.position = 'fixed';
    this.container.style.top = '0';
    this.container.style.left = '0';
    this.container.style.width = '100%';
    this.container.style.height = '100%';
    this.container.style.pointerEvents = 'none';
    this.container.style.fontFamily = '"Press Start 2P", "Courier New", monospace';
    this.container.style.color = '#cc0000';
    this.container.style.zIndex = '10';
    this.container.style.textTransform = 'uppercase';
    parentContainer.appendChild(this.container);

    // Create health bar (top-left) - DOOM style
    const healthContainer = document.createElement('div');
    healthContainer.style.position = 'absolute';
    healthContainer.style.top = '20px';
    healthContainer.style.left = '20px';
    healthContainer.style.display = 'flex';
    healthContainer.style.alignItems = 'center';
    healthContainer.style.gap = '10px';
    this.container.appendChild(healthContainer);

    // Skull icon
    this.healthIcon = document.createElement('div');
    this.healthIcon.innerHTML = '💀';
    this.healthIcon.style.fontSize = '28px';
    this.healthIcon.style.filter = 'drop-shadow(2px 2px 4px rgba(0,0,0,0.9))';
    healthContainer.appendChild(this.healthIcon);

    const healthBarContainer = document.createElement('div');
    healthContainer.appendChild(healthBarContainer);

    const healthLabel = document.createElement('div');
    healthLabel.textContent = 'VITALITY';
    healthLabel.style.fontSize = '10px';
    healthLabel.style.marginBottom = '4px';
    healthLabel.style.color = '#aa0000';
    healthLabel.style.textShadow = '2px 2px 4px rgba(0,0,0,0.9)';
    healthLabel.style.letterSpacing = '2px';
    healthBarContainer.appendChild(healthLabel);

    // Health bar background - demonic style
    const healthBarBg = document.createElement('div');
    healthBarBg.style.width = '200px';
    healthBarBg.style.height = '20px';
    healthBarBg.style.backgroundColor = 'rgba(20, 0, 0, 0.8)';
    healthBarBg.style.border = '2px solid #660000';
    healthBarBg.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.3), inset 0 0 10px rgba(0, 0, 0, 0.5)';
    healthBarBg.style.position = 'relative';
    healthBarContainer.appendChild(healthBarBg);

    // Health bar fill - blood red gradient
    this.healthBar = document.createElement('div');
    this.healthBar.style.width = '100%';
    this.healthBar.style.height = '100%';
    this.healthBar.style.background = 'linear-gradient(180deg, #cc0000 0%, #880000 50%, #660000 100%)';
    this.healthBar.style.transition = 'width 0.2s ease-out';
    this.healthBar.style.boxShadow = '0 0 8px rgba(255, 0, 0, 0.5)';
    healthBarBg.appendChild(this.healthBar);

    // Health text
    this.healthText = document.createElement('span');
    this.healthText.style.position = 'absolute';
    this.healthText.style.top = '50%';
    this.healthText.style.left = '50%';
    this.healthText.style.transform = 'translate(-50%, -50%)';
    this.healthText.style.fontSize = '12px';
    this.healthText.style.fontWeight = 'bold';
    this.healthText.style.color = '#ffcccc';
    this.healthText.style.textShadow = '1px 1px 2px rgba(0,0,0,1)';
    this.healthText.textContent = '100';
    healthBarBg.appendChild(this.healthText);

    // Create ammo counter (bottom-right) - DOOM style
    this.ammoText = document.createElement('div');
    this.ammoText.style.position = 'absolute';
    this.ammoText.style.bottom = '80px';
    this.ammoText.style.right = '20px';
    this.ammoText.style.fontSize = '42px';
    this.ammoText.style.fontWeight = 'bold';
    this.ammoText.style.color = '#ff4444';
    this.ammoText.style.textShadow = '0 0 10px rgba(255, 0, 0, 0.5), 3px 3px 6px rgba(0,0,0,1)';
    this.ammoText.textContent = '15';
    this.container.appendChild(this.ammoText);

    // Create weapon name (bottom-right, above ammo) - demonic names
    this.weaponNameText = document.createElement('div');
    this.weaponNameText.style.position = 'absolute';
    this.weaponNameText.style.bottom = '50px';
    this.weaponNameText.style.right = '20px';
    this.weaponNameText.style.fontSize = '14px';
    this.weaponNameText.style.color = '#aa4444';
    this.weaponNameText.style.textShadow = '2px 2px 4px rgba(0,0,0,0.9)';
    this.weaponNameText.style.letterSpacing = '1px';
    this.weaponNameText.textContent = 'HELLFIRE PISTOL';
    this.container.appendChild(this.weaponNameText);

    // Create crosshair (center) - aggressive demonic style
    this.crosshair = document.createElement('div');
    this.crosshair.style.position = 'absolute';
    this.crosshair.style.top = '50%';
    this.crosshair.style.left = '50%';
    this.crosshair.style.transform = 'translate(-50%, -50%)';
    this.crosshair.style.width = '20px';
    this.crosshair.style.height = '20px';
    this.crosshair.style.display = 'flex';
    this.crosshair.style.justifyContent = 'center';
    this.crosshair.style.alignItems = 'center';
    this.crosshair.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24">
        <line x1="12" y1="0" x2="12" y2="8" stroke="#ff0000" stroke-width="2"/>
        <line x1="12" y1="16" x2="12" y2="24" stroke="#ff0000" stroke-width="2"/>
        <line x1="0" y1="12" x2="8" y2="12" stroke="#ff0000" stroke-width="2"/>
        <line x1="16" y1="12" x2="24" y2="12" stroke="#ff0000" stroke-width="2"/>
        <circle cx="12" cy="12" r="3" fill="none" stroke="#ff0000" stroke-width="1"/>
      </svg>
    `;
    this.container.appendChild(this.crosshair);

    // Create death screen (hidden initially) - DOOM style
    this.deathScreen = document.createElement('div');
    this.deathScreen.style.position = 'absolute';
    this.deathScreen.style.top = '0';
    this.deathScreen.style.left = '0';
    this.deathScreen.style.width = '100%';
    this.deathScreen.style.height = '100%';
    this.deathScreen.style.backgroundColor = 'rgba(30, 0, 0, 0.9)';
    this.deathScreen.style.display = 'none';
    this.deathScreen.style.flexDirection = 'column';
    this.deathScreen.style.justifyContent = 'center';
    this.deathScreen.style.alignItems = 'center';
    this.deathScreen.style.pointerEvents = 'all';
    // Blood drip effect at top
    this.deathScreen.style.backgroundImage = 'linear-gradient(180deg, rgba(100, 0, 0, 0.8) 0%, transparent 20%)';
    this.container.appendChild(this.deathScreen);

    const deathTitle = document.createElement('h1');
    deathTitle.textContent = 'SLAUGHTERED';
    deathTitle.style.fontSize = '56px';
    deathTitle.style.color = '#ff0000';
    deathTitle.style.marginBottom = '10px';
    deathTitle.style.textShadow = '0 0 20px rgba(255, 0, 0, 0.8), 4px 4px 8px rgba(0,0,0,1)';
    deathTitle.style.letterSpacing = '4px';
    this.deathScreen.appendChild(deathTitle);

    const deathSubtitle = document.createElement('div');
    deathSubtitle.textContent = 'THE DEMONS CLAIM YOUR SOUL';
    deathSubtitle.style.fontSize = '16px';
    deathSubtitle.style.color = '#aa0000';
    deathSubtitle.style.marginBottom = '40px';
    deathSubtitle.style.textShadow = '2px 2px 4px rgba(0,0,0,1)';
    this.deathScreen.appendChild(deathSubtitle);

    this.respawnButton = document.createElement('button');
    this.respawnButton.textContent = 'RISE AGAIN';
    this.respawnButton.style.fontSize = '20px';
    this.respawnButton.style.padding = '15px 40px';
    this.respawnButton.style.backgroundColor = '#220000';
    this.respawnButton.style.color = '#ff4444';
    this.respawnButton.style.border = '2px solid #660000';
    this.respawnButton.style.cursor = 'pointer';
    this.respawnButton.style.fontFamily = '"Press Start 2P", "Courier New", monospace';
    this.respawnButton.style.transition = 'all 0.2s';
    this.respawnButton.style.textShadow = '0 0 10px rgba(255, 0, 0, 0.5)';
    this.respawnButton.style.boxShadow = '0 0 15px rgba(255, 0, 0, 0.3)';
    this.respawnButton.addEventListener('mouseenter', () => {
      this.respawnButton.style.backgroundColor = '#440000';
      this.respawnButton.style.boxShadow = '0 0 25px rgba(255, 0, 0, 0.6)';
    });
    this.respawnButton.addEventListener('mouseleave', () => {
      this.respawnButton.style.backgroundColor = '#220000';
      this.respawnButton.style.boxShadow = '0 0 15px rgba(255, 0, 0, 0.3)';
    });
    this.deathScreen.appendChild(this.respawnButton);

    // Create wave display (top-center) - DOOM style
    this.waveDisplay = document.createElement('div');
    this.waveDisplay.style.position = 'absolute';
    this.waveDisplay.style.top = '20px';
    this.waveDisplay.style.left = '50%';
    this.waveDisplay.style.transform = 'translateX(-50%)';
    this.waveDisplay.style.fontSize = '20px';
    this.waveDisplay.style.fontWeight = 'bold';
    this.waveDisplay.style.color = '#ff2200';
    this.waveDisplay.style.textShadow = '0 0 10px rgba(255, 0, 0, 0.5), 3px 3px 6px rgba(0,0,0,1)';
    this.waveDisplay.style.letterSpacing = '2px';
    this.waveDisplay.textContent = 'DEMON WAVE 1';
    this.container.appendChild(this.waveDisplay);

    // Create wave countdown display (center, large) - DOOM style
    this.waveCountdownDisplay = document.createElement('div');
    this.waveCountdownDisplay.style.position = 'absolute';
    this.waveCountdownDisplay.style.top = '40%';
    this.waveCountdownDisplay.style.left = '50%';
    this.waveCountdownDisplay.style.transform = 'translate(-50%, -50%)';
    this.waveCountdownDisplay.style.fontSize = '64px';
    this.waveCountdownDisplay.style.fontWeight = 'bold';
    this.waveCountdownDisplay.style.color = '#ff2200';
    this.waveCountdownDisplay.style.textShadow = '0 0 20px rgba(255, 0, 0, 0.7), 4px 4px 8px rgba(0,0,0,1)';
    this.waveCountdownDisplay.style.display = 'none';
    this.waveCountdownDisplay.style.letterSpacing = '3px';
    this.container.appendChild(this.waveCountdownDisplay);
  }

  /**
   * Update health bar - DOOM style colors
   */
  updateHealth(current: number, max: number): void {
    const percent = (current / max) * 100;
    this.healthBar.style.width = `${percent}%`;
    this.healthText.textContent = `${Math.ceil(current)}`;

    // Always blood red, but darker when low
    if (percent > 60) {
      this.healthBar.style.background = 'linear-gradient(180deg, #cc0000 0%, #880000 50%, #660000 100%)';
      this.healthIcon.style.transform = 'scale(1)';
    } else if (percent > 30) {
      this.healthBar.style.background = 'linear-gradient(180deg, #aa0000 0%, #660000 50%, #440000 100%)';
      this.healthIcon.style.transform = 'scale(1.1)';
    } else {
      this.healthBar.style.background = 'linear-gradient(180deg, #880000 0%, #440000 50%, #220000 100%)';
      this.healthIcon.style.transform = 'scale(1.2)';
    }
  }

  /**
   * Update ammo display - DOOM style
   */
  updateAmmo(current: number, max: number, isReloading: boolean): void {
    if (isReloading) {
      this.ammoText.textContent = 'RELOAD';
      this.ammoText.style.color = '#ffaa00';
      this.ammoText.style.fontSize = '32px';
    } else {
      this.ammoText.textContent = `${current}`;
      this.ammoText.style.fontSize = '42px';
      this.ammoText.style.color = current === 0 ? '#ff0000' : '#ff4444';
    }
  }

  /**
   * Update weapon name - demonic names
   */
  updateWeaponName(name: string): void {
    const demonicNames: Record<string, string> = {
      'pistol': 'HELLFIRE PISTOL',
      'rifle': 'DEMON RIFLE'
    };
    this.weaponNameText.textContent = demonicNames[name.toLowerCase()] || name.toUpperCase();
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
   * Update wave number - DOOM style
   */
  updateWave(wave: number, enemyCount: number): void {
    this.waveDisplay.textContent = `DEMON WAVE ${wave}`;
  }

  /**
   * Show wave countdown - DOOM style
   */
  showWaveCountdown(seconds: number): void {
    // Don't show countdown if showing wave start
    if (this.showingWaveStart) return;

    if (seconds > 0 && seconds <= 5) {
      this.waveCountdownDisplay.textContent = `DEMONS INCOMING: ${Math.ceil(seconds)}`;
      this.waveCountdownDisplay.style.display = 'block';
      this.waveCountdownDisplay.style.color = '#ff4400';
      this.waveCountdownDisplay.style.fontSize = '48px';
    } else {
      this.waveCountdownDisplay.style.display = 'none';
    }
  }

  /**
   * Show wave start message - DOOM style
   */
  showWaveStart(wave: number): void {
    this.waveCountdownDisplay.textContent = `WAVE ${wave} - KILL THEM ALL`;
    this.waveCountdownDisplay.style.display = 'block';
    this.waveCountdownDisplay.style.color = '#ff0000';
    this.waveCountdownDisplay.style.fontSize = '48px';
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
        this.showingWaveStart = false;
      }
    }

    // Low health pulse effect
    const healthPercent = parseFloat(this.healthBar.style.width) || 100;
    if (healthPercent <= 30) {
      this.lowHealthPulse += deltaTime * 4;
      const pulse = Math.sin(this.lowHealthPulse) * 0.3 + 0.7;
      this.healthBar.style.opacity = `${pulse}`;
      this.healthIcon.style.opacity = `${pulse}`;
    } else {
      this.healthBar.style.opacity = '1';
      this.healthIcon.style.opacity = '1';
      this.lowHealthPulse = 0;
    }
  }

  /**
   * Clean up
   */
  dispose(): void {
    this.container.remove();
  }
}
