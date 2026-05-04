import type { GameState } from "@gas-city/poker-core";

export type Room = {
  gameId: number;
  state: GameState | null;
  /** socket.id -> seatIndex; tracks live socket bindings to seats */
  seatBySocket: Map<string, number>;
};

export class Rooms {
  private readonly rooms = new Map<number, Room>();

  get(gameId: number): Room | undefined {
    return this.rooms.get(gameId);
  }

  ensure(gameId: number): Room {
    const existing = this.rooms.get(gameId);
    if (existing) return existing;
    const fresh: Room = {
      gameId,
      state: null,
      seatBySocket: new Map(),
    };
    this.rooms.set(gameId, fresh);
    return fresh;
  }

  setState(gameId: number, state: GameState): void {
    const room = this.ensure(gameId);
    room.state = state;
  }

  bindSocket(gameId: number, socketId: string, seatIndex: number): void {
    const room = this.ensure(gameId);
    room.seatBySocket.set(socketId, seatIndex);
  }

  unbindSocket(socketId: string): { gameId: number; seatIndex: number } | null {
    for (const room of this.rooms.values()) {
      const seat = room.seatBySocket.get(socketId);
      if (seat !== undefined) {
        room.seatBySocket.delete(socketId);
        return { gameId: room.gameId, seatIndex: seat };
      }
    }
    return null;
  }

  seatForSocket(socketId: string): { gameId: number; seatIndex: number } | null {
    for (const room of this.rooms.values()) {
      const seat = room.seatBySocket.get(socketId);
      if (seat !== undefined) {
        return { gameId: room.gameId, seatIndex: seat };
      }
    }
    return null;
  }

  socketForSeat(gameId: number, seatIndex: number): string | null {
    const room = this.rooms.get(gameId);
    if (!room) return null;
    for (const [socketId, seat] of room.seatBySocket) {
      if (seat === seatIndex) return socketId;
    }
    return null;
  }
}

export function gameRoomName(gameId: number): string {
  return `game:${gameId}`;
}
