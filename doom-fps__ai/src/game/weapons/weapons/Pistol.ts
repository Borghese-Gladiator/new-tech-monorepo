import { HitscanWeapon } from '../HitscanWeapon';
import { FireMode } from '../Weapon';

export class Pistol extends HitscanWeapon {
  constructor() {
    super({
      name: 'Pistol',
      fireRate: 300,           // 300 rounds per minute (5 per second)
      damage: 25,              // 4 shots to kill (assuming 100 HP)
      range: 50,               // 50 meters effective range
      spread: 2,               // 2 degrees spread (accurate)
      maxAmmo: 12,             // 12 round magazine
      reloadTime: 1.5,         // 1.5 seconds to reload
      fireMode: FireMode.SEMI_AUTO
    });
  }
}
