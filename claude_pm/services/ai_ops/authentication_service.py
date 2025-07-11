"""
Authentication Service

Manages API keys and authentication for multiple AI service providers
with enterprise-grade security features.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class KeyStatus(Enum):
    """API key status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"
    NEEDS_ROTATION = "needs_rotation"


@dataclass
class APIKeyInfo:
    """API key information structure."""
    provider: str
    key_id: str
    status: KeyStatus
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    usage_count: int = 0
    rotation_threshold: int = 10000
    environment: str = "production"
    
    def needs_rotation(self) -> bool:
        """Check if key needs rotation."""
        if self.status == KeyStatus.NEEDS_ROTATION:
            return True
        
        # Check usage threshold
        if self.usage_count >= self.rotation_threshold:
            return True
        
        # Check age (rotate every 90 days)
        if datetime.now() - self.created_at > timedelta(days=90):
            return True
        
        return False


class AuthenticationService:
    """
    Authentication service for AI providers.
    
    Manages API keys with encryption, rotation, and enterprise security features.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize authentication service.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self._init_encryption()
        
        # Key storage
        self.api_keys: Dict[str, str] = {}
        self.key_info: Dict[str, APIKeyInfo] = {}
        
        # Environment configuration
        self.environment = self.config.get("environment", "production")
        
        # Load existing keys
        self._load_keys()
        
        # Security settings
        self.require_encryption = self.config.get("require_encryption", True)
        self.key_rotation_days = self.config.get("key_rotation_days", 90)
        
        self.logger.info("Authentication service initialized")
    
    def _init_encryption(self):
        """Initialize encryption for key storage."""
        # Get or generate encryption key
        encryption_key = os.getenv("CLAUDE_PM_ENCRYPTION_KEY")
        
        if not encryption_key:
            # Generate new key
            password = os.getenv("CLAUDE_PM_MASTER_PASSWORD", "default_password").encode()
            salt = os.getenv("CLAUDE_PM_SALT", "default_salt").encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.cipher_suite = Fernet(key)
        else:
            self.cipher_suite = Fernet(encryption_key.encode())
    
    def _load_keys(self):
        """Load API keys from environment and secure storage."""
        # Load from environment variables
        providers = ["openai", "anthropic", "google", "openrouter", "vercel"]
        
        for provider in providers:
            # Try different environment variable patterns
            key_vars = [
                f"CLAUDE_PM_{provider.upper()}_API_KEY",
                f"{provider.upper()}_API_KEY",
                f"AI_{provider.upper()}_API_KEY"
            ]
            
            for key_var in key_vars:
                api_key = os.getenv(key_var)
                if api_key:
                    self._store_key(provider, api_key)
                    break
        
        # Load from secure storage file
        self._load_from_secure_storage()
    
    def _store_key(self, provider: str, api_key: str):
        """Store API key with metadata."""
        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        # Store encrypted key
        if self.require_encryption:
            encrypted_key = self.cipher_suite.encrypt(api_key.encode())
            self.api_keys[provider] = base64.urlsafe_b64encode(encrypted_key).decode()
        else:
            self.api_keys[provider] = api_key
        
        # Store key info
        self.key_info[provider] = APIKeyInfo(
            provider=provider,
            key_id=key_id,
            status=KeyStatus.ACTIVE,
            created_at=datetime.now(),
            environment=self.environment
        )
        
        self.logger.info(f"Stored API key for {provider} (ID: {key_id})")
    
    def _load_from_secure_storage(self):
        """Load keys from secure storage file."""
        try:
            secure_storage_path = Path.home() / ".claude-multiagent-pm" / "secure_keys.json"
            
            if secure_storage_path.exists():
                with open(secure_storage_path, 'r') as f:
                    stored_data = json.load(f)
                
                # Decrypt and load keys
                for provider, encrypted_key in stored_data.get("keys", {}).items():
                    if self.require_encryption:
                        decrypted_key = self.cipher_suite.decrypt(
                            base64.urlsafe_b64decode(encrypted_key.encode())
                        ).decode()
                        self.api_keys[provider] = encrypted_key
                    else:
                        self.api_keys[provider] = encrypted_key
                
                # Load key info
                for provider, info_data in stored_data.get("key_info", {}).items():
                    self.key_info[provider] = APIKeyInfo(
                        provider=info_data["provider"],
                        key_id=info_data["key_id"],
                        status=KeyStatus(info_data["status"]),
                        created_at=datetime.fromisoformat(info_data["created_at"]),
                        last_used=datetime.fromisoformat(info_data["last_used"]) if info_data.get("last_used") else None,
                        expires_at=datetime.fromisoformat(info_data["expires_at"]) if info_data.get("expires_at") else None,
                        usage_count=info_data.get("usage_count", 0),
                        rotation_threshold=info_data.get("rotation_threshold", 10000),
                        environment=info_data.get("environment", "production")
                    )
                
                self.logger.info(f"Loaded {len(self.api_keys)} keys from secure storage")
        
        except Exception as e:
            self.logger.error(f"Failed to load from secure storage: {e}")
    
    def _save_to_secure_storage(self):
        """Save keys to secure storage file."""
        try:
            secure_storage_path = Path.home() / ".claude-multiagent-pm" / "secure_keys.json"
            secure_storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for storage
            storage_data = {
                "keys": self.api_keys.copy(),
                "key_info": {}
            }
            
            # Convert key info to serializable format
            for provider, info in self.key_info.items():
                storage_data["key_info"][provider] = {
                    "provider": info.provider,
                    "key_id": info.key_id,
                    "status": info.status.value,
                    "created_at": info.created_at.isoformat(),
                    "last_used": info.last_used.isoformat() if info.last_used else None,
                    "expires_at": info.expires_at.isoformat() if info.expires_at else None,
                    "usage_count": info.usage_count,
                    "rotation_threshold": info.rotation_threshold,
                    "environment": info.environment
                }
            
            # Save to file
            with open(secure_storage_path, 'w') as f:
                json.dump(storage_data, f, indent=2)
            
            # Set restrictive permissions
            secure_storage_path.chmod(0o600)
            
            self.logger.info("Keys saved to secure storage")
        
        except Exception as e:
            self.logger.error(f"Failed to save to secure storage: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            API key or None
        """
        if provider not in self.api_keys:
            return None
        
        # Update usage tracking
        if provider in self.key_info:
            self.key_info[provider].usage_count += 1
            self.key_info[provider].last_used = datetime.now()
        
        # Decrypt key if needed
        if self.require_encryption:
            try:
                encrypted_key = base64.urlsafe_b64decode(self.api_keys[provider].encode())
                return self.cipher_suite.decrypt(encrypted_key).decode()
            except Exception as e:
                self.logger.error(f"Failed to decrypt key for {provider}: {e}")
                return None
        else:
            return self.api_keys[provider]
    
    def is_provider_configured(self, provider: str) -> bool:
        """
        Check if provider is configured.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider is configured
        """
        return provider in self.api_keys and self.api_keys[provider] is not None
    
    def add_api_key(self, provider: str, api_key: str) -> bool:
        """
        Add new API key for provider.
        
        Args:
            provider: Provider name
            api_key: API key
            
        Returns:
            True if successful
        """
        try:
            self._store_key(provider, api_key)
            self._save_to_secure_storage()
            return True
        except Exception as e:
            self.logger.error(f"Failed to add API key for {provider}: {e}")
            return False
    
    def remove_api_key(self, provider: str) -> bool:
        """
        Remove API key for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if successful
        """
        try:
            if provider in self.api_keys:
                del self.api_keys[provider]
            
            if provider in self.key_info:
                del self.key_info[provider]
            
            self._save_to_secure_storage()
            self.logger.info(f"Removed API key for {provider}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove API key for {provider}: {e}")
            return False
    
    async def validate_api_key(self, provider: str) -> bool:
        """
        Validate API key for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if key is valid
        """
        api_key = self.get_api_key(provider)
        if not api_key:
            return False
        
        # Provider-specific validation would go here
        # For now, just check if key exists and is not empty
        return len(api_key) > 0
    
    async def validate_all_authentications(self) -> Dict[str, Any]:
        """
        Validate all provider authentications.
        
        Returns:
            Validation results
        """
        results = {
            "all_valid": True,
            "providers": {},
            "issues": []
        }
        
        for provider in self.api_keys.keys():
            try:
                is_valid = await self.validate_api_key(provider)
                results["providers"][provider] = {
                    "valid": is_valid,
                    "last_validated": datetime.now().isoformat()
                }
                
                if not is_valid:
                    results["all_valid"] = False
                    results["issues"].append(f"Invalid API key for {provider}")
                    
            except Exception as e:
                results["all_valid"] = False
                results["providers"][provider] = {
                    "valid": False,
                    "error": str(e),
                    "last_validated": datetime.now().isoformat()
                }
                results["issues"].append(f"Validation failed for {provider}: {str(e)}")
        
        return results
    
    def get_key_info(self, provider: str) -> Optional[APIKeyInfo]:
        """
        Get key information for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            API key information or None
        """
        return self.key_info.get(provider)
    
    def get_all_key_info(self) -> Dict[str, APIKeyInfo]:
        """
        Get all key information.
        
        Returns:
            Dictionary of key information
        """
        return self.key_info.copy()
    
    def check_key_rotation_status(self) -> Dict[str, Any]:
        """
        Check which keys need rotation.
        
        Returns:
            Key rotation status
        """
        rotation_status = {
            "keys_need_rotation": False,
            "providers_needing_rotation": [],
            "rotation_recommendations": []
        }
        
        for provider, info in self.key_info.items():
            if info.needs_rotation():
                rotation_status["keys_need_rotation"] = True
                rotation_status["providers_needing_rotation"].append(provider)
                
                # Determine reason
                if info.usage_count >= info.rotation_threshold:
                    rotation_status["rotation_recommendations"].append(
                        f"{provider}: High usage count ({info.usage_count})"
                    )
                elif datetime.now() - info.created_at > timedelta(days=self.key_rotation_days):
                    rotation_status["rotation_recommendations"].append(
                        f"{provider}: Key age ({(datetime.now() - info.created_at).days} days)"
                    )
        
        return rotation_status
    
    async def rotate_key(self, provider: str, new_api_key: str) -> bool:
        """
        Rotate API key for provider.
        
        Args:
            provider: Provider name
            new_api_key: New API key
            
        Returns:
            True if successful
        """
        try:
            # Validate new key first
            old_key = self.get_api_key(provider)
            
            # Store new key
            self._store_key(provider, new_api_key)
            
            # Test new key
            if await self.validate_api_key(provider):
                # New key is valid, update status
                self.key_info[provider].status = KeyStatus.ACTIVE
                self._save_to_secure_storage()
                
                self.logger.info(f"Successfully rotated API key for {provider}")
                return True
            else:
                # New key is invalid, restore old key
                if old_key:
                    self._store_key(provider, old_key)
                
                self.logger.error(f"New API key for {provider} is invalid")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to rotate key for {provider}: {e}")
            return False
    
    def get_providers(self) -> List[str]:
        """
        Get list of configured providers.
        
        Returns:
            List of provider names
        """
        return list(self.api_keys.keys())
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get security metrics.
        
        Returns:
            Security metrics
        """
        total_keys = len(self.api_keys)
        active_keys = sum(1 for info in self.key_info.values() if info.status == KeyStatus.ACTIVE)
        keys_needing_rotation = sum(1 for info in self.key_info.values() if info.needs_rotation())
        
        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "inactive_keys": total_keys - active_keys,
            "keys_needing_rotation": keys_needing_rotation,
            "encryption_enabled": self.require_encryption,
            "last_rotation_check": datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health check results
        """
        return {
            "healthy": len(self.api_keys) > 0,
            "total_providers": len(self.api_keys),
            "encryption_enabled": self.require_encryption,
            "keys_need_rotation": any(info.needs_rotation() for info in self.key_info.values())
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"AuthenticationService(providers={len(self.api_keys)})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"<AuthenticationService providers={list(self.api_keys.keys())}>"