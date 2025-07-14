#!/usr/bin/env python3
"""
Test Agent Functionality

Check which agent scripts are functioning vs non-functioning and identify any that should be removed.
"""

import sys
import importlib
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_agent_imports():
    """Test which agents can be imported successfully"""
    agents_dir = project_root / "claude_pm" / "agents"
    agent_files = [f for f in agents_dir.glob("*.py") if f.name != "__init__.py"]
    
    print("🧪 Testing Agent Script Functionality")
    print("=" * 60)
    
    working_agents = []
    broken_agents = []
    
    for agent_file in agent_files:
        agent_name = agent_file.stem
        module_name = f"claude_pm.agents.{agent_name}"
        
        try:
            # Try to import the module
            module = importlib.import_module(module_name)
            
            # Check if it has expected classes
            classes = [name for name in dir(module) if name.endswith('Agent') and not name.startswith('_')]
            
            if classes:
                print(f"✅ {agent_name}: {', '.join(classes)}")
                working_agents.append({
                    'file': agent_name,
                    'classes': classes,
                    'module': module
                })
            else:
                print(f"⚠️  {agent_name}: No agent classes found")
                broken_agents.append({
                    'file': agent_name,
                    'issue': 'No agent classes'
                })
                
        except Exception as e:
            print(f"❌ {agent_name}: Import failed - {e}")
            broken_agents.append({
                'file': agent_name,
                'issue': f'Import error: {e}'
            })
    
    print(f"\n📊 Summary:")
    print(f"  Working: {len(working_agents)}")
    print(f"  Issues:  {len(broken_agents)}")
    
    return working_agents, broken_agents

def test_agent_functionality():
    """Test basic functionality of working agents"""
    working_agents, broken_agents = test_agent_imports()
    
    if not working_agents:
        print("\n❌ No working agents found")
        return
    
    print(f"\n🔧 Testing Basic Functionality of {len(working_agents)} Working Agents:")
    print("-" * 50)
    
    functional_agents = []
    non_functional_agents = []
    
    for agent_info in working_agents:
        agent_name = agent_info['file']
        classes = agent_info['classes']
        
        try:
            # Try to instantiate the main agent class
            main_class_name = next((c for c in classes if c.replace('Agent', '').lower() in agent_name.lower()), classes[0])
            main_class = getattr(agent_info['module'], main_class_name)
            
            # Try basic instantiation
            agent_instance = main_class()
            
            # Check for basic methods
            has_execute = hasattr(agent_instance, 'execute')
            has_run = hasattr(agent_instance, 'run')
            has_process = hasattr(agent_instance, 'process')
            
            methods = []
            if has_execute: methods.append('execute')
            if has_run: methods.append('run')
            if has_process: methods.append('process')
            
            print(f"✅ {agent_name} ({main_class_name}): {', '.join(methods) if methods else 'basic functionality'}")
            functional_agents.append(agent_info)
            
        except Exception as e:
            print(f"❌ {agent_name}: Instantiation failed - {e}")
            non_functional_agents.append({
                **agent_info,
                'issue': f'Instantiation error: {e}'
            })
    
    print(f"\n📈 Functionality Summary:")
    print(f"  Fully Functional: {len(functional_agents)}")
    print(f"  Import Only:      {len(non_functional_agents)}")
    print(f"  Import Failed:    {len(broken_agents)}")
    
    return functional_agents, non_functional_agents, broken_agents

def identify_candidates_for_removal():
    """Identify which agents should be removed"""
    functional_agents, non_functional_agents, broken_agents = test_agent_functionality()
    
    print(f"\n🗑️  Removal Candidates Analysis:")
    print("-" * 50)
    
    # Current profile-based system makes these agents potentially redundant
    profile_system_agents = [
        'scaffolding_agent',  # Replaced by profile system
        'memory_enhanced_agents',  # Profiles provide memory context
        'ai_ops_agent',  # Ops profile covers this
        'enhanced_qa_agent',  # QA profile covers this
    ]
    
    removal_candidates = []
    keep_agents = []
    
    all_agents = functional_agents + non_functional_agents + broken_agents
    
    for agent_info in all_agents:
        agent_name = agent_info['file']
        
        if agent_name in profile_system_agents:
            print(f"🗑️  {agent_name}: Redundant with profile system")
            removal_candidates.append(agent_info)
        elif agent_name in [a['file'] for a in broken_agents]:
            print(f"🗑️  {agent_name}: Non-functional - {agent_info['issue']}")
            removal_candidates.append(agent_info)
        elif agent_name == 'hierarchical_agent_loader':
            print(f"✅ {agent_name}: Keep - Core framework component")
            keep_agents.append(agent_info)
        elif agent_name in ['pm_agent', 'ticketing_agent', 'documentation_agent', 'version_control_agent']:
            print(f"✅ {agent_name}: Keep - Core orchestration component")
            keep_agents.append(agent_info)
        else:
            print(f"⚠️  {agent_name}: Review needed")
            keep_agents.append(agent_info)
    
    print(f"\n📋 Removal Plan:")
    print(f"  Remove: {len(removal_candidates)} agents")
    print(f"  Keep:   {len(keep_agents)} agents")
    
    if removal_candidates:
        print(f"\n🗑️  Files to remove:")
        for agent in removal_candidates:
            print(f"    claude_pm/agents/{agent['file']}.py")
    
    return removal_candidates, keep_agents

if __name__ == "__main__":
    identify_candidates_for_removal()