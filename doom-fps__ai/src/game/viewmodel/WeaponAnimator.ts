import * as THREE from 'three';
import { AnimationClip, AnimationState } from './animations/AnimationClip';
import { IdleAnimation } from './animations/IdleAnimation';
import { FireAnimation } from './animations/FireAnimation';
import { ReloadAnimation } from './animations/ReloadAnimation';

export class WeaponAnimator {
  private currentAnimation: AnimationClip;
  private animationTime = 0;
  private animations: Map<AnimationState, AnimationClip> = new Map();
  private queuedAnimation?: AnimationClip;

  constructor(reloadTime: number, recoilStrength = 0.1) {
    // Register animations
    this.animations.set(AnimationState.IDLE, new IdleAnimation());
    this.animations.set(AnimationState.FIRE, new FireAnimation(recoilStrength));
    this.animations.set(AnimationState.RELOAD, new ReloadAnimation(reloadTime));

    // Start with idle
    this.currentAnimation = this.animations.get(AnimationState.IDLE)!;
  }

  /**
   * Update animation state
   */
  update(deltaTime: number): void {
    this.animationTime += deltaTime;

    // Check if current animation is complete
    if (!this.currentAnimation.isLooping() &&
        this.animationTime >= this.currentAnimation.getDuration()) {

      this.currentAnimation.onComplete();

      // Transition to queued animation or idle
      if (this.queuedAnimation) {
        this.transitionTo(this.queuedAnimation);
        this.queuedAnimation = undefined;
      } else {
        this.transitionTo(this.animations.get(AnimationState.IDLE)!);
      }
    }
  }

  /**
   * Play fire animation
   */
  playFire(): void {
    const fireAnim = this.animations.get(AnimationState.FIRE);
    if (fireAnim) {
      this.transitionTo(fireAnim);
    }
  }

  /**
   * Play reload animation
   */
  playReload(): void {
    const reloadAnim = this.animations.get(AnimationState.RELOAD);
    if (reloadAnim) {
      this.transitionTo(reloadAnim);
    }
  }

  /**
   * Transition to a new animation
   */
  private transitionTo(animation: AnimationClip): void {
    // Can't interrupt reload
    if (this.currentAnimation.getState() === AnimationState.RELOAD &&
        this.animationTime < this.currentAnimation.getDuration()) {
      this.queuedAnimation = animation;
      return;
    }

    this.currentAnimation = animation;
    this.animationTime = 0;
    this.currentAnimation.onStart();
  }

  /**
   * Get current animation frame
   */
  getCurrentFrame(): { position: THREE.Vector3; rotation: THREE.Euler; scale: THREE.Vector3 } {
    return this.currentAnimation.evaluate(this.animationTime);
  }

  /**
   * Get current animation state
   */
  getCurrentState(): AnimationState {
    return this.currentAnimation.getState();
  }

  /**
   * Check if currently playing specific animation
   */
  isPlaying(state: AnimationState): boolean {
    return this.currentAnimation.getState() === state;
  }

  /**
   * Check if animation can be interrupted
   */
  canInterrupt(): boolean {
    return this.currentAnimation.getState() !== AnimationState.RELOAD ||
           this.animationTime >= this.currentAnimation.getDuration();
  }

  /**
   * Update reload animation duration (when weapon changes)
   */
  updateReloadDuration(duration: number): void {
    this.animations.set(AnimationState.RELOAD, new ReloadAnimation(duration));
  }

  /**
   * Update recoil strength (when weapon changes)
   */
  updateRecoilStrength(strength: number): void {
    this.animations.set(AnimationState.FIRE, new FireAnimation(strength));
  }
}
