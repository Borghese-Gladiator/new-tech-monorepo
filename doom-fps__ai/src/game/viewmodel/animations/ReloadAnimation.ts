import * as THREE from 'three';
import { AnimationClip, AnimationState } from './AnimationClip';

export class ReloadAnimation extends AnimationClip {
  constructor(duration: number) {
    super(AnimationState.RELOAD, duration, false);
  }

  evaluate(time: number): {
    position: THREE.Vector3;
    rotation: THREE.Euler;
    scale: THREE.Vector3;
  } {
    const t = Math.min(time / this.duration, 1);

    let posY: number;
    let posZ: number;
    let rotX: number;
    let rotY: number;

    // Reload animation: lower weapon, tilt, bring back up
    if (t < 0.3) {
      // Lower weapon down and to the right
      const lowerT = this.easeInCubic(t / 0.3);
      posY = -lowerT * 0.3;
      posZ = lowerT * 0.15;
      rotX = lowerT * 0.4;
      rotY = lowerT * 0.3;
    } else if (t < 0.7) {
      // Hold at bottom (magazine swap)
      posY = -0.3;
      posZ = 0.15;
      rotX = 0.4;
      rotY = 0.3;
    } else {
      // Bring weapon back up
      const raiseT = this.easeOutCubic((t - 0.7) / 0.3);
      posY = -0.3 * (1 - raiseT);
      posZ = 0.15 * (1 - raiseT);
      rotX = 0.4 * (1 - raiseT);
      rotY = 0.3 * (1 - raiseT);
    }

    return {
      position: new THREE.Vector3(0, posY, posZ),
      rotation: new THREE.Euler(rotX, rotY, 0),
      scale: new THREE.Vector3(1, 1, 1)
    };
  }
}
