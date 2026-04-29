# Multiplayer Rules

The server is authoritative.

Clients may send:
- createGame
- joinGame
- leaveGame
- playerAction
- reconnectSession

Clients must not decide:
- legal actions
- turn order
- pot size
- card dealing
- winner
- stack changes

The server broadcasts:
- gameSnapshot
- gameEvent
- playerError
- connectionStatus
