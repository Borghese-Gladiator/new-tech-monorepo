import * as THREE from 'three';

export enum AnimationState {
  IDLE = 'idle',
  FIRE = 'fire',
  RELOAD = 'reload',
  EQUIP = 'equip'
}

export interface AnimationFrame {
  time: number;           // Time in seconds
  position?: THREE.Vector3;
  rotation?: THREE.Euler;
  scale?: THREE.Vector3;
}

export abstract class AnimationClip {
  protected duration: number;
  protected loop: boolean;
  protected state: AnimationState;

  constructor(state: AnimationState, duration: number, loop = false) {
    this.state = state;
    this.duration = duration;
    this.loop = loop;
  }

  /**
   * Get the animation state
   */
  getState(): AnimationState {
    return this.state;
  }

  /**
   * Get animation duration in seconds
   */
  getDuration(): number {
    return this.duration;
  }

  /**
   * Check if animation should loop
   */
  isLooping(): boolean {
    return this.loop;
  }

  /**
   * Evaluate animation at given time
   * Returns position, rotation, scale offsets
   */
  abstract evaluate(time: number): {
    position: THREE.Vector3;
    rotation: THREE.Euler;
    scale: THREE.Vector3;
  };

  /**
   * Called when animation starts
   */
  onStart(): void {
    // Override in subclasses
  }

  /**
   * Called when animation completes
   */
  onComplete(): void {
    // Override in subclasses
  }

  /**
   * Linear interpolation between two frames
   */
  protected lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }

  /**
   * Ease out cubic interpolation
   */
  protected easeOutCubic(t: number): number {
    return 1 - Math.pow(1 - t, 3);
  }

  /**
   * Ease in cubic interpolation
   */
  protected easeInCubic(t: number): number {
    return t * t * t;
  }

  /**
   * Ease in-out cubic interpolation
   */
  protected easeInOutCubic(t: number): number {
    return t < 0.5
      ? 4 * t * t * t
      : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }
}
