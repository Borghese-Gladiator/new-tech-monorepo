#!/usr/bin/env python3
"""
Manual test script for Valkey caching service.

Usage:
    # Start the server first:
    export VALKEY_FAKE=1
    uvicorn src.cache_service:app --reload

    # Then run this script:
    python manual_test.py

    # Or with real Redis:
    export VALKEY_FAKE=0
    python manual_test.py
"""
import httpx
import asyncio
import time
import sys
from typing import Dict, Any
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8000"


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def assert_true(self, condition: bool, message: str):
        if condition:
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {message}")
            self.passed += 1
        else:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {message}")
            self.failed += 1
            return False
        return True

    def print_header(self, text: str):
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{text}")
        print(f"{'='*60}{Style.RESET_ALL}")

    def print_section(self, text: str):
        print(f"\n{Fore.YELLOW}[{text}]{Style.RESET_ALL}")

    def print_summary(self):
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"Test Summary")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"Passed: {Fore.GREEN}{self.passed}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{self.failed}{Style.RESET_ALL}")
        print(f"Total:  {self.passed + self.failed}")

        if self.failed == 0:
            print(f"\n{Fore.GREEN}All tests passed! 🎉{Style.RESET_ALL}\n")
            return 0
        else:
            print(f"\n{Fore.RED}Some tests failed! ❌{Style.RESET_ALL}\n")
            return 1


async def test_health_check(client: httpx.AsyncClient, runner: TestRunner):
    """Test 1: Health Check"""
    runner.print_section("Test 1: Health Check")

    r = await client.get("/healthz")
    runner.assert_true(r.status_code == 200, "Health check returns 200")

    data = r.json()
    runner.assert_true(data.get("ok") is True, "Health status is ok")
    runner.assert_true("valkey" in data, "Health check includes Valkey status")
    runner.assert_true("circuit_breaker" in data, "Health check includes circuit breaker status")

    print(f"  Response: {data}")


async def test_cache_stats(client: httpx.AsyncClient, runner: TestRunner):
    """Test 2: Cache Statistics"""
    runner.print_section("Test 2: Cache Statistics")

    r = await client.get("/stats")
    runner.assert_true(r.status_code == 200, "Stats endpoint returns 200")

    data = r.json()
    runner.assert_true("total_keys" in data, "Stats include total_keys")
    runner.assert_true("connected" in data, "Stats include connection status")
    runner.assert_true(data.get("connected") is True, "Cache is connected")

    print(f"  Total keys: {data.get('total_keys')}")
    print(f"  Memory usage: {data.get('memory_usage')} bytes")


async def test_cache_aside(client: httpx.AsyncClient, runner: TestRunner):
    """Test 3: Cache-Aside Pattern"""
    runner.print_section("Test 3: Cache-Aside Pattern")

    # First request (cache miss)
    start = time.time()
    r1 = await client.get("/users/1", params={"strategy": "cache-aside", "ttl": 60})
    t1 = time.time() - start

    runner.assert_true(r1.status_code == 200, "Cache-aside request succeeds")
    data1 = r1.json()
    runner.assert_true(data1.get("id") == "1", "Returns correct user")
    print(f"  First request (miss): {t1*1000:.2f}ms")

    # Second request (cache hit)
    start = time.time()
    r2 = await client.get("/users/1", params={"strategy": "cache-aside", "ttl": 60})
    t2 = time.time() - start

    runner.assert_true(r2.status_code == 200, "Second request succeeds")
    runner.assert_true(r2.json() == data1, "Cached data matches")
    print(f"  Second request (hit): {t2*1000:.2f}ms")
    print(f"  Speedup: {t1/t2:.1f}x faster")


async def test_singleflight(client: httpx.AsyncClient, runner: TestRunner):
    """Test 4: Singleflight Pattern"""
    runner.print_section("Test 4: Singleflight Pattern")

    r = await client.get("/users/2", params={"strategy": "singleflight", "ttl": 60})
    runner.assert_true(r.status_code == 200, "Singleflight request succeeds")

    data = r.json()
    runner.assert_true(data.get("id") == "2", "Returns correct user")
    runner.assert_true("name" in data, "User has name field")

    print(f"  User: {data.get('name')} - {data.get('title')}")


