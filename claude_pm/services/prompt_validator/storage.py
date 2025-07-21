"""
Storage operations for prompt validation framework.

This module handles all persistence operations including saving and loading
test scenarios, results, reports, and analytics data.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .models import (
    TestScenario, TestResult, ABTestResult, 
    ValidationReport
)


class StorageManager:
    """Manages storage operations for prompt validation data"""
    
    def __init__(self, base_path: str = '.claude-pm/prompt_validation'):
        self.logger = logging.getLogger(__name__)
        
        # Storage paths
        self.base_path = Path(base_path)
        self.scenarios_path = self.base_path / 'scenarios'
        self.results_path = self.base_path / 'results'
        self.reports_path = self.base_path / 'reports'
        self.ab_tests_path = self.base_path / 'ab_tests'
        
        # Create directories
        for path in [self.scenarios_path, self.results_path, self.reports_path, self.ab_tests_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    # Scenario storage
    async def save_scenario(self, scenario: TestScenario):
        """Save test scenario to storage"""
        try:
            scenario_file = self.scenarios_path / f"{scenario.scenario_id}.json"
            with open(scenario_file, 'w') as f:
                json.dump(asdict(scenario), f, indent=2)
            self.logger.debug(f"Saved scenario: {scenario.scenario_id}")
        except Exception as e:
            self.logger.error(f"Error saving scenario: {e}")
    
    async def load_scenario(self, scenario_id: str) -> Optional[TestScenario]:
        """Load test scenario from storage"""
        try:
            scenario_file = self.scenarios_path / f"{scenario_id}.json"
            if not scenario_file.exists():
                return None
            
            with open(scenario_file, 'r') as f:
                data = json.load(f)
            
            return TestScenario(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading scenario {scenario_id}: {e}")
            return None
    
    async def list_scenarios(self) -> List[str]:
        """List all scenario IDs"""
        try:
            return [f.stem for f in self.scenarios_path.glob("*.json")]
        except Exception as e:
            self.logger.error(f"Error listing scenarios: {e}")
            return []
    
    # Report storage
    async def save_validation_report(self, report: ValidationReport):
        """Save validation report to storage"""
        try:
            report_file = self.reports_path / f"{report.report_id}.json"
            with open(report_file, 'w') as f:
                report_dict = asdict(report)
                report_dict['timestamp'] = report.timestamp.isoformat()
                # Convert test results
                report_dict['test_results'] = [
                    {
                        **asdict(result),
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in report.test_results
                ]
                json.dump(report_dict, f, indent=2)
            self.logger.debug(f"Saved validation report: {report.report_id}")
        except Exception as e:
            self.logger.error(f"Error saving validation report: {e}")
    
    async def load_validation_report(self, report_id: str) -> Optional[ValidationReport]:
        """Load validation report from storage"""
        try:
            report_file = self.reports_path / f"{report_id}.json"
            if not report_file.exists():
                return None
            
            with open(report_file, 'r') as f:
                data = json.load(f)
            
            # Convert timestamps
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            for result in data['test_results']:
                result['timestamp'] = datetime.fromisoformat(result['timestamp'])
            
            # Reconstruct objects
            data['test_results'] = [TestResult(**r) for r in data['test_results']]
            
            return ValidationReport(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading validation report {report_id}: {e}")
            return None
    
    # A/B test storage
    async def save_ab_test_result(self, ab_result: ABTestResult):
        """Save A/B test result to storage"""
        try:
            ab_file = self.ab_tests_path / f"{ab_result.test_id}.json"
            with open(ab_file, 'w') as f:
                ab_dict = asdict(ab_result)
                ab_dict['timestamp'] = ab_result.timestamp.isoformat()
                # Convert test results
                ab_dict['prompt_a_results'] = [
                    {
                        **asdict(result),
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in ab_result.prompt_a_results
                ]
                ab_dict['prompt_b_results'] = [
                    {
                        **asdict(result),
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in ab_result.prompt_b_results
                ]
                json.dump(ab_dict, f, indent=2)
            self.logger.debug(f"Saved A/B test result: {ab_result.test_id}")
        except Exception as e:
            self.logger.error(f"Error saving A/B test result: {e}")
    
    async def load_ab_test_result(self, test_id: str) -> Optional[ABTestResult]:
        """Load A/B test result from storage"""
        try:
            ab_file = self.ab_tests_path / f"{test_id}.json"
            if not ab_file.exists():
                return None
            
            with open(ab_file, 'r') as f:
                data = json.load(f)
            
            # Convert timestamps and results
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            
            for result_list in ['prompt_a_results', 'prompt_b_results']:
                for result in data[result_list]:
                    result['timestamp'] = datetime.fromisoformat(result['timestamp'])
                data[result_list] = [TestResult(**r) for r in data[result_list]]
            
            return ABTestResult(**data)
            
        except Exception as e:
            self.logger.error(f"Error loading A/B test result {test_id}: {e}")
            return None
    
    # Benchmark storage
    async def save_benchmark_results(self, benchmark_results: Dict[str, Any]):
        """Save benchmark results to storage"""
        try:
            benchmark_file = self.results_path / f"benchmark_{benchmark_results['prompt_id']}_{int(datetime.now().timestamp())}.json"
            with open(benchmark_file, 'w') as f:
                json.dump(benchmark_results, f, indent=2)
            self.logger.debug(f"Saved benchmark results for: {benchmark_results['prompt_id']}")
        except Exception as e:
            self.logger.error(f"Error saving benchmark results: {e}")
    
    # Analytics data loading
    async def load_test_results_since(self, since_date: datetime) -> List[TestResult]:
        """Load test results since given date"""
        results = []
        
        try:
            # Load from validation reports
            for report_file in self.reports_path.glob("*.json"):
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    
                    report_timestamp = datetime.fromisoformat(report_data['timestamp'])
                    if report_timestamp >= since_date:
                        for result_data in report_data['test_results']:
                            result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                            results.append(TestResult(**result_data))
                            
                except Exception as e:
                    self.logger.error(f"Error loading report {report_file}: {e}")
                    continue
            
            # Load from A/B test results
            for ab_file in self.ab_tests_path.glob("*.json"):
                try:
                    with open(ab_file, 'r') as f:
                        ab_data = json.load(f)
                    
                    ab_timestamp = datetime.fromisoformat(ab_data['timestamp'])
                    if ab_timestamp >= since_date:
                        for result_data in ab_data['prompt_a_results'] + ab_data['prompt_b_results']:
                            result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
                            results.append(TestResult(**result_data))
                            
                except Exception as e:
                    self.logger.error(f"Error loading A/B test {ab_file}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error loading test results since {since_date}: {e}")
        
        return results
    
    # Cleanup operations
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data files"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            # Clean up each directory
            for directory in [self.results_path, self.reports_path, self.ab_tests_path]:
                for file_path in directory.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_date:
                        file_path.unlink()
                        self.logger.info(f"Deleted old file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    # Export/Import operations
    async def export_all_data(self, export_path: str):
        """Export all validation data to a single file"""
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'scenarios': [],
                'reports': [],
                'ab_tests': []
            }
            
            # Export scenarios
            for scenario_file in self.scenarios_path.glob("*.json"):
                with open(scenario_file, 'r') as f:
                    export_data['scenarios'].append(json.load(f))
            
            # Export reports
            for report_file in self.reports_path.glob("*.json"):
                with open(report_file, 'r') as f:
                    export_data['reports'].append(json.load(f))
            
            # Export A/B tests
            for ab_file in self.ab_tests_path.glob("*.json"):
                with open(ab_file, 'r') as f:
                    export_data['ab_tests'].append(json.load(f))
            
            # Write export file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported all data to: {export_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")