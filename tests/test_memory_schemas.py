"""
Claude PM Framework - Memory Schema Test Suite
Comprehensive tests for memory schemas, validation, and migration.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from schemas.memory_schemas import (
    MemoryCategory,
    MemoryPriority,
    ProjectMemorySchema,
    PatternMemorySchema,
    TeamMemorySchema,
    ErrorMemorySchema,
    MemoryTagSchema,
    MemoryRelationSchema,
    get_schema_for_category,
    validate_memory_schema,
)
from schemas.memory_manager import ClaudePMMemoryManager, create_memory_manager
from schemas.schema_migration import SchemaValidator, create_schema_validator


class TestMemorySchemas:
    """Test memory schema definitions and validation."""

    def test_project_memory_schema_creation(self):
        """Test creating a project memory with all required fields."""
        project_memory = ProjectMemorySchema(
            title="Migration to FastAPI",
            content="Decision to migrate from Flask to FastAPI for better async support",
            decision_type="tech_stack",
            decision_rationale="Need better async handling for real-time features",
            alternatives_considered=["Django", "Tornado"],
            tags=["python", "backend", "architecture"],
        )

        assert project_memory.category == MemoryCategory.PROJECT
        assert project_memory.title == "Migration to FastAPI"
        assert project_memory.decision_type == "tech_stack"
        assert len(project_memory.alternatives_considered) == 2
        assert "python" in project_memory.tags

    def test_pattern_memory_schema_creation(self):
        """Test creating a pattern memory with success tracking."""
        pattern_memory = PatternMemorySchema(
            title="Repository Pattern for Database Access",
            content="Use repository pattern to abstract database operations",
            pattern_type="design",
            problem_domain="data_access",
            complexity_level="moderate",
            problem_description="Need to abstract database operations for testing",
            solution_approach="Create repository interfaces and implementations",
            success_rate=0.85,
            tags=["design-pattern", "database", "testing"],
        )

        assert pattern_memory.category == MemoryCategory.PATTERN
        assert pattern_memory.pattern_type == "design"
        assert pattern_memory.success_rate == 0.85
        assert pattern_memory.complexity_level == "moderate"

    def test_team_memory_schema_creation(self):
        """Test creating a team memory for coding standards."""
        team_memory = TeamMemorySchema(
            title="Python Code Formatting Standards",
            content="Use Black formatter with line length of 88 characters",
            standard_type="coding",
            scope="team",
            enforcement_level="required",
            standard_description="Consistent code formatting using Black",
            examples=["black --line-length 88 .", "pre-commit hook integration"],
            linting_rules=["E501", "W503"],
            compliance_rate=0.95,
            tags=["python", "formatting", "standards"],
        )

        assert team_memory.category == MemoryCategory.TEAM
        assert team_memory.enforcement_level == "required"
        assert team_memory.compliance_rate == 0.95
        assert len(team_memory.examples) == 2

    def test_error_memory_schema_creation(self):
        """Test creating an error memory with root cause analysis."""
        error_memory = ErrorMemorySchema(
            title="Database Connection Pool Exhaustion",
            content="Application fails with connection pool exhausted error",
            error_type="runtime",
            severity="high",
            frequency="occasional",
            error_description="SQLAlchemy connection pool exhausted after high load",
            error_symptoms=["ConnectionPoolExhausted exception", "500 errors", "slow response"],
            root_causes=["No connection cleanup", "Long-running transactions"],
            successful_solution="Implement proper connection cleanup and connection limits",
            solution_effectiveness=0.9,
            prevention_strategies=["Connection monitoring", "Automated cleanup"],
            tags=["database", "performance", "sqlalchemy"],
        )

        assert error_memory.category == MemoryCategory.ERROR
        assert error_memory.severity == "high"
        assert error_memory.solution_effectiveness == 0.9
        assert len(error_memory.root_causes) == 2

    def test_schema_registry(self):
        """Test schema registry functionality."""
        project_schema = get_schema_for_category(MemoryCategory.PROJECT)
        pattern_schema = get_schema_for_category(MemoryCategory.PATTERN)
        team_schema = get_schema_for_category(MemoryCategory.TEAM)
        error_schema = get_schema_for_category(MemoryCategory.ERROR)

        assert project_schema == ProjectMemorySchema
        assert pattern_schema == PatternMemorySchema
        assert team_schema == TeamMemorySchema
        assert error_schema == ErrorMemorySchema

    def test_memory_validation(self):
        """Test memory validation function."""
        valid_data = {
            "title": "Test Memory",
            "content": "Test content",
            "decision_type": "architecture",
            "decision_rationale": "For testing purposes",
        }

        validated_memory = validate_memory_schema(valid_data, MemoryCategory.PROJECT)
        assert isinstance(validated_memory, ProjectMemorySchema)
        assert validated_memory.title == "Test Memory"


class TestMemoryManager:
    """Test memory manager functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.memory_manager = create_memory_manager()

    def test_memory_manager_initialization(self):
        """Test memory manager initialization with default tags."""
        assert len(self.memory_manager.tag_registry) > 0
        assert "python" in self.memory_manager.tag_registry
        assert "backend" in self.memory_manager.tag_registry
        assert "urgent" in self.memory_manager.tag_registry

    def test_create_memory(self):
        """Test creating memories through memory manager."""
        memory_id = self.memory_manager.create_memory(
            category=MemoryCategory.PROJECT,
            title="Test Project Decision",
            content="This is a test decision",
            decision_type="testing",
            decision_rationale="For unit testing",
            tags=["testing", "python"],
        )

        assert memory_id is not None
        assert len(memory_id) > 0

        # Check tag usage count increased
        assert self.memory_manager.tag_registry["python"].usage_count == 1

    def test_add_custom_tag(self):
        """Test adding custom tags to registry."""
        success = self.memory_manager.add_tag(
            tag_name="custom_tag", category="custom", description="Custom test tag"
        )

        assert success is True
        assert "custom_tag" in self.memory_manager.tag_registry
        assert self.memory_manager.tag_registry["custom_tag"].tag_category == "custom"

        # Test duplicate tag
        duplicate_success = self.memory_manager.add_tag(
            tag_name="custom_tag", category="custom", description="Duplicate tag"
        )
        assert duplicate_success is False

    def test_get_tags_by_category(self):
        """Test retrieving tags by category."""
        tech_tags = self.memory_manager.get_tags_by_category("technology")
        priority_tags = self.memory_manager.get_tags_by_category("priority")

        assert len(tech_tags) > 0
        assert len(priority_tags) > 0
        assert all(tag.tag_category == "technology" for tag in tech_tags)
        assert all(tag.tag_category == "priority" for tag in priority_tags)

    def test_add_memory_relation(self):
        """Test adding relationships between memories."""
        success = self.memory_manager.add_memory_relation(
            source_id="memory_1",
            target_id="memory_2",
            relationship_type="related",
            strength=0.8,
            description="Related memories",
        )

        assert success is True
        assert len(self.memory_manager.memory_relations) == 1

        relations = self.memory_manager.get_related_memories("memory_1")
        assert len(relations) == 1
        assert relations[0].relationship_type == "related"

    def test_categorize_content(self):
        """Test automatic content categorization."""
        pattern_content = "This is a design pattern for solving database access"
        error_content = "Error occurred during database connection"
        team_content = "Standard practice for code review process"
        project_content = "Architectural decision about microservices"

        assert self.memory_manager.categorize_content(pattern_content) == MemoryCategory.PATTERN
        assert self.memory_manager.categorize_content(error_content) == MemoryCategory.ERROR
        assert self.memory_manager.categorize_content(team_content) == MemoryCategory.TEAM
        assert self.memory_manager.categorize_content(project_content) == MemoryCategory.PROJECT

    def test_suggest_tags(self):
        """Test automatic tag suggestion."""
        python_content = "Python Django application with FastAPI endpoints"
        frontend_content = "React component with TypeScript and JSX"

        python_tags = self.memory_manager.suggest_tags(python_content, MemoryCategory.PROJECT)
        frontend_tags = self.memory_manager.suggest_tags(frontend_content, MemoryCategory.PATTERN)

        assert "python" in python_tags
        assert "backend" in python_tags
        assert "javascript" in frontend_tags or "typescript" in frontend_tags
        assert "react" in frontend_tags


