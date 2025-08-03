#!/usr/bin/env python3
"""
Quick Start Script for Agent Swarm
Run this to test your setup quickly
"""

import asyncio
import sys
import os
from datetime import datetime

# Check for required packages
try:
    import langgraph
    import aiohttp
    from dotenv import load_dotenv
except ImportError as e:
    print("❌ Missing required packages!")
    print("Please run: pip install langgraph aiohttp python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

async def test_setup():
    """Test your setup and run a simple iteration"""
    print("🔍 Checking your setup...\n")
    
    # 1. Check environment variables
    coordinator_url = os.getenv('COORDINATOR_URL')
    if not coordinator_url:
        print("⚠️  COORDINATOR_URL not set in .env file")
        print("   Using default: http://localhost:8787")
        coordinator_url = "http://localhost:8787"
    else:
        print(f"✅ Coordinator URL: {coordinator_url}")
    
    # 2. Test dashboard connection
    print("\n🌐 Testing dashboard connection...")
    dashboard_available = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{coordinator_url}/dashboard", timeout=5) as resp:
                if resp.status == 200:
                    print("✅ Dashboard is running!")
                    print(f"   View at: {coordinator_url}/dashboard")
                    dashboard_available = True
    except:
        print("⚠️  Dashboard not accessible (that's OK for testing)")
    
    # 3. Run minimal workflow
    print("\n🚀 Running test workflow...")
    print("-" * 50)
    
    # Import and run the simple framework
    from simple_agent_framework import run_iteration
    
    # Mini backlog for testing
    test_backlog = [
        {
            "id": "TEST-001",
            "title": "Hello World API",
            "description": "Simple test endpoint"
        }
    ]
    
    await run_iteration(test_backlog)
    
    print("\n" + "="*50)
    print("✅ Setup test complete!")
    
    if dashboard_available:
        print(f"\n👉 Check your dashboard at: {coordinator_url}/dashboard")
        print("   You should see agent activity there!")
    else:
        print("\n💡 To see the web dashboard:")
        print("   1. Deploy the Cloudflare Worker first")
        print("   2. Update COORDINATOR_URL in your .env file")
        print("   3. Run this test again")
    
    print("\n🎉 Your agent swarm is working!")

if __name__ == "__main__":
    print("🤖 Agent Swarm Quick Start")
    print("="*50)
    asyncio.run(test_setup())