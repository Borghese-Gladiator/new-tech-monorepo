export class InputManager {
  private keys: Set<string> = new Set();
  private mouseMovement = { x: 0, y: 0 };
  private isPointerLocked = false;
  private canvas: HTMLElement;
  private mouseButtons: Set<number> = new Set();
  private mouseJustPressed: Set<number> = new Set();

  constructor(canvas: HTMLElement) {
    this.canvas = canvas;
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    // Keyboard events
    window.addEventListener('keydown', (e) => {
      this.keys.add(e.code);
    });

    window.addEventListener('keyup', (e) => {
      this.keys.delete(e.code);
    });

    // Mouse buttons
    window.addEventListener('mousedown', (e) => {
      if (this.isPointerLocked) {
        this.mouseButtons.add(e.button);
        this.mouseJustPressed.add(e.button);
      }
    });

    window.addEventListener('mouseup', (e) => {
      this.mouseButtons.delete(e.button);
    });

    // Pointer lock
    this.canvas.addEventListener('click', () => {
      if (!this.isPointerLocked) {
        this.canvas.requestPointerLock();
      }
    });

    document.addEventListener('pointerlockchange', () => {
      this.isPointerLocked = document.pointerLockElement === this.canvas;
      if (!this.isPointerLocked) {
        this.mouseButtons.clear();
        this.mouseJustPressed.clear();
      }
    });

    // Mouse movement
    document.addEventListener('mousemove', (e) => {
      if (this.isPointerLocked) {
        this.mouseMovement.x = e.movementX;
        this.mouseMovement.y = e.movementY;
      }
    });
  }

  isKeyPressed(code: string): boolean {
    return this.keys.has(code);
  }

  getMouseMovement(): { x: number; y: number } {
    return { ...this.mouseMovement };
  }

  resetMouseMovement(): void {
    this.mouseMovement.x = 0;
    this.mouseMovement.y = 0;
  }

  getPointerLocked(): boolean {
    return this.isPointerLocked;
  }

  isMouseButtonPressed(button: number): boolean {
    return this.mouseButtons.has(button);
  }

  isMouseButtonJustPressed(button: number): boolean {
    return this.mouseJustPressed.has(button);
  }

  clearMouseJustPressed(): void {
    this.mouseJustPressed.clear();
  }
}
