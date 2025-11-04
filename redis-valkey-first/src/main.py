# client_example.py
import httpx, asyncio

BASE = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient(base_url=BASE) as c:
        # health
        print((await c.get("/healthz")).json())

        # read a user (single-flight strategy)
        r = await c.get("/users/1", params={"strategy": "singleflight"})
        print("GET /users/1", r.status_code, r.json())

        # update write-through
        r = await c.post("/users/1", json={"name": "Ada L.", "mode": "write-through"})
        print("POST /users/1", r.json())

        # SWR read
        r = await c.get("/users/1", params={"strategy": "swr", "ttl": 5, "stale_grace": 20})
        print("SWR /users/1", r.json())

        # bulk
        r = await c.get("/bulk/users", params={"ids": "1,2,999"})
        print("BULK:", r.json())

        # request-scope cache demo
        r = await c.get("/calc/heavy", params={"n": 20})
        print("heavy calc:", r.json())

if __name__ == "__main__":
    asyncio.run(main())
