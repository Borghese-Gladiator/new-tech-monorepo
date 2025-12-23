export interface PlayerHealthCallbacks {
  onDamage?: (currentHealth: number, maxHealth: number) => void;
  onDeath?: () => void;
  onHeal?: (currentHealth: number, maxHealth: number) => void;
}

export class PlayerHealth {
  private health: number;
  private maxHealth: number;
  private isDead = false;
  private callbacks: PlayerHealthCallbacks = {};

  constructor(maxHealth = 100) {
    this.maxHealth = maxHealth;
    this.health = maxHealth;
  }

  /**
   * Take damage from enemies or environment
   */
  takeDamage(amount: number): void {
    if (this.isDead) return;

    this.health = Math.max(0, this.health - amount);
    this.callbacks.onDamage?.(this.health, this.maxHealth);

    if (this.health <= 0) {
      this.isDead = true;
      this.callbacks.onDeath?.();
    }
  }

  /**
   * Heal player
   */
  heal(amount: number): void {
    if (this.isDead) return;

    this.health = Math.min(this.maxHealth, this.health + amount);
    this.callbacks.onHeal?.(this.health, this.maxHealth);
  }

  /**
   * Respawn player at full health
   */
  respawn(): void {
    this.health = this.maxHealth;
    this.isDead = false;
  }

  /**
   * Set event callbacks
   */
  setCallbacks(callbacks: PlayerHealthCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  // Getters
  getHealth(): number {
    return this.health;
  }

  getMaxHealth(): number {
    return this.maxHealth;
  }

  getHealthPercent(): number {
    return this.health / this.maxHealth;
  }

  getIsDead(): boolean {
    return this.isDead;
  }
}