async def test_swr(client: httpx.AsyncClient, runner: TestRunner):
    """Test 5: Stale-While-Revalidate"""
    runner.print_section("Test 5: Stale-While-Revalidate")

    # Initial request
    r1 = await client.get("/users/1", params={
        "strategy": "swr",
        "ttl": 2,
        "stale_grace": 10
    })
    runner.assert_true(r1.status_code == 200, "SWR initial request succeeds")

    # Wait for stale
    print("  Waiting 2.5s for cache to become stale...")
    await asyncio.sleep(2.5)

    # Should serve stale
    r2 = await client.get("/users/1", params={
        "strategy": "swr",
        "ttl": 2,
        "stale_grace": 10
    })
    runner.assert_true(r2.status_code == 200, "SWR serves stale data")
    runner.assert_true(r2.json() == r1.json(), "Stale data matches original")


async def test_negative_cache(client: httpx.AsyncClient, runner: TestRunner):
    """Test 6: Negative Caching"""
    runner.print_section("Test 6: Negative Caching")

    r1 = await client.get("/users/99999", params={"strategy": "negative"})
    runner.assert_true(r1.status_code == 404, "Non-existent user returns 404")

    # Second request should hit negative cache
    r2 = await client.get("/users/99999", params={"strategy": "negative"})
    runner.assert_true(r2.status_code == 404, "Negative cache returns 404")


async def test_write_through(client: httpx.AsyncClient, runner: TestRunner):
    """Test 7: Write-Through Caching"""
    runner.print_section("Test 7: Write-Through Caching")

    r = await client.post("/users/1", json={
        "name": "Ada Lovelace",
        "title": "First Programmer",
        "mode": "write-through"
    })

    runner.assert_true(r.status_code == 200, "Write-through update succeeds")
    data = r.json()
    runner.assert_true(data.get("ok") is True, "Response indicates success")
    runner.assert_true(data.get("mode") == "write-through", "Correct mode confirmed")

    # Verify cache updated
    r2 = await client.get("/users/1", params={"strategy": "cache-aside"})
    runner.assert_true(r2.json().get("name") == "Ada Lovelace", "Cache updated with new data")


async def test_write_behind(client: httpx.AsyncClient, runner: TestRunner):
    """Test 8: Write-Behind Caching"""
    runner.print_section("Test 8: Write-Behind Caching")

    r = await client.post("/users/3", json={
        "name": "Grace Hopper",
        "title": "COBOL Creator",
        "mode": "write-behind"
    })

    runner.assert_true(r.status_code == 200, "Write-behind update succeeds")
    data = r.json()
    runner.assert_true(data.get("mode") == "write-behind", "Correct mode confirmed")

    # Wait for background processing
    await asyncio.sleep(0.5)
    print("  Background write should have completed")


async def test_bulk_operations(client: httpx.AsyncClient, runner: TestRunner):
    """Test 9: Bulk Operations"""
    runner.print_section("Test 9: Bulk Operations")

    r = await client.get("/bulk/users", params={"ids": "1,2,999"})
    runner.assert_true(r.status_code == 200, "Bulk request succeeds")

    data = r.json()
    runner.assert_true("1" in data, "Bulk includes user 1")
    runner.assert_true("2" in data, "Bulk includes user 2")

    print(f"  Retrieved {len(data)} users")


async def test_invalidation(client: httpx.AsyncClient, runner: TestRunner):
    """Test 10: Cache Invalidation"""
    runner.print_section("Test 10: Cache Invalidation")

    r = await client.post("/invalidate/1")
    runner.assert_true(r.status_code == 200, "Invalidation succeeds")
    runner.assert_true(r.json().get("ok") is True, "Invalidation confirmed")


