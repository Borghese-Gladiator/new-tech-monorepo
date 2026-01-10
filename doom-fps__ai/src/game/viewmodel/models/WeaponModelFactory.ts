import * as THREE from 'three';
import { WeaponType } from '../../weapons/WeaponFactory';

export interface WeaponModelConfig {
  model: THREE.Group;
  muzzlePosition: THREE.Vector3;  // Position of muzzle for flash effect
  glowingParts?: THREE.Mesh[];    // Parts that glow/pulse
}

export class WeaponModelFactory {
  /**
   * Create weapon model by type
   */
  static createModel(type: WeaponType): WeaponModelConfig {
    switch (type) {
      case WeaponType.PISTOL:
        return this.createDemonicPistolModel();
      case WeaponType.RIFLE:
        return this.createDemonicRifleModel();
      default:
        throw new Error(`Unknown weapon type: ${type}`);
    }
  }

  /**
   * Create demonic pistol model - DOOM style hellfire weapon
   */
  private static createDemonicPistolModel(): WeaponModelConfig {
    const group = new THREE.Group();
    const glowingParts: THREE.Mesh[] = [];

    // Dark metal materials
    const darkMetalMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a0a0a,
      roughness: 0.5,
      metalness: 0.7
    });

    const demonBoneMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a1515,
      roughness: 0.8,
      metalness: 0.2
    });

    // Glowing rune material
    const runeMaterial = new THREE.MeshBasicMaterial({
      color: 0xff2200,
      transparent: true,
      opacity: 0.9
    });

    // Bulky demonic grip - bone-like
    const gripGeometry = new THREE.BoxGeometry(0.04, 0.14, 0.05);
    const grip = new THREE.Mesh(gripGeometry, demonBoneMaterial);
    grip.position.set(0, -0.09, 0);
    grip.rotation.z = 0.12;
    group.add(grip);

    // Grip spikes
    const spikeGeometry = new THREE.ConeGeometry(0.008, 0.025, 4);
    const spikeMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a0505,
      roughness: 0.4,
      metalness: 0.6
    });

    for (let i = 0; i < 3; i++) {
      const spike = new THREE.Mesh(spikeGeometry, spikeMaterial);
      spike.position.set(-0.025, -0.05 + i * 0.04, 0);
      spike.rotation.z = Math.PI / 2;
      group.add(spike);
    }

    // Heavy slide with demonic design
    const slideGeometry = new THREE.BoxGeometry(0.035, 0.06, 0.18);
    const slide = new THREE.Mesh(slideGeometry, darkMetalMaterial);
    slide.position.set(0, 0, -0.04);
    group.add(slide);

    // Demonic barrel - thicker, more aggressive
    const barrelGeometry = new THREE.CylinderGeometry(0.012, 0.015, 0.1, 8);
    const barrel = new THREE.Mesh(barrelGeometry, darkMetalMaterial);
    barrel.rotation.x = Math.PI / 2;
    barrel.position.set(0, 0, -0.13);
    group.add(barrel);

    // Glowing barrel core
    const barrelCoreGeometry = new THREE.CylinderGeometry(0.006, 0.006, 0.12, 6);
    const barrelCore = new THREE.Mesh(barrelCoreGeometry, runeMaterial);
    barrelCore.rotation.x = Math.PI / 2;
    barrelCore.position.set(0, 0, -0.13);
    group.add(barrelCore);
    glowingParts.push(barrelCore);

    // Demonic rune ring on slide
    const runeRingGeometry = new THREE.TorusGeometry(0.02, 0.003, 6, 12);
    const runeRing = new THREE.Mesh(runeRingGeometry, runeMaterial);
    runeRing.position.set(0, 0.035, -0.02);
    runeRing.rotation.x = Math.PI / 2;
    group.add(runeRing);
    glowingParts.push(runeRing);

    // Skull emblem on side
    const skullGeometry = new THREE.SphereGeometry(0.012, 6, 6);
    const skullMaterial = new THREE.MeshStandardMaterial({
      color: 0xccbbaa,
      roughness: 0.8
    });
    const skull = new THREE.Mesh(skullGeometry, skullMaterial);
    skull.position.set(0.02, 0, 0);
    skull.scale.set(0.8, 1, 0.6);
    group.add(skull);

    // Trigger guard with horn-like design
    const guardGeometry = new THREE.TorusGeometry(0.025, 0.004, 6, 8, Math.PI);
    const guard = new THREE.Mesh(guardGeometry, darkMetalMaterial);
    guard.position.set(0, -0.025, 0.01);
    guard.rotation.x = Math.PI;
    guard.rotation.z = Math.PI / 2;
    group.add(guard);

    // Trigger
    const triggerGeometry = new THREE.BoxGeometry(0.018, 0.035, 0.012);
    const trigger = new THREE.Mesh(triggerGeometry, spikeMaterial);
    trigger.position.set(0, -0.035, 0.01);
    group.add(trigger);

    // Muzzle position
    const muzzlePosition = new THREE.Vector3(0, 0, -0.18);

    return { model: group, muzzlePosition, glowingParts };
  }

  /**
   * Create demonic rifle model - DOOM style plasma/demon rifle
   */
  private static createDemonicRifleModel(): WeaponModelConfig {
    const group = new THREE.Group();
    const glowingParts: THREE.Mesh[] = [];

    // Dark demonic metal
    const darkMetalMaterial = new THREE.MeshStandardMaterial({
      color: 0x151010,
      roughness: 0.4,
      metalness: 0.8
    });

    const demonBoneMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a0a0a,
      roughness: 0.7,
      metalness: 0.3
    });

    // Hellfire glow material
    const hellfireMaterial = new THREE.MeshBasicMaterial({
      color: 0x44ff44, // Green hellfire
      transparent: true,
      opacity: 0.9
    });

    const runeRedMaterial = new THREE.MeshBasicMaterial({
      color: 0xff2200,
      transparent: true,
      opacity: 0.8
    });

    // Angular demonic receiver
    const receiverGeometry = new THREE.BoxGeometry(0.05, 0.07, 0.35);
    const receiver = new THREE.Mesh(receiverGeometry, darkMetalMaterial);
    receiver.position.set(0, 0, -0.12);
    group.add(receiver);

    // Receiver spikes (top)
    const receiverSpikeGeo = new THREE.ConeGeometry(0.01, 0.04, 4);
    for (let i = 0; i < 3; i++) {
      const spike = new THREE.Mesh(receiverSpikeGeo, demonBoneMaterial);
      spike.position.set(0, 0.05, -0.05 + i * 0.1);
      group.add(spike);
    }

    // Demonic stock with bone/horn design
    const stockGeometry = new THREE.BoxGeometry(0.04, 0.1, 0.22);
    const stock = new THREE.Mesh(stockGeometry, demonBoneMaterial);
    stock.position.set(0, -0.01, 0.18);
    group.add(stock);

    // Stock horn curves
    const hornGeometry = new THREE.TorusGeometry(0.04, 0.008, 6, 8, Math.PI / 2);
    const hornMaterial = new THREE.MeshStandardMaterial({
      color: 0x0a0505,
      roughness: 0.5,
      metalness: 0.4
    });
    const stockHorn = new THREE.Mesh(hornGeometry, hornMaterial);
    stockHorn.position.set(0, 0.04, 0.28);
    stockHorn.rotation.y = Math.PI / 2;
    group.add(stockHorn);

    // Heavy barrel with demonic design
    const barrelGeometry = new THREE.CylinderGeometry(0.018, 0.022, 0.3, 8);
    const barrel = new THREE.Mesh(barrelGeometry, darkMetalMaterial);
    barrel.rotation.x = Math.PI / 2;
    barrel.position.set(0, 0.01, -0.4);
    group.add(barrel);

    // Glowing barrel core (hellfire green)
    const barrelCoreGeometry = new THREE.CylinderGeometry(0.008, 0.008, 0.35, 6);
    const barrelCore = new THREE.Mesh(barrelCoreGeometry, hellfireMaterial);
    barrelCore.rotation.x = Math.PI / 2;
    barrelCore.position.set(0, 0.01, -0.4);
    group.add(barrelCore);
    glowingParts.push(barrelCore);

    // Barrel rings (demonic)
    for (let i = 0; i < 3; i++) {
      const ringGeometry = new THREE.TorusGeometry(0.025, 0.004, 6, 12);
      const ring = new THREE.Mesh(ringGeometry, runeRedMaterial);
      ring.position.set(0, 0.01, -0.3 - i * 0.08);
      group.add(ring);
      glowingParts.push(ring);
    }

    // Handguard with skeletal design
    const handguardGeometry = new THREE.BoxGeometry(0.045, 0.05, 0.18);
    const handguard = new THREE.Mesh(handguardGeometry, demonBoneMaterial);
    handguard.position.set(0, -0.015, -0.32);
    group.add(handguard);

    // Handguard ribs
    for (let i = 0; i < 4; i++) {
      const ribGeometry = new THREE.BoxGeometry(0.05, 0.008, 0.015);
      const rib = new THREE.Mesh(ribGeometry, darkMetalMaterial);
      rib.position.set(0, -0.04, -0.26 - i * 0.04);
      group.add(rib);
    }

    // Magazine with demonic carving
    const magazineGeometry = new THREE.BoxGeometry(0.035, 0.14, 0.05);
    const magazine = new THREE.Mesh(magazineGeometry, darkMetalMaterial);
    magazine.position.set(0, -0.1, -0.08);
    group.add(magazine);

    // Magazine glow strip
    const magGlowGeometry = new THREE.BoxGeometry(0.005, 0.12, 0.02);
    const magGlow = new THREE.Mesh(magGlowGeometry, hellfireMaterial);
    magGlow.position.set(0.018, -0.1, -0.08);
    group.add(magGlow);
    glowingParts.push(magGlow);

    // Demonic pistol grip
    const gripGeometry = new THREE.BoxGeometry(0.035, 0.1, 0.05);
    const grip = new THREE.Mesh(gripGeometry, demonBoneMaterial);
    grip.position.set(0, -0.08, 0.04);
    grip.rotation.z = 0.08;
    group.add(grip);

    // Trigger
    const triggerGeometry = new THREE.BoxGeometry(0.02, 0.03, 0.012);
    const triggerMaterial = new THREE.MeshStandardMaterial({ color: 0x1a0a0a });
    const trigger = new THREE.Mesh(triggerGeometry, triggerMaterial);
    trigger.position.set(0, -0.045, -0.01);
    group.add(trigger);

    // Side runes
    const runeGeometry = new THREE.PlaneGeometry(0.02, 0.04);
    const rune1 = new THREE.Mesh(runeGeometry, runeRedMaterial);
    rune1.position.set(0.028, 0, -0.1);
    rune1.rotation.y = Math.PI / 2;
    group.add(rune1);
    glowingParts.push(rune1);

    const rune2 = new THREE.Mesh(runeGeometry, runeRedMaterial);
    rune2.position.set(-0.028, 0, -0.1);
    rune2.rotation.y = -Math.PI / 2;
    group.add(rune2);
    glowingParts.push(rune2);

    // Muzzle position
    const muzzlePosition = new THREE.Vector3(0, 0.01, -0.55);

    return { model: group, muzzlePosition, glowingParts };
  }

  /**
   * Create generic weapon model (fallback)
   */
  static createGenericModel(): WeaponModelConfig {
    const group = new THREE.Group();

    const geometry = new THREE.BoxGeometry(0.05, 0.05, 0.2);
    const material = new THREE.MeshStandardMaterial({
      color: 0x2a0a0a
    });
    const mesh = new THREE.Mesh(geometry, material);
    group.add(mesh);

    return {
      model: group,
      muzzlePosition: new THREE.Vector3(0, 0, -0.1)
    };
  }
}
