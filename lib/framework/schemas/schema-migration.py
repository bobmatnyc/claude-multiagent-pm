"""
Claude PM Framework - Schema Migration and Validation System
Handles schema versioning, migration, and validation for memory schemas.
"""

import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ValidationError

from memory_schemas import (
    BaseMemorySchema, ProjectMemorySchema, PatternMemorySchema,
    TeamMemorySchema, ErrorMemorySchema, MemoryCategory,
    MEMORY_SCHEMA_REGISTRY
)


class SchemaVersion(str, Enum):
    """Schema version enumeration."""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


class MigrationStatus(str, Enum):
    """Migration status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SchemaMigration(BaseModel):
    """Schema migration definition."""
    
    migration_id: str
    from_version: SchemaVersion
    to_version: SchemaVersion
    description: str
    migration_function: str  # Function name as string
    created_at: datetime = datetime.now()
    
    class Config:
        use_enum_values = True


class MigrationRecord(BaseModel):
    """Record of a migration execution."""
    
    migration_id: str
    status: MigrationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    records_migrated: int = 0
    records_failed: int = 0


class SchemaValidator:
    """Validates memory schemas and handles migration."""
    
    def __init__(self):
        self.current_version = SchemaVersion.V1_0
        self.migrations: Dict[str, SchemaMigration] = {}
        self.migration_records: List[MigrationRecord] = []
        
        # Register default migrations
        self._register_default_migrations()
    
    def _register_default_migrations(self):
        """Register default schema migrations."""
        # Example migration from v1.0 to v1.1
        self.register_migration(
            migration_id="add_confidence_score",
            from_version=SchemaVersion.V1_0,
            to_version=SchemaVersion.V1_1,
            description="Add confidence_score field to all memory schemas",
            migration_function="migrate_add_confidence_score"
        )
        
        # Example migration from v1.1 to v2.0
        self.register_migration(
            migration_id="enhance_relationship_tracking",
            from_version=SchemaVersion.V1_1,
            to_version=SchemaVersion.V2_0,
            description="Enhanced relationship tracking with bidirectional links",
            migration_function="migrate_enhance_relationships"
        )
    
    def register_migration(
        self,
        migration_id: str,
        from_version: SchemaVersion,
        to_version: SchemaVersion,
        description: str,
        migration_function: str
    ):
        """Register a new schema migration."""
        migration = SchemaMigration(
            migration_id=migration_id,
            from_version=from_version,
            to_version=to_version,
            description=description,
            migration_function=migration_function
        )
        
        self.migrations[migration_id] = migration
    
    def validate_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and potentially migrate memory data.
        
        Args:
            memory_data: Raw memory data dictionary
            
        Returns:
            Validated and migrated memory data
            
        Raises:
            ValidationError: If validation fails
        """
        # Determine memory category
        category = MemoryCategory(memory_data.get("category", "project"))
        
        # Get appropriate schema
        schema_class = MEMORY_SCHEMA_REGISTRY.get(category, BaseMemorySchema)
        
        # Check if migration is needed
        data_version = memory_data.get("schema_version", "1.0")
        if data_version != self.current_version.value:
            memory_data = self._migrate_memory_data(memory_data, data_version)
        
        # Validate against schema
        try:
            validated_memory = schema_class(**memory_data)
            return validated_memory.dict()
        except ValidationError as e:
            # Try to fix common validation issues
            fixed_data = self._fix_validation_errors(memory_data, e)
            if fixed_data:
                validated_memory = schema_class(**fixed_data)
                return validated_memory.dict()
            else:
                raise e
    
    def _migrate_memory_data(self, memory_data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Migrate memory data from one schema version to another."""
        current_version = from_version
        migrated_data = memory_data.copy()
        
        # Apply migrations in sequence
        while current_version != self.current_version.value:
            migration = self._find_next_migration(current_version)
            if not migration:
                break
            
            # Apply migration
            migrated_data = self._apply_migration(migrated_data, migration)
            current_version = migration.to_version.value
        
        # Update schema version
        migrated_data["schema_version"] = self.current_version.value
        return migrated_data
    
    def _find_next_migration(self, from_version: str) -> Optional[SchemaMigration]:
        """Find the next migration to apply."""
        for migration in self.migrations.values():
            if migration.from_version.value == from_version:
                return migration
        return None
    
    def _apply_migration(self, data: Dict[str, Any], migration: SchemaMigration) -> Dict[str, Any]:
        """Apply a specific migration to memory data."""
        migration_func = getattr(self, migration.migration_function, None)
        if migration_func:
            return migration_func(data)
        else:
            print(f"Warning: Migration function {migration.migration_function} not found")
            return data
    
    def _fix_validation_errors(self, data: Dict[str, Any], error: ValidationError) -> Optional[Dict[str, Any]]:
        """Attempt to fix common validation errors automatically."""
        fixed_data = data.copy()
        
        for error_detail in error.errors():
            field = error_detail.get("loc", [])
            error_type = error_detail.get("type", "")
            
            if error_type == "missing":
                # Add missing required fields with defaults
                if field == ("priority",):
                    fixed_data["priority"] = "medium"
                elif field == ("tags",):
                    fixed_data["tags"] = []
                elif field == ("created_at",):
                    fixed_data["created_at"] = datetime.now()
                elif field == ("success_count",):
                    fixed_data["success_count"] = 0
                elif field == ("failure_count",):
                    fixed_data["failure_count"] = 0
                elif field == ("confidence_score",):
                    fixed_data["confidence_score"] = 0.5
            
            elif error_type == "type_error":
                # Fix type errors
                if field and len(field) > 0:
                    field_name = field[0]
                    if field_name in fixed_data:
                        # Try to convert to appropriate type
                        value = fixed_data[field_name]
                        if "datetime" in error_type:
                            if isinstance(value, str):
                                try:
                                    fixed_data[field_name] = datetime.fromisoformat(value)
                                except:
                                    fixed_data[field_name] = datetime.now()
                        elif "list" in error_type and not isinstance(value, list):
                            fixed_data[field_name] = [value] if value else []
        
        return fixed_data
    
    # Migration functions
    def migrate_add_confidence_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migration: Add confidence_score field."""
        if "confidence_score" not in data:
            data["confidence_score"] = 0.5
        return data
    
    def migrate_enhance_relationships(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migration: Enhance relationship tracking."""
        if "related_memories" not in data:
            data["related_memories"] = []
        if "parent_memory" not in data:
            data["parent_memory"] = None
        return data
    
    def bulk_migrate_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Migrate a bulk list of memories."""
        migrated_memories = []
        failed_migrations = []
        
        for i, memory_data in enumerate(memories):
            try:
                migrated_memory = self.validate_memory(memory_data)
                migrated_memories.append(migrated_memory)
            except ValidationError as e:
                failed_migrations.append({
                    "index": i,
                    "memory_id": memory_data.get("memory_id", "unknown"),
                    "error": str(e)
                })
        
        if failed_migrations:
            print(f"Warning: {len(failed_migrations)} memories failed migration:")
            for failure in failed_migrations:
                print(f"  - Memory {failure['memory_id']} (index {failure['index']}): {failure['error']}")
        
        return migrated_memories
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about current schema and available migrations."""
        return {
            "current_version": self.current_version.value,
            "available_migrations": [
                {
                    "migration_id": migration.migration_id,
                    "from_version": migration.from_version.value,
                    "to_version": migration.to_version.value,
                    "description": migration.description
                }
                for migration in self.migrations.values()
            ],
            "schema_categories": list(MEMORY_SCHEMA_REGISTRY.keys()),
            "migration_records": len(self.migration_records)
        }


class SchemaCompatibilityChecker:
    """Checks compatibility between different schema versions."""
    
    @staticmethod
    def check_compatibility(
        source_version: SchemaVersion,
        target_version: SchemaVersion
    ) -> Dict[str, Any]:
        """Check compatibility between two schema versions."""
        compatibility_matrix = {
            (SchemaVersion.V1_0, SchemaVersion.V1_1): {
                "compatible": True,
                "breaking_changes": False,
                "migration_required": True,
                "notes": "Added confidence_score field with default value"
            },
            (SchemaVersion.V1_1, SchemaVersion.V2_0): {
                "compatible": True,
                "breaking_changes": False,
                "migration_required": True,
                "notes": "Enhanced relationship tracking, backward compatible"
            },
            (SchemaVersion.V1_0, SchemaVersion.V2_0): {
                "compatible": True,
                "breaking_changes": False,
                "migration_required": True,
                "notes": "Requires sequential migration through v1.1"
            }
        }
        
        key = (source_version, target_version)
        if key in compatibility_matrix:
            return compatibility_matrix[key]
        
        # Same version
        if source_version == target_version:
            return {
                "compatible": True,
                "breaking_changes": False,
                "migration_required": False,
                "notes": "Same version, no migration needed"
            }
        
        # Unknown compatibility
        return {
            "compatible": False,
            "breaking_changes": True,
            "migration_required": True,
            "notes": "Unknown compatibility, manual review required"
        }


# Factory functions
def create_schema_validator() -> SchemaValidator:
    """Create and initialize a schema validator."""
    return SchemaValidator()


def validate_memory_batch(memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate a batch of memories with automatic migration."""
    validator = create_schema_validator()
    return validator.bulk_migrate_memories(memories)


def get_current_schema_version() -> str:
    """Get the current schema version."""
    return SchemaVersion.V1_0.value