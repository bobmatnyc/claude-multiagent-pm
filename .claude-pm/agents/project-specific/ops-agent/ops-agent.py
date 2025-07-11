#!/usr/bin/env python3
"""
Claude-MultiAgent-PM Ops Agent - Main Interface
Project-specific operations agent with comprehensive claude-multiagent-pm knowledge.

Author: Claude-MultiAgent-PM Ops Agent
Version: 1.0.0
Date: 2025-07-11
Framework Version: 4.5.1
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/masa/Projects/claude-multiagent-pm/logs/ops-agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('claude-multiagent-pm-ops-agent')

class ClaudeMultiAgentPMOpsAgent:
    """
    Claude-MultiAgent-PM Project-Specific Operations Agent
    
    Comprehensive operations agent with deep knowledge of claude-multiagent-pm 
    framework architecture, deployment processes, and local development workflows.
    """
    
    def __init__(self):
        self.agent_info = {
            "name": "claude-multiagent-pm-ops-agent",
            "version": "1.0.0",
            "type": "project-specific",
            "tier": "project",
            "framework_version": "4.5.1",
            "created_date": "2025-07-11",
            "authority_level": "project-deployment"
        }
        
        self.project_root = Path("/Users/masa/Projects/claude-multiagent-pm")
        self.deployment_target = Path("/Users/masa/.local")
        
        # Agent module paths
        self.agent_root = self.project_root / ".claude-pm" / "agents" / "project-specific" / "ops-agent"
        self.automation_dir = self.agent_root / "automation"
        self.diagnostics_dir = self.agent_root / "diagnostics"
        self.knowledge_dir = self.agent_root / "knowledge"
        
        logger.info(f"🤖 {self.agent_info['name']} v{self.agent_info['version']} initialized")
    
    def display_agent_info(self) -> None:
        """Display comprehensive agent information."""
        print("🤖 Claude-MultiAgent-PM Ops Agent")
        print("=" * 50)
        print(f"Agent Name: {self.agent_info['name']}")
        print(f"Version: {self.agent_info['version']}")
        print(f"Type: {self.agent_info['type']}")
        print(f"Tier: {self.agent_info['tier']}")
        print(f"Framework Version: {self.agent_info['framework_version']}")
        print(f"Authority Level: {self.agent_info['authority_level']}")
        print(f"Created: {self.agent_info['created_date']}")
        print()
        print("📋 Core Responsibilities:")
        print("   • Complete framework architecture understanding and management")
        print("   • Local deployment processes and script synchronization")
        print("   • Memory system (mem0AI v0.1.113) configuration and operations")
        print("   • AI-trackdown-tools integration and management")
        print("   • Framework version management (v4.5.1) and upgrades")
        print("   • CLAUDE.md deployment tree management and synchronization")
        print("   • Health monitoring and comprehensive diagnostics")
        print("   • Development workflow automation and testing procedures")
        print("   • Script deployment and synchronization operations")
        print("   • Configuration management and validation")
        print("   • Performance optimization and monitoring")
        print("   • Backup and recovery operations")
        print()
        print("🎯 Specialization: claude-multiagent-pm local development and deployment operations")
        print("=" * 50)
    
    def display_available_operations(self) -> None:
        """Display available operations and commands."""
        print("📋 Available Operations:")
        print()
        print("🚀 Deployment Operations:")
        print("   deploy-full       - Execute complete framework deployment")
        print("   deploy-incremental - Synchronize changes without full redeployment")
        print("   deploy-scripts    - Synchronize scripts only")
        print("   deploy-binaries   - Synchronize binaries only")
        print("   deploy-claude-md  - Deploy CLAUDE.md with variable substitution")
        print()
        print("🔍 Diagnostic Operations:")
        print("   diagnose          - Run comprehensive system diagnostics")
        print("   health-check      - Quick health status check")
        print("   validate-sync     - Validate synchronization status")
        print("   check-integrations - Check external integration status")
        print()
        print("⚙️ Maintenance Operations:")
        print("   optimize          - Run performance optimization")
        print("   cleanup           - Clean logs and temporary files")
        print("   backup            - Create system backup")
        print("   rollback          - Rollback to previous state")
        print()
        print("📊 Information Operations:")
        print("   status            - Show comprehensive system status")
        print("   info              - Display agent information")
        print("   knowledge         - Access framework knowledge base")
        print("   help              - Show this help message")
        print()
        print("Usage: python ops-agent.py <operation> [options]")
        print("Example: python ops-agent.py deploy-full")
        print("Example: python ops-agent.py diagnose --verbose")
    
    def execute_full_deployment(self, options: Dict = None) -> bool:
        """Execute full deployment automation."""
        logger.info("🚀 Executing full deployment...")
        
        try:
            # Run full deployment script directly
            import subprocess
            script_path = self.automation_dir / "full-deployment.py"
            result = subprocess.run([sys.executable, str(script_path)], 
                                  capture_output=True, text=True, 
                                  cwd=str(self.project_root))
            
            if result.returncode == 0:
                logger.info("✅ Full deployment completed successfully")
                print(result.stdout)
                return True
            else:
                logger.error("❌ Full deployment completed with errors")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ Full deployment failed: {e}")
            return False
    
    def execute_incremental_sync(self, options: Dict = None) -> bool:
        """Execute incremental synchronization."""
        logger.info("🔄 Executing incremental synchronization...")
        
        try:
            # Run incremental sync script directly
            import subprocess
            script_path = self.automation_dir / "incremental-sync.py"
            result = subprocess.run([sys.executable, str(script_path)], 
                                  capture_output=True, text=True,
                                  cwd=str(self.project_root))
            
            if result.returncode == 0:
                logger.info("✅ Incremental sync completed successfully")
                print(result.stdout)
                return True
            else:
                logger.error("❌ Incremental sync completed with errors")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ Incremental sync failed: {e}")
            return False
    
    def run_comprehensive_diagnostics(self, options: Dict = None) -> bool:
        """Run comprehensive system diagnostics."""
        logger.info("🔍 Running comprehensive diagnostics...")
        
        try:
            # Run diagnostics script directly
            import subprocess
            script_path = self.diagnostics_dir / "comprehensive-diagnostics.py"
            result = subprocess.run([sys.executable, str(script_path)], 
                                  capture_output=True, text=True,
                                  cwd=str(self.project_root))
            
            if result.returncode == 0:
                logger.info("✅ Diagnostics completed successfully")
                print(result.stdout)
                return True
            else:
                logger.error("❌ Diagnostics found critical issues")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ Diagnostics failed: {e}")
            return False
    
    def show_system_status(self) -> None:
        """Show comprehensive system status."""
        print("📊 Claude-MultiAgent-PM System Status")
        print("=" * 50)
        
        # Framework status
        print("🔧 Framework Status:")
        try:
            sys.path.insert(0, str(self.project_root))
            import claude_pm
            print(f"   ✅ Framework Core: Available (v{self.agent_info['framework_version']})")
        except ImportError:
            print("   ❌ Framework Core: Import Error")
        except Exception as e:
            print(f"   ❌ Framework Core: Error - {e}")
        
        # Deployment status
        print("\n🚀 Deployment Status:")
        scripts_target = self.deployment_target / "scripts"
        bin_target = self.deployment_target / "bin"
        claude_md_target = self.deployment_target / "CLAUDE.md"
        
        print(f"   Scripts: {'✅ Deployed' if scripts_target.exists() else '❌ Missing'}")
        print(f"   Binaries: {'✅ Deployed' if bin_target.exists() else '❌ Missing'}")
        print(f"   CLAUDE.md: {'✅ Deployed' if claude_md_target.exists() else '❌ Missing'}")
        
        # Agent hierarchy status
        print("\n🤖 Agent Hierarchy:")
        hierarchy_config = self.project_root / ".claude-pm" / "agents" / "hierarchy.yaml"
        registry_file = self.project_root / ".claude-pm" / "agents" / "registry.json"
        
        print(f"   Configuration: {'✅ Available' if hierarchy_config.exists() else '❌ Missing'}")
        print(f"   Registry: {'✅ Available' if registry_file.exists() else '❌ Missing'}")
        
        # Integration status
        print("\n🔗 Integration Status:")
        
        # mem0AI
        try:
            import mem0
            print("   mem0AI: ✅ Available")
        except ImportError:
            print("   mem0AI: ❌ Not Installed")
        
        # AI-trackdown
        aitrackdown_path = bin_target / "aitrackdown"
        print(f"   AI-trackdown: {'✅ Available' if aitrackdown_path.exists() else '❌ Missing'}")
        
        print("=" * 50)
        print(f"Status generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def access_knowledge_base(self, topic: str = None) -> None:
        """Access framework knowledge base."""
        print("📚 Framework Knowledge Base")
        print("=" * 40)
        
        if topic:
            # Show specific topic if requested
            topic_file = self.knowledge_dir / f"{topic}.md"
            if topic_file.exists():
                print(f"📖 Topic: {topic}")
                print("-" * 30)
                try:
                    with open(topic_file, 'r') as f:
                        content = f.read()
                    print(content[:2000])  # Show first 2000 characters
                    if len(content) > 2000:
                        print("\n... (truncated, see full file for complete content)")
                except Exception as e:
                    print(f"❌ Error reading topic file: {e}")
            else:
                print(f"❌ Topic '{topic}' not found")
        else:
            # Show available topics
            print("📋 Available Knowledge Topics:")
            try:
                knowledge_files = list(self.knowledge_dir.glob("*.md"))
                for kf in knowledge_files:
                    topic_name = kf.stem.replace("-", " ").title()
                    print(f"   • {topic_name} ({kf.name})")
                
                print(f"\nTotal: {len(knowledge_files)} knowledge files available")
                print("\nUsage: python ops-agent.py knowledge <topic-name>")
                print("Example: python ops-agent.py knowledge framework-architecture")
            except Exception as e:
                print(f"❌ Error accessing knowledge base: {e}")
    
    def execute_operation(self, operation: str, options: Dict = None) -> bool:
        """Execute the specified operation."""
        if options is None:
            options = {}
        
        logger.info(f"🔄 Executing operation: {operation}")
        
        # Operation routing
        operations = {
            "deploy-full": self.execute_full_deployment,
            "deploy-incremental": self.execute_incremental_sync,
            "diagnose": self.run_comprehensive_diagnostics,
            "status": lambda opts: (self.show_system_status(), True)[1],
            "info": lambda opts: (self.display_agent_info(), True)[1],
            "help": lambda opts: (self.display_available_operations(), True)[1],
            "knowledge": lambda opts: (self.access_knowledge_base(opts.get("topic")), True)[1]
        }
        
        if operation in operations:
            try:
                return operations[operation](options)
            except Exception as e:
                logger.error(f"❌ Operation {operation} failed: {e}")
                return False
        else:
            logger.error(f"❌ Unknown operation: {operation}")
            print(f"❌ Unknown operation: {operation}")
            print("Run 'python ops-agent.py help' to see available operations")
            return False

def main():
    """Main CLI interface for the Ops Agent."""
    parser = argparse.ArgumentParser(
        description="Claude-MultiAgent-PM Project-Specific Operations Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Operations:
  deploy-full       Execute complete framework deployment
  deploy-incremental Synchronize changes without full redeployment
  diagnose          Run comprehensive system diagnostics
  status            Show comprehensive system status
  info              Display agent information
  knowledge [topic] Access framework knowledge base
  help              Show available operations

Examples:
  python ops-agent.py deploy-full
  python ops-agent.py diagnose --verbose
  python ops-agent.py knowledge framework-architecture
  python ops-agent.py status
        """
    )
    
    parser.add_argument(
        "operation",
        nargs="?",
        default="info",
        help="Operation to execute (default: info)"
    )
    
    parser.add_argument(
        "topic",
        nargs="?",
        help="Topic for knowledge base access"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force operation (skip confirmations)"
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize agent
    agent = ClaudeMultiAgentPMOpsAgent()
    
    # Prepare options
    options = {
        "verbose": args.verbose,
        "force": args.force,
        "topic": args.topic
    }
    
    # Execute operation
    success = agent.execute_operation(args.operation, options)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()