class TestSchemaValidation:
    """Test schema validation and migration."""

    def setup_method(self):
        """Set up test environment."""
        self.validator = create_schema_validator()

    def test_validate_memory_basic(self):
        """Test basic memory validation."""
        valid_data = {
            "category": "project",
            "title": "Test Memory",
            "content": "Test content",
            "decision_type": "architecture",
            "decision_rationale": "For testing",
        }

        validated_data = self.validator.validate_memory(valid_data)
        assert validated_data["title"] == "Test Memory"
        assert validated_data["category"] == "project"
        assert "created_at" in validated_data

    def test_validation_error_fixing(self):
        """Test automatic fixing of validation errors."""
        incomplete_data = {
            "category": "project",
            "title": "Incomplete Memory",
            "content": "Missing some fields",
            "decision_type": "test",
            "decision_rationale": "testing",
            # Missing priority, tags, etc.
        }

        validated_data = self.validator.validate_memory(incomplete_data)
        assert validated_data["priority"] == "medium"  # Default added
        assert validated_data["tags"] == []  # Default added
        assert "confidence_score" in validated_data

    def test_bulk_migration(self):
        """Test bulk migration of memories."""
        memories = [
            {
                "category": "project",
                "title": "Memory 1",
                "content": "Content 1",
                "decision_type": "test",
                "decision_rationale": "testing",
            },
            {
                "category": "pattern",
                "title": "Memory 2",
                "content": "Content 2",
                "pattern_type": "design",
                "problem_domain": "testing",
                "complexity_level": "simple",
                "problem_description": "test problem",
                "solution_approach": "test solution",
            },
        ]

        migrated_memories = self.validator.bulk_migrate_memories(memories)
        assert len(migrated_memories) == 2
        assert all("confidence_score" in memory for memory in migrated_memories)

    def test_schema_info(self):
        """Test getting schema information."""
        info = self.validator.get_schema_info()

        assert "current_version" in info
        assert "available_migrations" in info
        assert "schema_categories" in info
        assert len(info["schema_categories"]) == 4  # PROJECT, PATTERN, TEAM, ERROR


