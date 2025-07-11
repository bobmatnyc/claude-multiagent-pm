#!/usr/bin/env python3
"""
Security CLI tool for Claude PM Framework mem0AI integration.

Provides commands for API key generation, security validation, and
authentication testing.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from claude_pm.integrations.security import (
    SecurityConfig,
    create_security_config,
    validate_security_configuration,
    generate_secure_api_key,
    mask_api_key,
    get_security_recommendations,
    Mem0AIAuthenticator,
)
from claude_pm.integrations.mem0ai_integration import (
    create_mem0ai_integration,
    create_secure_mem0ai_integration,
)
from claude_pm.core.logging_config import setup_logging


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_status(status: str, message: str):
    """Print a status message with emoji."""
    emoji_map = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "💡"}
    emoji = emoji_map.get(status, "📋")
    print(f"{emoji} {message}")


def generate_api_key_command(args):
    """Generate a new secure API key."""
    print_header("API Key Generation")

    # Generate key
    api_key = generate_secure_api_key()

    print_status("success", "Generated secure API key:")
    print(f"\nAPI Key: {api_key}")
    print(f"Length: {len(api_key)} characters")

    print("\n📋 Usage Instructions:")
    print("1. Copy the API key above")
    print("2. Add to your .env file:")
    print(f"   MEM0AI_API_KEY={api_key}")
    print("3. Restart your Claude PM services")
    print("4. Store the key securely (password manager recommended)")

    print("\n⚠️ Security Notes:")
    print("- Never commit this key to version control")
    print("- Use unique keys for each environment")
    print("- Rotate keys regularly (quarterly recommended)")
    print("- Store in environment variables only")


def validate_config_command(args):
    """Validate security configuration."""
    print_header("Security Configuration Validation")

    try:
        # Load configuration from environment
        config = create_security_config()

        print("📋 Current Configuration:")
        print(f"  API Key: {'Configured' if config.api_key else 'Not configured'}")
        if config.api_key:
            print(f"  API Key (masked): {mask_api_key(config.api_key)}")
            print(f"  API Key length: {len(config.api_key)} chars")
        print(f"  TLS Enabled: {config.use_tls}")
        print(f"  SSL Verification: {config.verify_ssl}")
        print(f"  Max Auth Failures: {config.max_auth_failures}")
        print(f"  Lockout Duration: {config.auth_failure_lockout_minutes} minutes")

        # Validate configuration
        validation = validate_security_configuration(config)

        print("\n📋 Validation Results:")
        if validation["valid"]:
            print_status("success", "Configuration is valid")
        else:
            print_status("error", "Configuration has errors")

        if validation["errors"]:
            print("\n❌ Errors:")
            for error in validation["errors"]:
                print(f"  - {error}")

        if validation["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")

        if validation["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in validation["recommendations"]:
                print(f"  - {rec}")

        # Environment variables check
        print("\n📋 Environment Variables:")
        env_vars = [
            "MEM0AI_API_KEY",
            "MEM0AI_HOST",
            "MEM0AI_PORT",
            "MEM0AI_USE_TLS",
            "MEM0AI_VERIFY_SSL",
        ]

        for var in env_vars:
            value = os.getenv(var)
            if value:
                if "API_KEY" in var:
                    print(f"  {var}: {mask_api_key(value)}")
                else:
                    print(f"  {var}: {value}")
            else:
                print(f"  {var}: Not set")

    except Exception as e:
        print_status("error", f"Failed to validate configuration: {e}")
        return 1

    return 0


async def test_auth_command(args):
    """Test authentication with mem0AI service."""
    print_header("Authentication Test")

    try:
        # Get configuration
        host = args.host or os.getenv("MEM0AI_HOST", "localhost")
        port = int(args.port or os.getenv("MEM0AI_PORT", "8002"))
        api_key = args.api_key or os.getenv("MEM0AI_API_KEY")
        use_tls = args.tls or (os.getenv("MEM0AI_USE_TLS", "false").lower() == "true")

        print(f"📋 Test Configuration:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  TLS: {use_tls}")
        print(f"  API Key: {'Configured' if api_key else 'Not configured'}")

        if not api_key:
            print_status("error", "No API key provided. Use --api-key or set MEM0AI_API_KEY")
            return 1

        # Create integration
        if use_tls:
            integration = create_secure_mem0ai_integration(host=host, port=port, api_key=api_key)
        else:
            integration = create_mem0ai_integration(
                host=host, port=port, api_key=api_key, use_tls=False
            )

        print("\n📋 Testing Connection...")

        # Test connection
        async with integration:
            if integration.is_connected():
                print_status("success", "Successfully connected to mem0AI service")

                if integration.is_authenticated():
                    print_status("success", "Authentication successful")

                    # Get detailed status
                    status = integration.get_security_status()
                    print(f"\n📋 Security Status:")
                    print(f"  Connected: {status['connected']}")
                    print(f"  Authenticated: {status['authenticated']}")
                    print(f"  TLS Enabled: {status['tls_enabled']}")
                    print(f"  Base URL: {status['base_url']}")

                    # Test basic operation
                    try:
                        spaces_created = await integration.create_project_space(
                            "test_auth_project", "Authentication test project"
                        )
                        if spaces_created:
                            print_status("success", "Successfully created test project space")

                            # Clean up
                            await integration.delete_project_space("test_auth_project")
                            print_status("info", "Cleaned up test project space")
                        else:
                            print_status("warning", "Failed to create test project space")
                    except Exception as e:
                        print_status("warning", f"Project space test failed: {e}")

                else:
                    print_status("error", "Authentication failed")
                    auth_status = integration.authenticator.get_auth_status()
                    print(f"  Failure count: {auth_status['failure_count']}")
                    if auth_status["last_failure"]:
                        print(f"  Last failure: {auth_status['last_failure']}")
                    return 1
            else:
                print_status("error", "Failed to connect to mem0AI service")
                print("  Check that the service is running and accessible")
                return 1

    except Exception as e:
        print_status("error", f"Authentication test failed: {e}")
        return 1

    print_status("success", "Authentication test completed successfully")
    return 0


def security_recommendations_command(args):
    """Show security recommendations."""
    print_header("Security Recommendations")

    recommendations = get_security_recommendations()

    print("💡 Claude PM Framework Security Best Practices:\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i:2d}. {rec}")

    print("\n📋 Additional Resources:")
    print("  - Security Guide: docs/MEM0AI_SECURITY_GUIDE.md")
    print("  - Configuration Template: framework/templates/.env.template")
    print("  - Test Suite: tests/test_mem0ai_authentication.py")

    print("\n⚠️ Critical Security Checklist:")
    checklist = [
        "API key is at least 32 characters long",
        "API key is stored in environment variables only",
        "TLS is enabled for production environments",
        "SSL certificate verification is enabled",
        "Security event logging is configured",
        "Regular API key rotation schedule is in place",
        "Authentication failure monitoring is active",
    ]

    for item in checklist:
        print(f"  [ ] {item}")

    print("\n💡 Use 'claude-pm-security validate' to check your configuration!")


def status_command(args):
    """Show current security status."""
    print_header("Security Status")

    try:
        config = create_security_config()

        print("📋 Configuration Status:")
        print(f"  API Key: {'✅ Configured' if config.api_key else '❌ Not configured'}")

        if config.api_key:
            key_length = len(config.api_key)
            if key_length >= 32:
                print(f"  API Key Length: ✅ {key_length} characters")
            else:
                print(f"  API Key Length: ❌ {key_length} characters (minimum 32)")

        print(f"  TLS Enabled: {'✅' if config.use_tls else '⚠️'} {config.use_tls}")
        print(f"  SSL Verification: {'✅' if config.verify_ssl else '⚠️'} {config.verify_ssl}")

        # Validation
        validation = validate_security_configuration(config)
        print(f"\n📋 Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")

        if validation["errors"]:
            print("  Errors:")
            for error in validation["errors"]:
                print(f"    - {error}")

        if validation["warnings"]:
            print("  Warnings:")
            for warning in validation["warnings"]:
                print(f"    - {warning}")

        # Environment check
        print("\n📋 Environment Variables:")
        required_vars = ["MEM0AI_API_KEY"]
        optional_vars = ["MEM0AI_HOST", "MEM0AI_PORT", "MEM0AI_USE_TLS"]

        for var in required_vars:
            value = os.getenv(var)
            status = "✅" if value else "❌"
            print(f"  {var}: {status}")

        for var in optional_vars:
            value = os.getenv(var)
            status = "✅" if value else "⚠️"
            display_value = value if value else "Not set"
            print(f"  {var}: {status} {display_value}")

    except Exception as e:
        print_status("error", f"Failed to get security status: {e}")
        return 1

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude PM Framework Security CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-pm-security generate-key           # Generate new API key
  claude-pm-security validate              # Validate configuration
  claude-pm-security test-auth             # Test authentication
  claude-pm-security status                # Show security status
  claude-pm-security recommendations       # Show security best practices
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate API key command
    generate_parser = subparsers.add_parser("generate-key", help="Generate a new secure API key")
    generate_parser.set_defaults(func=generate_api_key_command)

    # Validate configuration command
    validate_parser = subparsers.add_parser("validate", help="Validate security configuration")
    validate_parser.set_defaults(func=validate_config_command)

    # Test authentication command
    test_parser = subparsers.add_parser("test-auth", help="Test authentication with mem0AI service")
    test_parser.add_argument("--host", help="mem0AI service host")
    test_parser.add_argument("--port", type=int, help="mem0AI service port")
    test_parser.add_argument("--api-key", help="API key to test")
    test_parser.add_argument("--tls", action="store_true", help="Use TLS/HTTPS")
    test_parser.set_defaults(func=test_auth_command)

    # Security recommendations command
    rec_parser = subparsers.add_parser("recommendations", help="Show security recommendations")
    rec_parser.set_defaults(func=security_recommendations_command)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current security status")
    status_parser.set_defaults(func=status_command)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging("claude_pm.security_cli", level="INFO")

    # Run command
    try:
        if asyncio.iscoroutinefunction(args.func):
            return asyncio.run(args.func(args))
        else:
            return args.func(args) or 0
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        print_status("error", f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
