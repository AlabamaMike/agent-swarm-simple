# Simplified LangGraph Multi-Agent Framework
# Minimal implementation focused on getting you running quickly

import asyncio
import aiohttp
import os
from typing import Dict, List, TypedDict, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
import json
from dotenv import load_dotenv

load_dotenv()

# ============== Configuration ==============
COORDINATOR_URL = os.getenv('COORDINATOR_URL', 'http://localhost:8787')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# ============== State Definition ==============
class IterationState(TypedDict):
    """Simple state for tracking iteration progress"""
    phase: Literal["planning", "approval", "building", "complete"]
    backlog: List[Dict]
    plan: Dict
    completed_tasks: List[str]
    messages: List[str]

# ============== Simple Agent Base ==============
class Agent:
    """Minimal agent that can execute tasks and report to dashboard"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.session = None
    
    async def setup(self):
        """Initialize HTTP session and register with dashboard"""
        self.session = aiohttp.ClientSession()
        try:
            await self.session.post(
                f"{COORDINATOR_URL}/api/agent/register",
                json={"id": self.name, "name": self.name, "role": self.role}
            )
        except:
            print(f"Warning: Could not register {self.name} with dashboard")
    
    async def update_dashboard(self, status: str, message: str):
        """Send status update to dashboard"""
        try:
            await self.session.post(
                f"{COORDINATOR_URL}/api/agent/update",
                json={"agentId": self.name, "status": status, "activity": message}
            )
            await self.session.post(
                f"{COORDINATOR_URL}/api/activity/post",
                json={"agent": self.name, "message": message}
            )
        except:
            pass  # Dashboard updates are optional
    
    async def cleanup(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

# ============== Core Workflow Nodes ==============

async def planning_node(state: IterationState) -> Dict:
    """Convert backlog items into a simple task plan"""
    print("\n🎯 PLANNING PHASE")
    
    # Create simple plan from backlog
    tasks = []
    for item in state["backlog"]:
        # Every feature needs: backend → frontend → tests
        feature_id = item["id"]
        tasks.extend([
            {"id": f"{feature_id}-backend", "title": f"Backend: {item['title']}", "assignee": "backend"},
            {"id": f"{feature_id}-frontend", "title": f"Frontend: {item['title']}", "assignee": "frontend"},
            {"id": f"{feature_id}-tests", "title": f"Tests: {item['title']}", "assignee": "qa"}
        ])
    
    plan = {"tasks": tasks, "total_tasks": len(tasks)}
    print(f"📋 Created plan with {len(tasks)} tasks")
    
    return {
        "phase": "approval",
        "plan": plan,
        "messages": state["messages"] + [f"Created plan with {len(tasks)} tasks"]
    }

async def approval_node(state: IterationState) -> Dict:
    """Simple approval - just wait a few seconds then auto-approve"""
    print("\n✅ APPROVAL PHASE")
    print("🤔 Waiting for approval... (auto-approving in 3 seconds)")
    
    # In real implementation, this would wait for dashboard approval
    await asyncio.sleep(3)
    
    print("✅ Plan approved!")
    return {
        "phase": "building",
        "messages": state["messages"] + ["Plan approved by product owner"]
    }

async def building_node(state: IterationState) -> Dict:
    """Simulate agents building the features"""
    print("\n🔨 BUILDING PHASE")
    
    # Create agents
    agents = {
        "backend": Agent("Backend SWE", "engineer"),
        "frontend": Agent("Frontend SWE", "engineer"),
        "qa": Agent("QA Engineer", "tester")
    }
    
    # Setup agents
    for agent in agents.values():
        await agent.setup()
    
    completed = []
    tasks = state["plan"]["tasks"]
    
    # Process tasks by type (simulate parallel work)
    for task_type in ["backend", "frontend", "qa"]:
        type_tasks = [t for t in tasks if t["assignee"] == task_type]
        if type_tasks:
            agent = agents[task_type]
            print(f"\n👤 {agent.name} working on {len(type_tasks)} tasks...")
            
            for task in type_tasks:
                await agent.update_dashboard("busy", f"Working on: {task['title']}")
                await asyncio.sleep(1)  # Simulate work
                
                print(f"  ✓ Completed: {task['title']}")
                completed.append(task["id"])
                
                await agent.update_dashboard("idle", f"Completed: {task['title']}")
    
    # Cleanup
    for agent in agents.values():
        await agent.cleanup()
    
    return {
        "phase": "complete",
        "completed_tasks": completed,
        "messages": state["messages"] + [f"Completed {len(completed)} tasks"]
    }

# ============== Main Workflow ==============

def create_workflow() -> StateGraph:
    """Create the simplest possible workflow"""
    workflow = StateGraph(IterationState)
    
    # Add nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("building", building_node)
    
    # Add flow
    workflow.set_entry_point("planning")
    workflow.add_edge("planning", "approval")
    workflow.add_edge("approval", "building")
    workflow.add_edge("building", END)
    
    return workflow.compile()

# ============== Simple Runner ==============

async def run_iteration(backlog_items: List[Dict]):
    """Run a single iteration with given backlog items"""
    print("🚀 Starting iteration...")
    
    # Initial state
    initial_state = {
        "phase": "planning",
        "backlog": backlog_items,
        "plan": {},
        "completed_tasks": [],
        "messages": []
    }
    
    # Create and run workflow
    workflow = create_workflow()
    
    # Execute workflow
    final_state = await workflow.ainvoke(initial_state)
    
    print("\n✨ ITERATION COMPLETE!")
    print(f"Completed tasks: {len(final_state['completed_tasks'])}")
    print("\nIteration log:")
    for msg in final_state["messages"]:
        print(f"  • {msg}")

# ============== Main Entry Point ==============

async def main():
    """Run a test iteration"""
    
    # Test connection to dashboard (optional)
    print("🔗 Testing dashboard connection...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{COORDINATOR_URL}/api/iteration/status") as resp:
                if resp.status == 200:
                    print("✅ Dashboard connected!")
                else:
                    print("⚠️  Dashboard not responding (will continue anyway)")
    except:
        print("⚠️  Dashboard not available (will continue anyway)")
    
    # Example backlog
    backlog = [
        {
            "id": "FEAT-001",
            "title": "User Login API",
            "description": "Create login endpoint with JWT"
        },
        {
            "id": "FEAT-002", 
            "title": "Dashboard UI",
            "description": "Create main dashboard page"
        }
    ]
    
    # Run iteration
    await run_iteration(backlog)

if __name__ == "__main__":
    asyncio.run(main())