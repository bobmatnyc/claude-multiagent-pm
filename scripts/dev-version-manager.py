#!/usr/bin/env python3
"""
Development Version Manager for Claude PM Framework
Manages service version increments based on actual work completed.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.utils.subsystem_versions import (
    SubsystemVersionManager,
    increment_version,
    VersionStatus
)


class DevelopmentVersionManager:
    """Enhanced version manager for development workflows."""
    
    def __init__(self):
        self.manager = SubsystemVersionManager()
        self.work_log = []
        
    async def initialize(self):
        """Initialize the manager and scan current versions."""
        await self.manager.scan_subsystem_versions()
        
    async def show_current_versions(self):
        """Display current version status."""
        print("🔍 Current Service Versions:")
        print("=" * 50)
        
        # Get all available services
        services = self.manager.get_all_available_subsystems()
        
        for service in sorted(services):
            version = self.manager.get_version(service)
            if version:
                print(f"  ✅ {service}: {version}")
            else:
                print(f"  ❌ {service}: not found")
        
        print()
        
    async def increment_service_version(self, service: str, reason: str = "Development work completed"):
        """Increment version for a specific service."""
        try:
            current_version = self.manager.get_version(service)
            if not current_version:
                print(f"❌ Service '{service}' not found or has no version")
                return False
            
            new_version = increment_version(current_version, "serial")
            
            # Update the version file
            success = await self.manager.update_version(service, new_version, backup=True)
            
            if success:
                print(f"✅ {service}: {current_version} → {new_version}")
                
                # Log the work
                self.work_log.append({
                    "service": service,
                    "from_version": current_version,
                    "to_version": new_version,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Re-scan to update internal state
                await self.manager.scan_subsystem_versions()
                return True
            else:
                print(f"❌ Failed to update {service} version")
                return False
                
        except Exception as e:
            print(f"❌ Error incrementing {service} version: {e}")
            return False
    
    async def increment_multiple_services(self, services: List[str], reason: str = "Development work completed"):
        """Increment versions for multiple services."""
        print(f"🔄 Incrementing versions for {len(services)} services...")
        print(f"📝 Reason: {reason}")
        print()
        
        results = {}
        for service in services:
            success = await self.increment_service_version(service, reason)
            results[service] = success
            
        # Summary
        successful = sum(1 for success in results.values() if success)
        print(f"\n📊 Summary: {successful}/{len(services)} services updated successfully")
        
        return results
    
    async def validate_all_versions(self):
        """Validate all service versions for consistency."""
        print("🔍 Validating all service versions...")
        print("=" * 40)
        
        # Get current versions
        await self.manager.scan_subsystem_versions()
        
        # Generate comprehensive requirements based on current versions
        requirements = {}
        for service in self.manager.get_all_available_subsystems():
            version = self.manager.get_version(service)
            if version:
                requirements[service] = version
        
        # Validate compatibility
        checks = await self.manager.validate_compatibility(requirements)
        
        compatible_count = sum(1 for check in checks if check.compatible)
        total_checks = len(checks)
        
        for check in checks:
            status = "✅" if check.compatible else "❌"
            print(f"{status} {check.subsystem}: {check.current_version}")
        
        print(f"\n📊 Validation Results: {compatible_count}/{total_checks} services valid")
        
        return compatible_count == total_checks
    
    def show_work_log(self):
        """Display the work log for this session."""
        if not self.work_log:
            print("📝 No version changes made this session")
            return
        
        print("📝 Work Log (This Session):")
        print("=" * 30)
        
        for entry in self.work_log:
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
            print(f"[{timestamp}] {entry['service']}: {entry['from_version']} → {entry['to_version']}")
            print(f"           Reason: {entry['reason']}")
            print()
    
    def export_work_log(self, filepath: str):
        """Export work log to JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.work_log, f, indent=2)
            print(f"✅ Work log exported to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Failed to export work log: {e}")
            return False
    
    async def interactive_mode(self):
        """Interactive mode for version management."""
        print("🚀 Interactive Development Version Manager")
        print("=" * 45)
        print("Commands:")
        print("  show    - Show current versions")
        print("  inc     - Increment service version")
        print("  batch   - Increment multiple services")
        print("  validate - Validate all versions")
        print("  log     - Show work log")
        print("  export  - Export work log")
        print("  help    - Show this help")
        print("  quit    - Exit")
        print()
        
        while True:
            try:
                command = input("dev-version> ").strip().lower()
                
                if command == "quit" or command == "q":
                    break
                elif command == "show":
                    await self.show_current_versions()
                elif command == "inc":
                    try:
                        service = input("Service name: ").strip()
                        reason = input("Reason (optional): ").strip()
                        if not reason:
                            reason = "Development work completed"
                        await self.increment_service_version(service, reason)
                    except EOFError:
                        print("\nEOF encountered. Exiting interactive mode.")
                        break
                elif command == "batch":
                    try:
                        services_input = input("Services (comma-separated): ").strip()
                        services = [s.strip() for s in services_input.split(",") if s.strip()]
                        reason = input("Reason (optional): ").strip()
                        if not reason:
                            reason = "Development work completed"
                        await self.increment_multiple_services(services, reason)
                    except EOFError:
                        print("\nEOF encountered. Exiting interactive mode.")
                        break
                elif command == "validate":
                    await self.validate_all_versions()
                elif command == "log":
                    self.show_work_log()
                elif command == "export":
                    try:
                        filepath = input("Export file path: ").strip()
                        if not filepath:
                            filepath = f"work_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        self.export_work_log(filepath)
                    except EOFError:
                        print("\nEOF encountered. Exiting interactive mode.")
                        break
                elif command == "help":
                    print("Available commands: show, inc, batch, validate, log, export, help, quit")
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nEOF encountered. Exiting interactive mode.")
                break
            except Exception as e:
                print(f"Error: {e}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Development Version Manager for Claude PM Framework"
    )
    parser.add_argument(
        "--show", 
        action="store_true", 
        help="Show current versions"
    )
    parser.add_argument(
        "--increment", 
        type=str,
        help="Increment version for specific service"
    )
    parser.add_argument(
        "--batch", 
        type=str,
        help="Increment versions for multiple services (comma-separated)"
    )
    parser.add_argument(
        "--reason", 
        type=str,
        default="Development work completed",
        help="Reason for version increment"
    )
    parser.add_argument(
        "--validate", 
        action="store_true",
        help="Validate all service versions"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Start interactive mode"
    )
    parser.add_argument(
        "--export-log", 
        type=str,
        help="Export work log to file"
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    dev_manager = DevelopmentVersionManager()
    await dev_manager.initialize()
    
    # Handle command line arguments
    if args.show:
        await dev_manager.show_current_versions()
    elif args.increment:
        await dev_manager.increment_service_version(args.increment, args.reason)
    elif args.batch:
        services = [s.strip() for s in args.batch.split(",") if s.strip()]
        await dev_manager.increment_multiple_services(services, args.reason)
    elif args.validate:
        await dev_manager.validate_all_versions()
    elif args.export_log:
        dev_manager.export_work_log(args.export_log)
    elif args.interactive:
        await dev_manager.interactive_mode()
    else:
        # Default: show current versions
        await dev_manager.show_current_versions()
        print("💡 Use --help for more options, or --interactive for interactive mode")


if __name__ == "__main__":
    asyncio.run(main())