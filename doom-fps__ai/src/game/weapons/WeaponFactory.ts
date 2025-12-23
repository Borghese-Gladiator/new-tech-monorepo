import { Weapon } from './Weapon';
import { Pistol } from './weapons/Pistol';
import { Rifle } from './weapons/Rifle';

export enum WeaponType {
  PISTOL = 'pistol',
  RIFLE = 'rifle'
}

export class WeaponFactory {
  /**
   * Create a weapon by type
   */
  static createWeapon(type: WeaponType): Weapon {
    switch (type) {
      case WeaponType.PISTOL:
        return new Pistol();
      case WeaponType.RIFLE:
        return new Rifle();
      default:
        throw new Error(`Unknown weapon type: ${type}`);
    }
  }

  /**
   * Create multiple weapons at once
   */
  static createWeapons(types: WeaponType[]): Weapon[] {
    return types.map(type => this.createWeapon(type));
  }

  /**
   * Create default loadout (pistol + rifle)
   */
  static createDefaultLoadout(): Weapon[] {
    return [
      new Pistol(),
      new Rifle()
    ];
  }

  /**
   * Get all available weapon types
   */
  static getAvailableTypes(): WeaponType[] {
    return Object.values(WeaponType);
  }
}
