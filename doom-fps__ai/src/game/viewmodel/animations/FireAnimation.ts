import * as THREE from 'three';
import { AnimationClip, AnimationState } from './AnimationClip';

export class FireAnimation extends AnimationClip {
  private recoilStrength: number;

  constructor(recoilStrength = 0.1) {
    super(AnimationState.FIRE, 0.15, false);
    this.recoilStrength = recoilStrength;
  }

  evaluate(time: number): {
    position: THREE.Vector3;
    rotation: THREE.Euler;
    scale: THREE.Vector3;
  } {
    const t = Math.min(time / this.duration, 1);

    // Recoil: quick up/back, then ease back to position
    let recoilY: number;
    let recoilZ: number;
    let recoilRotX: number;

    if (t < 0.2) {
      // Fast recoil up and back
      const kickT = t / 0.2;
      recoilY = kickT * this.recoilStrength * 0.3;
      recoilZ = kickT * this.recoilStrength;
      recoilRotX = kickT * this.recoilStrength * 0.5;
    } else {
      // Ease back to original position
      const returnT = (t - 0.2) / 0.8;
      const eased = this.easeOutCubic(returnT);
      recoilY = (1 - eased) * this.recoilStrength * 0.3;
      recoilZ = (1 - eased) * this.recoilStrength;
      recoilRotX = (1 - eased) * this.recoilStrength * 0.5;
    }

    return {
      position: new THREE.Vector3(0, recoilY, recoilZ),
      rotation: new THREE.Euler(-recoilRotX, 0, 0),
      scale: new THREE.Vector3(1, 1, 1)
    };
  }
}