async def test_rate_limiting(client: httpx.AsyncClient, runner: TestRunner):
    """Test 11: Rate Limiting"""
    runner.print_section("Test 11: Rate Limiting")

    # Make many requests
    responses = []
    for i in range(110):
        r = await client.get("/users/1", headers={"X-User": "test-rate-limit"})
        responses.append(r.status_code)

    rate_limited = [r for r in responses if r == 429]
    runner.assert_true(len(rate_limited) > 0, f"Rate limiting triggered ({len(rate_limited)} requests blocked)")


async def test_input_validation(client: httpx.AsyncClient, runner: TestRunner):
    """Test 12: Input Validation"""
    runner.print_section("Test 12: Input Validation")

    # Invalid strategy
    r1 = await client.get("/users/1", params={"strategy": "invalid"})
    runner.assert_true(r1.status_code == 400, "Invalid strategy rejected")

    # Invalid TTL
    r2 = await client.get("/users/1", params={"ttl": 999999})
    runner.assert_true(r2.status_code == 400, "Invalid TTL rejected")

    # Invalid stale_grace
    r3 = await client.get("/users/1", params={"strategy": "swr", "stale_grace": 99999})
    runner.assert_true(r3.status_code == 400, "Invalid stale_grace rejected")

    # Invalid mode in update
    r4 = await client.post("/users/1", json={"name": "Test", "mode": "invalid-mode"})
    runner.assert_true(r4.status_code == 422, "Invalid mode rejected")


async def test_distributed_lock(client: httpx.AsyncClient, runner: TestRunner):
    """Test 13: Distributed Locking"""
    runner.print_section("Test 13: Distributed Locking")

    r1 = await client.post("/recompute")
    runner.assert_true(r1.status_code == 200, "First recompute succeeds")

    # Try again immediately (should be locked)
    r2 = await client.post("/recompute")
    # May succeed if first completed, or 423 if locked
    if r2.status_code == 423:
        runner.assert_true(True, "Second recompute blocked by lock")
    else:
        runner.assert_true(r2.status_code == 200, "Recompute completed")


async def test_request_scope_cache(client: httpx.AsyncClient, runner: TestRunner):
    """Test 14: Request-Scope Cache"""
    runner.print_section("Test 14: Request-Scope Cache")

    r = await client.get("/calc/heavy", params={"n": 20})
    runner.assert_true(r.status_code == 200, "Heavy calc succeeds")

    data = r.json()
    runner.assert_true("sum" in data, "Returns sum")
    print(f"  Calculated sum: {data.get('sum')}")


async def test_concurrent_requests(client: httpx.AsyncClient, runner: TestRunner):
    """Test 15: Concurrent Request Handling"""
    runner.print_section("Test 15: Concurrent Request Handling")

    # Make 20 concurrent requests
    tasks = []
    for i in range(20):
        task = client.get("/users/1", params={"strategy": "singleflight"})
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r.status_code == 200)
    runner.assert_true(success_count == 20, f"All concurrent requests succeed ({success_count}/20)")


async def main():
    runner = TestRunner()

    runner.print_header("Valkey Caching Service - Manual Test Suite")
    print(f"Testing against: {BASE_URL}")

    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Check if server is running
            try:
                await client.get("/healthz")
            except httpx.ConnectError:
                print(f"{Fore.RED}ERROR: Cannot connect to {BASE_URL}")
                print(f"Please start the server first:")
                print(f"  export VALKEY_FAKE=1")
                print(f"  uvicorn src.cache_service:app --reload{Style.RESET_ALL}")
                return 1

            # Run all tests
            await test_health_check(client, runner)
            await test_cache_stats(client, runner)
            await test_cache_aside(client, runner)
            await test_singleflight(client, runner)
            await test_swr(client, runner)
            await test_negative_cache(client, runner)
            await test_write_through(client, runner)
            await test_write_behind(client, runner)
            await test_bulk_operations(client, runner)
            await test_invalidation(client, runner)
            await test_rate_limiting(client, runner)
            await test_input_validation(client, runner)
            await test_distributed_lock(client, runner)
            await test_request_scope_cache(client, runner)
            await test_concurrent_requests(client, runner)

    except Exception as e:
        print(f"{Fore.RED}Error running tests: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return 1

    # Print summary
    return runner.print_summary()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
