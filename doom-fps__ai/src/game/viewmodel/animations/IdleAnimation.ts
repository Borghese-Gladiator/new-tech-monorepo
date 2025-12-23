import * as THREE from 'three';
import { AnimationClip, AnimationState } from './AnimationClip';

export class IdleAnimation extends AnimationClip {
  constructor() {
    super(AnimationState.IDLE, Infinity, true);
  }

  evaluate(time: number): {
    position: THREE.Vector3;
    rotation: THREE.Euler;
    scale: THREE.Vector3;
  } {
    // Subtle breathing animation
    const breathingSpeed = 0.8;
    const breathingAmount = 0.003;

    const breathY = Math.sin(time * breathingSpeed) * breathingAmount;
    const breathRotZ = Math.sin(time * breathingSpeed * 0.5) * 0.005;

    return {
      position: new THREE.Vector3(0, breathY, 0),
      rotation: new THREE.Euler(0, 0, breathRotZ),
      scale: new THREE.Vector3(1, 1, 1)
    };
  }
}
