#!/usr/bin/env python3
"""
Production Environment Validation Script for Claude PM Framework.

Validates that all required environment variables are properly configured
for production deployment, with special focus on mem0AI authentication.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.integrations.security import (
    create_security_config, validate_security_configuration,
    mask_api_key, MIN_API_KEY_LENGTH
)


class ProductionValidator:
    """Validates production environment configuration."""
    
    def __init__(self):
        """Initialize validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_total = 0
    
    def check(self, condition: bool, success_msg: str, error_msg: str, is_warning: bool = False) -> bool:
        """Check a condition and record results."""
        self.checks_total += 1
        
        if condition:
            self.checks_passed += 1
            print(f"✅ {success_msg}")
            return True
        else:
            if is_warning:
                self.warnings.append(error_msg)
                print(f"⚠️  {error_msg}")
            else:
                self.errors.append(error_msg)
                print(f"❌ {error_msg}")
            return False
    
    def validate_api_key(self, api_key: Optional[str], env_name: str) -> bool:
        """Validate API key format and security."""
        if not api_key:
            return self.check(False, "", f"{env_name} is not set")
        
        # Check length
        length_ok = len(api_key) >= MIN_API_KEY_LENGTH
        self.check(
            length_ok,
            f"{env_name} has sufficient length ({len(api_key)} chars)",
            f"{env_name} is too short ({len(api_key)} chars, minimum {MIN_API_KEY_LENGTH})"
        )
        
        # Check for placeholder values
        placeholder_patterns = [
            "REPLACE_WITH_",
            "your_",
            "example_",
            "test_key_with_sufficient_length",
            "dev_key_with_sufficient_length"
        ]
        
        is_placeholder = any(pattern in api_key for pattern in placeholder_patterns)
        self.check(
            not is_placeholder,
            f"{env_name} appears to be a real API key",
            f"{env_name} appears to be a placeholder value"
        )
        
        # Check entropy (basic check)
        unique_chars = len(set(api_key.lower()))
        entropy_ok = unique_chars >= 8  # At least 8 unique characters
        self.check(
            entropy_ok,
            f"{env_name} has good character diversity",
            f"{env_name} has low character diversity (may be weak)",
            is_warning=True
        )
        
        return length_ok and not is_placeholder
    
    def validate_boolean_env(self, env_name: str, expected: bool, description: str) -> bool:
        """Validate boolean environment variable."""
        value = os.getenv(env_name, "").lower()
        expected_str = str(expected).lower()
        
        return self.check(
            value == expected_str,
            f"{env_name} is correctly set to {expected}",
            f"{env_name} should be '{expected_str}' for production but is '{value}'"
        )
    
    def validate_required_env(self, env_name: str, description: str) -> bool:
        """Validate that a required environment variable is set."""
        value = os.getenv(env_name)
        
        return self.check(
            value is not None and value.strip() != "",
            f"{env_name} is configured",
            f"{env_name} is required for production but not set"
        )
    
    def validate_mem0ai_security(self) -> bool:
        """Validate mem0AI security configuration."""
        print("\n🔐 Validating mem0AI Security Configuration")
        print("=" * 50)
        
        # Check API key
        api_key = os.getenv("MEM0AI_API_KEY")
        key_valid = self.validate_api_key(api_key, "MEM0AI_API_KEY")
        
        # Check TLS configuration
        tls_valid = self.validate_boolean_env("MEM0AI_USE_TLS", True, "TLS encryption")
        ssl_valid = self.validate_boolean_env("MEM0AI_VERIFY_SSL", True, "SSL verification")
        
        # Check host configuration
        host = os.getenv("MEM0AI_HOST", "localhost")
        host_valid = self.check(
            host != "localhost",
            f"MEM0AI_HOST is configured for production ({host})",
            "MEM0AI_HOST is set to localhost (should be production host)",
            is_warning=True
        )
        
        # Test security configuration
        try:
            security_config = create_security_config()
            validation = validate_security_configuration(security_config)
            
            config_valid = self.check(
                validation["valid"],
                "Security configuration validation passed",
                f"Security configuration validation failed: {validation.get('errors', [])}"
            )
            
            if validation.get("warnings"):
                for warning in validation["warnings"]:
                    self.warnings.append(f"Security config warning: {warning}")
                    print(f"⚠️  Security config warning: {warning}")
            
        except Exception as e:
            config_valid = self.check(False, "", f"Failed to validate security config: {e}")
        
        return key_valid and tls_valid and ssl_valid and config_valid
    
    def validate_github_integration(self) -> bool:
        """Validate GitHub integration configuration."""
        print("\n🐙 Validating GitHub Integration")
        print("=" * 50)
        
        # Check GitHub token
        token = os.getenv("GITHUB_TOKEN")
        token_valid = self.check(
            token and not any(placeholder in token for placeholder in ["REPLACE_WITH_", "your_"]),
            "GITHUB_TOKEN is configured",
            "GITHUB_TOKEN is not set or contains placeholder value"
        )
        
        # Check GitHub owner
        owner = os.getenv("GITHUB_OWNER")
        owner_valid = self.check(
            owner and not any(placeholder in owner for placeholder in ["REPLACE_WITH_", "your_"]),
            f"GITHUB_OWNER is configured ({owner})",
            "GITHUB_OWNER is not set or contains placeholder value"
        )
        
        return token_valid and owner_valid
    
    def validate_security_settings(self) -> bool:
        """Validate general security settings."""
        print("\n🛡️  Validating General Security Settings")
        print("=" * 50)
        
        # Check session secret
        session_secret = os.getenv("CLAUDE_PM_SESSION_SECRET")
        secret_valid = self.check(
            session_secret and len(session_secret) >= 32 and "REPLACE_WITH_" not in session_secret,
            "CLAUDE_PM_SESSION_SECRET is properly configured",
            "CLAUDE_PM_SESSION_SECRET is not set or too short or contains placeholder"
        )
        
        # Check security mode
        security_mode = os.getenv("CLAUDE_PM_SECURITY_MODE", "").lower()
        mode_valid = self.check(
            security_mode == "production",
            "CLAUDE_PM_SECURITY_MODE is set to production",
            f"CLAUDE_PM_SECURITY_MODE should be 'production' but is '{security_mode}'"
        )
        
        # Check SSL configuration
        ssl_enabled = os.getenv("CLAUDE_PM_SSL_ENABLED", "").lower()
        ssl_valid = self.check(
            ssl_enabled == "true",
            "CLAUDE_PM_SSL_ENABLED is enabled",
            "CLAUDE_PM_SSL_ENABLED should be 'true' for production",
            is_warning=True
        )
        
        return secret_valid and mode_valid
    
    def validate_monitoring_settings(self) -> bool:
        """Validate monitoring and alerting configuration."""
        print("\n📊 Validating Monitoring Configuration")
        print("=" * 50)
        
        # Check health monitoring
        health_enabled = os.getenv("CLAUDE_PM_ENABLE_HEALTH_MONITORING", "").lower()
        health_valid = self.check(
            health_enabled == "true",
            "Health monitoring is enabled",
            "CLAUDE_PM_ENABLE_HEALTH_MONITORING should be 'true' for production"
        )
        
        # Check alerting
        alerting_enabled = os.getenv("CLAUDE_PM_ENABLE_ALERTING", "").lower()
        alert_valid = self.check(
            alerting_enabled == "true",
            "Alerting is enabled",
            "CLAUDE_PM_ENABLE_ALERTING should be 'true' for production"
        )
        
        # Check email alerts configuration
        email_alerts = os.getenv("CLAUDE_PM_EMAIL_ALERTS", "").lower()
        if email_alerts == "true":
            smtp_host = os.getenv("CLAUDE_PM_SMTP_HOST")
            smtp_user = os.getenv("CLAUDE_PM_SMTP_USER")
            smtp_pass = os.getenv("CLAUDE_PM_SMTP_PASS")
            
            email_config_valid = self.check(
                all([smtp_host, smtp_user, smtp_pass]) and 
                not any("REPLACE_WITH_" in str(val) for val in [smtp_host, smtp_user, smtp_pass]),
                "Email alerting is properly configured",
                "Email alerting is enabled but SMTP settings contain placeholders"
            )
        else:
            email_config_valid = True
            print("ℹ️  Email alerting is disabled")
        
        return health_valid and alert_valid and email_config_valid
    
    def run_validation(self) -> bool:
        """Run complete production validation."""
        print("🚀 Claude PM Framework - Production Environment Validation")
        print("=" * 60)
        print(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
        print(f"Validation time: {os.popen('date').read().strip()}")
        print("=" * 60)
        
        # Run all validation checks
        mem0ai_valid = self.validate_mem0ai_security()
        github_valid = self.validate_github_integration()
        security_valid = self.validate_security_settings()
        monitoring_valid = self.validate_monitoring_settings()
        
        # Print summary
        print("\n📋 Validation Summary")
        print("=" * 50)
        print(f"Total checks: {self.checks_total}")
        print(f"Passed: {self.checks_passed}")
        print(f"Failed: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        success_rate = (self.checks_passed / self.checks_total * 100) if self.checks_total > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        # Print detailed results
        if self.errors:
            print(f"\n❌ Critical Issues ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        # Overall result
        all_valid = len(self.errors) == 0
        
        if all_valid:
            print("\n✅ Production Environment Validation PASSED")
            print("   Your environment is ready for production deployment!")
        else:
            print("\n❌ Production Environment Validation FAILED")
            print("   Please fix the critical issues before deploying to production.")
        
        if self.warnings:
            print("\n💡 Consider addressing the warnings for optimal security.")
        
        return all_valid


def main():
    """Main validation entry point."""
    validator = ProductionValidator()
    
    # Check if we're actually validating production environment
    env = os.getenv("ENVIRONMENT", "").lower()
    if env != "production":
        print(f"⚠️  Warning: ENVIRONMENT is '{env}', expected 'production'")
        
        # Ask for confirmation
        response = input("Continue validation anyway? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Validation cancelled.")
            return 1
    
    # Run validation
    success = validator.run_validation()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())