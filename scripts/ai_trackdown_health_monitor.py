#!/usr/bin/env python3
"""
AI-Trackdown Tools Health Monitor
Enhanced health monitoring script specifically for validating ai-trackdown-tools integration
and cutover implementation.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the claude_pm module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pm.collectors.ai_trackdown_collector import AITrackdownHealthCollector
from claude_pm.models.health import HealthStatus


class AITrackdownHealthMonitor:
    """
    Dedicated health monitor for ai-trackdown-tools integration.
    
    Provides comprehensive validation of the AI-trackdown-tools cutover
    implementation including CLI functionality, task system health,
    and migration progress.
    """
    
    def __init__(self, framework_root: Optional[Path] = None):
        """Initialize the health monitor."""
        self.framework_root = framework_root or Path("/Users/masa/Projects/claude-pm")
        self.collector = AITrackdownHealthCollector(self.framework_root)
        self.health_report_path = self.framework_root / "logs" / "ai_trackdown_health.json"
        
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Run comprehensive health check for ai-trackdown-tools integration.
        
        Returns:
            Dictionary containing health check results
        """
        print("🔍 AI-Trackdown Tools Health Monitor")
        print("====================================")
        print(f"Framework Root: {self.framework_root}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        start_time = time.time()
        
        # Collect health reports
        print("📊 Collecting health reports...")
        health_reports = await self.collector.collect_health()
        
        # Analyze results
        report_summary = self._analyze_health_reports(health_reports)
        
        # Create comprehensive report
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "framework_root": str(self.framework_root),
            "execution_time_ms": (time.time() - start_time) * 1000,
            "total_checks": len(health_reports),
            "summary": report_summary,
            "detailed_reports": [self._serialize_health_report(report) for report in health_reports],
            "collector_stats": self.collector.get_collector_stats()
        }
        
        # Save to file
        self._save_health_report(comprehensive_report)
        
        # Display results
        self._display_health_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _analyze_health_reports(self, reports: List) -> Dict[str, Any]:
        """Analyze health reports and generate summary."""
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        error_count = 0
        unknown_count = 0
        down_count = 0
        
        critical_issues = []
        warnings = []
        
        for report in reports:
            if report.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif report.status == HealthStatus.DEGRADED:
                degraded_count += 1
                warnings.append(f"{report.name}: {report.message}")
            elif report.status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1
                critical_issues.append(f"{report.name}: {report.message}")
            elif report.status == HealthStatus.ERROR:
                error_count += 1
                critical_issues.append(f"{report.name}: {report.message}")
            elif report.status == HealthStatus.DOWN:
                down_count += 1
                critical_issues.append(f"{report.name}: {report.message}")
            else:
                unknown_count += 1
        
        total_checks = len(reports)
        health_percentage = (healthy_count / total_checks) * 100 if total_checks > 0 else 0
        
        # Determine overall health status
        if critical_issues:
            overall_status = "CRITICAL"
        elif warnings:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"
        
        return {
            "overall_status": overall_status,
            "health_percentage": round(health_percentage, 2),
            "total_checks": total_checks,
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "unhealthy_count": unhealthy_count,
            "error_count": error_count,
            "down_count": down_count,
            "unknown_count": unknown_count,
            "critical_issues": critical_issues,
            "warnings": warnings
        }
    
    def _serialize_health_report(self, report) -> Dict[str, Any]:
        """Serialize health report for JSON storage."""
        return {
            "name": report.name,
            "status": report.status.value,
            "message": report.message,
            "timestamp": report.timestamp.isoformat(),
            "response_time_ms": report.response_time_ms,
            "metrics": report.metrics or {},
            "error": report.error
        }
    
    def _save_health_report(self, report: Dict[str, Any]) -> None:
        """Save health report to file."""
        try:
            # Ensure logs directory exists
            self.health_report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.health_report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"📄 Health report saved to: {self.health_report_path}")
            
        except Exception as e:
            print(f"❌ Failed to save health report: {e}")
    
    def _display_health_summary(self, report: Dict[str, Any]) -> None:
        """Display health summary to console."""
        summary = report["summary"]
        
        print("\n" + "="*50)
        print("📋 HEALTH SUMMARY")
        print("="*50)
        
        # Overall status
        status_emoji = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "❌"
        }.get(summary["overall_status"], "❓")
        
        print(f"Overall Status: {status_emoji} {summary['overall_status']}")
        print(f"Health Percentage: {summary['health_percentage']:.1f}%")
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Execution Time: {report['execution_time_ms']:.0f}ms")
        print()
        
        # Detailed counts
        print("📊 CHECK RESULTS:")
        print(f"  ✅ Healthy: {summary['healthy_count']}")
        print(f"  ⚠️  Degraded: {summary['degraded_count']}")
        print(f"  ❌ Unhealthy: {summary['unhealthy_count']}")
        print(f"  🔥 Error: {summary['error_count']}")
        print(f"  ⬇️  Down: {summary['down_count']}")
        if summary['unknown_count'] > 0:
            print(f"  ❓ Unknown: {summary['unknown_count']}")
        print()
        
        # Critical issues
        if summary['critical_issues']:
            print("🚨 CRITICAL ISSUES:")
            for issue in summary['critical_issues']:
                print(f"  • {issue}")
            print()
        
        # Warnings
        if summary['warnings']:
            print("⚠️  WARNINGS:")
            for warning in summary['warnings']:
                print(f"  • {warning}")
            print()
        
        # Service-specific details
        print("🔧 SERVICE DETAILS:")
        for detailed_report in report['detailed_reports']:
            status_emoji = {
                "healthy": "✅",
                "degraded": "⚠️",
                "unhealthy": "❌",
                "error": "🔥",
                "down": "⬇️",
                "unknown": "❓"
            }.get(detailed_report['status'], "❓")
            
            service_name = detailed_report['name'].replace('_', ' ').title()
            print(f"  {status_emoji} {service_name}")
            print(f"    Message: {detailed_report['message']}")
            
            if detailed_report['response_time_ms']:
                print(f"    Response Time: {detailed_report['response_time_ms']:.0f}ms")
            
            if detailed_report['metrics']:
                key_metrics = self._extract_key_metrics(detailed_report['metrics'])
                if key_metrics:
                    print(f"    Key Metrics: {key_metrics}")
            
            if detailed_report['error']:
                print(f"    Error: {detailed_report['error']}")
        
        print("\n" + "="*50)
        
        # Exit with appropriate code
        if summary['overall_status'] == "CRITICAL":
            print("❌ Health check failed - critical issues detected")
            sys.exit(1)
        elif summary['overall_status'] == "WARNING":
            print("⚠️  Health check completed with warnings")
            sys.exit(0)
        else:
            print("✅ Health check passed - all systems operational")
            sys.exit(0)
    
    def _extract_key_metrics(self, metrics: Dict[str, Any]) -> str:
        """Extract key metrics for display."""
        key_info = []
        
        if 'total_items' in metrics:
            key_info.append(f"Items: {metrics['total_items']}")
        
        if 'success_rate' in metrics:
            key_info.append(f"Success Rate: {metrics['success_rate']:.1f}%")
        
        if 'working_commands' in metrics and 'total_commands' in metrics:
            key_info.append(f"Commands: {metrics['working_commands']}/{metrics['total_commands']}")
        
        if 'version' in metrics:
            key_info.append(f"Version: {metrics['version']}")
        
        if 'completion_percentage' in metrics:
            key_info.append(f"Completion: {metrics['completion_percentage']}%")
        
        return ", ".join(key_info) if key_info else ""


async def main():
    """Main entry point for the health monitor."""
    try:
        monitor = AITrackdownHealthMonitor()
        await monitor.run_comprehensive_health_check()
    except KeyboardInterrupt:
        print("\n❌ Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())