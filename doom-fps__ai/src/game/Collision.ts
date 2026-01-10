import * as THREE from 'three';

export interface AABB {
  min: THREE.Vector3;
  max: THREE.Vector3;
}

export class CollisionSystem {
  private colliders: AABB[] = [];

  addCollider(box: AABB): void {
    this.colliders.push(box);
  }

  // Check if an AABB intersects with any registered colliders
  checkCollision(box: AABB): boolean {
    for (const collider of this.colliders) {
      if (this.aabbIntersects(box, collider)) {
        return true;
      }
    }
    return false;
  }

  // Sweep test: move from current position and check collision, return adjusted position
  sweepTest(
    currentPos: THREE.Vector3,
    targetPos: THREE.Vector3,
    playerBox: { width: number; height: number; depth: number }
  ): THREE.Vector3 {
    const halfWidth = playerBox.width / 2;
    const halfDepth = playerBox.depth / 2;

    // Test each axis independently for sliding collision
    const finalPos = currentPos.clone();

    // Test X axis
    const testX = finalPos.clone();
    testX.x = targetPos.x;
    const boxX = this.createAABB(testX, playerBox);
    if (!this.checkCollision(boxX)) {
      finalPos.x = targetPos.x;
    }

    // Test Y axis
    const testY = finalPos.clone();
    testY.y = targetPos.y;
    const boxY = this.createAABB(testY, playerBox);
    if (!this.checkCollision(boxY)) {
      finalPos.y = targetPos.y;
    }

    // Test Z axis
    const testZ = finalPos.clone();
    testZ.z = targetPos.z;
    const boxZ = this.createAABB(testZ, playerBox);
    if (!this.checkCollision(boxZ)) {
      finalPos.z = targetPos.z;
    }

    return finalPos;
  }

  private createAABB(
    center: THREE.Vector3,
    box: { width: number; height: number; depth: number }
  ): AABB {
    return {
      min: new THREE.Vector3(
        center.x - box.width / 2,
        center.y - box.height / 2,
        center.z - box.depth / 2
      ),
      max: new THREE.Vector3(
        center.x + box.width / 2,
        center.y + box.height / 2,
        center.z + box.depth / 2
      )
    };
  }

  private aabbIntersects(a: AABB, b: AABB): boolean {
    return (
      a.min.x <= b.max.x &&
      a.max.x >= b.min.x &&
      a.min.y <= b.max.y &&
      a.max.y >= b.min.y &&
      a.min.z <= b.max.z &&
      a.max.z >= b.min.z
    );
  }

  getColliders(): AABB[] {
    return this.colliders;
  }
}
