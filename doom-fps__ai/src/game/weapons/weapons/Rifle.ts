import { HitscanWeapon } from '../HitscanWeapon';
import { FireMode } from '../Weapon';

export class Rifle extends HitscanWeapon {
  constructor() {
    super({
      name: 'Assault Rifle',
      fireRate: 600,           // 600 rounds per minute (10 per second)
      damage: 20,              // 5 shots to kill (assuming 100 HP)
      range: 100,              // 100 meters effective range
      spread: 3,               // 3 degrees spread (moderate accuracy)
      maxAmmo: 30,             // 30 round magazine
      reloadTime: 2.0,         // 2 seconds to reload
      fireMode: FireMode.FULL_AUTO
    });
  }
}
