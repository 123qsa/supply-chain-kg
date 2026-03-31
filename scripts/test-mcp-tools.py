#!/usr/bin/env python3
"""
MCP Tools Test Script
Tests all registered MCP tools to verify they work correctly.
"""
import asyncio
import httpx
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


async def test_tool(client: httpx.AsyncClient, tool_name: str, params: Dict[str, Any]) -> bool:
    """Test a single MCP tool"""
    try:
        response = await client.post(
            f"{BASE_URL}/mcp/call/{tool_name}",
            json={"params": params},
            timeout=30.0
        )
        if response.status_code == 200:
            result = response.json()
            if "error" in result and result["error"]:
                print(f"  ✗ {tool_name}: {result['error']}")
                return False
            print(f"  ✓ {tool_name}")
            return True
        else:
            print(f"  ✗ {tool_name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ {tool_name}: {str(e)[:50]}")
        return False


async def main():
    print("=" * 60)
    print("MCP Tools Test Suite")
    print("=" * 60)
    print()

    async with httpx.AsyncClient() as client:
        # First check health
        print("Checking service health...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            health = response.json()
            print(f"  Status: {health.get('status', 'unknown')}")
            print(f"  Tools available: {health.get('tools_available', 0)}")
            print()
        except Exception as e:
            print(f"  ✗ Health check failed: {e}")
            sys.exit(1)

        # Get tools list
        print("Fetching tool list...")
        try:
            response = await client.get(f"{BASE_URL}/mcp/tools")
            tools = response.json().get("tools", [])
            print(f"  Found {len(tools)} tools")
            print()
        except Exception as e:
            print(f"  ✗ Failed to get tools: {e}")
            sys.exit(1)

        # Test KG Operations
        print("Testing KG Operations...")
        kg_tests = [
            ("upsert_company", {"ticker": "TEST", "name": "Test Company", "market": "us"}),
            ("get_company_neighbors", {"ticker": "NVDA"}),
            ("get_graph_stats", {}),
            ("find_paths", {"start": "NVDA", "end": "AMD"}),
            ("get_subgraph", {"ticker": "NVDA"}),
        ]

        kg_results = []
        for tool_name, params in kg_tests:
            result = await test_tool(client, tool_name, params)
            kg_results.append(result)

        print()

        # Test Discovery
        print("Testing Discovery Tools...")
        discovery_tests = [
            ("discover_peers", {"symbol": "NVDA", "market": "us"}),
            ("discover_etf_holdings", {"symbol": "SOXX"}),
            ("discover_institutional", {"symbol": "NVDA"}),
            ("expand_node", {"symbol": "NVDA"}),
        ]

        discovery_results = []
        for tool_name, params in discovery_tests:
            result = await test_tool(client, tool_name, params)
            discovery_results.append(result)

        print()

        # Test Collection
        print("Testing Collection Tools...")
        collection_tests = [
            ("get_profile", {"symbol": "NVDA", "market": "us"}),
            ("get_price", {"symbol": "NVDA", "start_date": "2024-01-01", "end_date": "2024-01-31"}),
            ("get_financials", {"symbol": "NVDA"}),
        ]

        collection_results = []
        for tool_name, params in collection_tests:
            result = await test_tool(client, tool_name, params)
            collection_results.append(result)

        print()

        # Test Database Operations
        print("Testing Database Tools...")
        db_tests = [
            ("get_price_history", {"ticker": "NVDA"}),
            ("get_discovery_history", {}),
            ("get_impact_history", {}),
        ]

        db_results = []
        for tool_name, params in db_tests:
            result = await test_tool(client, tool_name, params)
            db_results.append(result)

        print()

        # Summary
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)

        total_tests = len(kg_results) + len(discovery_results) + len(collection_results) + len(db_results)
        total_passed = sum(kg_results) + sum(discovery_results) + sum(collection_results) + sum(db_results)

        print(f"KG Operations:     {sum(kg_results)}/{len(kg_results)} passed")
        print(f"Discovery Tools:   {sum(discovery_results)}/{len(discovery_results)} passed")
        print(f"Collection Tools:  {sum(collection_results)}/{len(collection_results)} passed")
        print(f"Database Tools:    {sum(db_results)}/{len(db_results)} passed")
        print()
        print(f"Total: {total_passed}/{total_tests} tests passed")

        if total_passed == total_tests:
            print("\n✓ All tests passed!")
            return 0
        else:
            print(f"\n✗ {total_tests - total_passed} tests failed")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