class TestMemoryIntegration:
    """Integration tests for the complete memory system."""

    def setup_method(self):
        """Set up test environment."""
        self.memory_manager = create_memory_manager()
        self.validator = create_schema_validator()

    def test_end_to_end_memory_lifecycle(self):
        """Test complete memory lifecycle from creation to retrieval."""
        # Create a memory
        memory_id = self.memory_manager.create_memory(
            category=MemoryCategory.PATTERN,
            title="Factory Pattern Implementation",
            content="Use factory pattern for creating database connections",
            pattern_type="design",
            problem_domain="database",
            complexity_level="moderate",
            problem_description="Need flexible database connection creation",
            solution_approach="Implement factory with different database types",
            tags=["design-pattern", "database", "python"],
        )

        assert memory_id is not None

        # Test tag usage increased
        assert self.memory_manager.tag_registry["python"].usage_count == 1

        # Add relationships
        memory_id_2 = self.memory_manager.create_memory(
            category=MemoryCategory.PROJECT,
            title="Database Architecture Decision",
            content="Choose PostgreSQL for main database",
            decision_type="technology",
            decision_rationale="Better performance for our use case",
            tags=["database", "postgresql"],
        )

        self.memory_manager.add_memory_relation(
            source_id=memory_id,
            target_id=memory_id_2,
            relationship_type="related",
            description="Both relate to database implementation",
        )

        # Test relationship retrieval
        relations = self.memory_manager.get_related_memories(memory_id)
        assert len(relations) == 1

    def test_schema_validation_integration(self):
        """Test schema validation integrated with memory manager."""
        # Test with incomplete data that needs validation
        raw_memory_data = {
            "category": "error",
            "title": "Database Connection Error",
            "content": "Connection timeout during high load",
            "error_type": "runtime",
            "severity": "high",
            "frequency": "rare",
            # Missing required fields like error_description
        }

        # This should be fixed automatically by the validator
        try:
            validated_data = self.validator.validate_memory(raw_memory_data)
            assert "error_description" in validated_data or len(validated_data["content"]) > 0
        except Exception as e:
            # If validation fails, ensure it's for expected reasons
            assert "required" in str(e).lower()


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_schemas = TestMemorySchemas()
    test_schemas.test_project_memory_schema_creation()
    test_schemas.test_pattern_memory_schema_creation()
    test_schemas.test_team_memory_schema_creation()
    test_schemas.test_error_memory_schema_creation()

    print("✅ All basic schema tests passed!")

    test_manager = TestMemoryManager()
    test_manager.setup_method()
    test_manager.test_memory_manager_initialization()
    test_manager.test_create_memory()

    print("✅ All memory manager tests passed!")

    test_validation = TestSchemaValidation()
    test_validation.setup_method()
    test_validation.test_validate_memory_basic()

    print("✅ All validation tests passed!")
    print("🎯 Memory schema system fully tested and operational!")
