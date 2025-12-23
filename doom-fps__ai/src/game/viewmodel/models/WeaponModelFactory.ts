import * as THREE from 'three';
import { WeaponType } from '../../weapons/WeaponFactory';

export interface WeaponModelConfig {
  model: THREE.Group;
  muzzlePosition: THREE.Vector3;  // Position of muzzle for flash effect
}

export class WeaponModelFactory {
  /**
   * Create weapon model by type
   */
  static createModel(type: WeaponType): WeaponModelConfig {
    switch (type) {
      case WeaponType.PISTOL:
        return this.createPistolModel();
      case WeaponType.RIFLE:
        return this.createRifleModel();
      default:
        throw new Error(`Unknown weapon type: ${type}`);
    }
  }

  /**
   * Create pistol model (simple geometry)
   */
  private static createPistolModel(): WeaponModelConfig {
    const group = new THREE.Group();

    // Grip
    const gripGeometry = new THREE.BoxGeometry(0.03, 0.12, 0.04);
    const gripMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      roughness: 0.7,
      metalness: 0.3
    });
    const grip = new THREE.Mesh(gripGeometry, gripMaterial);
    grip.position.set(0, -0.08, 0);
    grip.rotation.z = 0.15;
    group.add(grip);

    // Slide (top part)
    const slideGeometry = new THREE.BoxGeometry(0.025, 0.05, 0.15);
    const slideMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.4,
      metalness: 0.8
    });
    const slide = new THREE.Mesh(slideGeometry, slideMaterial);
    slide.position.set(0, 0, -0.03);
    group.add(slide);

    // Barrel
    const barrelGeometry = new THREE.CylinderGeometry(0.008, 0.008, 0.08, 8);
    const barrelMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a0a0a,
      roughness: 0.3,
      metalness: 0.9
    });
    const barrel = new THREE.Mesh(barrelGeometry, barrelMaterial);
    barrel.rotation.x = Math.PI / 2;
    barrel.position.set(0, 0, -0.11);
    group.add(barrel);

    // Trigger
    const triggerGeometry = new THREE.BoxGeometry(0.015, 0.03, 0.01);
    const triggerMaterial = new THREE.MeshStandardMaterial({
      color: 0x3a3a3a,
      roughness: 0.6
    });
    const trigger = new THREE.Mesh(triggerGeometry, triggerMaterial);
    trigger.position.set(0, -0.03, 0.01);
    group.add(trigger);

    // Muzzle position (end of barrel)
    const muzzlePosition = new THREE.Vector3(0, 0, -0.15);

    return { model: group, muzzlePosition };
  }

  /**
   * Create rifle model (simple geometry)
   */
  private static createRifleModel(): WeaponModelConfig {
    const group = new THREE.Group();

    // Receiver (main body)
    const receiverGeometry = new THREE.BoxGeometry(0.04, 0.06, 0.3);
    const receiverMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      roughness: 0.7,
      metalness: 0.3
    });
    const receiver = new THREE.Mesh(receiverGeometry, receiverMaterial);
    receiver.position.set(0, 0, -0.1);
    group.add(receiver);

    // Stock (back part)
    const stockGeometry = new THREE.BoxGeometry(0.035, 0.08, 0.2);
    const stockMaterial = new THREE.MeshStandardMaterial({
      color: 0x3a2a1a,
      roughness: 0.8
    });
    const stock = new THREE.Mesh(stockGeometry, stockMaterial);
    stock.position.set(0, -0.01, 0.15);
    group.add(stock);

    // Barrel
    const barrelGeometry = new THREE.CylinderGeometry(0.012, 0.012, 0.25, 8);
    const barrelMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a0a0a,
      roughness: 0.3,
      metalness: 0.9
    });
    const barrel = new THREE.Mesh(barrelGeometry, barrelMaterial);
    barrel.rotation.x = Math.PI / 2;
    barrel.position.set(0, 0.01, -0.35);
    group.add(barrel);

    // Handguard
    const handguardGeometry = new THREE.BoxGeometry(0.035, 0.04, 0.15);
    const handguardMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.7
    });
    const handguard = new THREE.Mesh(handguardGeometry, handguardMaterial);
    handguard.position.set(0, -0.01, -0.3);
    group.add(handguard);

    // Magazine
    const magazineGeometry = new THREE.BoxGeometry(0.025, 0.12, 0.04);
    const magazineMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a1a,
      roughness: 0.6
    });
    const magazine = new THREE.Mesh(magazineGeometry, magazineMaterial);
    magazine.position.set(0, -0.09, -0.05);
    group.add(magazine);

    // Pistol grip
    const gripGeometry = new THREE.BoxGeometry(0.025, 0.08, 0.04);
    const gripMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      roughness: 0.7
    });
    const grip = new THREE.Mesh(gripGeometry, gripMaterial);
    grip.position.set(0, -0.07, 0.02);
    grip.rotation.z = 0.1;
    group.add(grip);

    // Trigger
    const triggerGeometry = new THREE.BoxGeometry(0.015, 0.025, 0.01);
    const triggerMaterial = new THREE.MeshStandardMaterial({
      color: 0x3a3a3a
    });
    const trigger = new THREE.Mesh(triggerGeometry, triggerMaterial);
    trigger.position.set(0, -0.04, -0.01);
    group.add(trigger);

    // Muzzle position (end of barrel)
    const muzzlePosition = new THREE.Vector3(0, 0.01, -0.475);

    return { model: group, muzzlePosition };
  }

  /**
   * Create generic weapon model (fallback)
   */
  static createGenericModel(): WeaponModelConfig {
    const group = new THREE.Group();

    const geometry = new THREE.BoxGeometry(0.05, 0.05, 0.2);
    const material = new THREE.MeshStandardMaterial({
      color: 0x555555
    });
    const mesh = new THREE.Mesh(geometry, material);
    group.add(mesh);

    return {
      model: group,
      muzzlePosition: new THREE.Vector3(0, 0, -0.1)
    };
  }
}
