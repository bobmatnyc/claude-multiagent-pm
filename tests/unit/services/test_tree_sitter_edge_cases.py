#!/usr/bin/env python3
"""
Edge case and multi-language tests for TreeSitterAnalyzer.

This module tests TreeSitterAnalyzer's handling of:
- Various language files
- Edge cases and error conditions
- Unicode and encoding issues
- Special file formats
"""

import asyncio
import pytest
import tempfile
from pathlib import Path

from claude_pm.services.agent_modification_tracker.tree_sitter_analyzer import TreeSitterAnalyzer
from claude_pm.services.agent_modification_tracker.models import ModificationType


class TestTreeSitterEdgeCases:
    """Edge case tests for TreeSitterAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create TreeSitterAnalyzer instance."""
        return TreeSitterAnalyzer()
    
    # Unicode and Encoding Tests
    
    @pytest.mark.asyncio
    async def test_unicode_content(self, analyzer, tmp_path):
        """Test analysis of files with Unicode content."""
        unicode_file = tmp_path / "unicode.py"
        content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unicode test file 🎉"""

def greet_世界():
    """Say hello in multiple languages."""
    messages = [
        "Hello, World! 👋",
        "你好，世界！",
        "こんにちは、世界！",
        "Привет, мир!",
        "مرحبا بالعالم!",
        "🌍🌎🌏",
    ]
    return messages

class 多言語クラス:
    """Multi-language class name."""
    
    def __init__(self):
        self.emoji = "🚀"
        self.中文 = "Chinese"
        self.русский = "Russian"
    
    def get_emoji(self) -> str:
        return self.emoji

# Comments with emojis 🎨🎭🎪
variable_with_emoji = "test_🔥_hot"
'''
        unicode_file.write_text(content, encoding='utf-8')
        
        metadata = await analyzer.collect_file_metadata(
            str(unicode_file),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'python'
        assert 'greet_世界' in metadata.get('functions', [])
        assert '多言語クラス' in metadata.get('classes', [])
        assert not metadata.get('parse_errors', 0)  # Should parse without errors
    
    @pytest.mark.asyncio
    async def test_different_encodings(self, analyzer, tmp_path):
        """Test files with different encodings."""
        # Latin-1 encoded file
        latin1_file = tmp_path / "latin1.py"
        content = "# -*- coding: latin-1 -*-\n# Café résumé naïve\ndef función(): return 'señor'"
        latin1_file.write_text(content, encoding='latin-1')
        
        metadata = await analyzer.collect_file_metadata(
            str(latin1_file),
            ModificationType.CREATE
        )
        
        # Should handle encoding gracefully (tree-sitter works with bytes)
        assert 'language' in metadata
    
    # Complex Language Constructs
    
    @pytest.mark.asyncio
    async def test_python_advanced_features(self, analyzer, tmp_path):
        """Test analysis of advanced Python features."""
        advanced_file = tmp_path / "advanced.py"
        content = '''#!/usr/bin/env python3
"""Advanced Python features test."""

from __future__ import annotations
from typing import TypeVar, Generic, Protocol, Literal, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
from functools import wraps

# Type variables and generics
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Protocol
class Comparable(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...

# Generic class
class Container(Generic[T]):
    def __init__(self, items: list[T]):
        self._items = items
    
    def add(self, item: T) -> None:
        self._items.append(item)

# Dataclass with complex types
@dataclass
class ComplexData:
    name: str
    values: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: Literal["active", "inactive"] = "active"

# Abstract base class
class AbstractProcessor(ABC):
    @abstractmethod
    async def process(self, data: Any) -> Any:
        pass

# Decorator factory
def retry(times: int = 3):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    if i == times - 1:
                        raise
            return None
        return wrapper
    return decorator

# Context manager
class ResourceManager:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Complex async function with annotations
@retry(times=5)
async def complex_async_function(
    data: list[dict[str, Union[str, int]]],
    *,
    timeout: float = 30.0,
    callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> tuple[bool, dict[str, Any]]:
    """Complex async function with many features."""
    async with ResourceManager() as rm:
        results = await asyncio.gather(
            *[process_item(item) for item in data],
            return_exceptions=True
        )
    
    return True, {"results": results}

# Pattern matching (Python 3.10+)
def pattern_match_example(value):
    match value:
        case {"type": "user", "name": str(name)}:
            return f"User: {name}"
        case {"type": "admin", "id": int(id)}:
            return f"Admin #{id}"
        case _:
            return "Unknown"

# Walrus operator
if (n := len(data := [1, 2, 3])) > 2:
    print(f"Data has {n} items")
'''
        advanced_file.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(advanced_file),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'python'
        assert 'Container' in metadata.get('classes', [])
        assert 'ComplexData' in metadata.get('classes', [])
        assert 'complex_async_function' in metadata.get('async_functions', [])
        assert metadata.get('decorators', 0) > 0
    
    @pytest.mark.asyncio
    async def test_javascript_modern_features(self, analyzer, tmp_path):
        """Test analysis of modern JavaScript/ES6+ features."""
        modern_js = tmp_path / "modern.js"
        content = '''// Modern JavaScript features

// ES6 imports/exports
import React, { useState, useEffect } from 'react';
import * as utils from './utils';
import { API_KEY } from './config';
export { MyComponent as default };
export * from './components';

// Class with private fields and methods
class ModernClass {
    #privateField = 42;
    static staticField = 'static';
    
    constructor(name) {
        this.name = name;
    }
    
    #privateMethod() {
        return this.#privateField;
    }
    
    async asyncMethod() {
        return await fetch('/api/data');
    }
    
    *generatorMethod() {
        yield 1;
        yield 2;
        yield 3;
    }
}

// Arrow functions and destructuring
const processData = async ({ id, name, ...rest }) => {
    const result = await api.get(`/users/${id}`);
    return { ...result, processed: true };
};

// Template literals and tagged templates
const sql = (strings, ...values) => {
    return strings.reduce((result, str, i) => 
        result + str + (values[i] || ''), ''
    );
};

const query = sql`SELECT * FROM users WHERE id = ${userId}`;

// Optional chaining and nullish coalescing
const value = obj?.prop?.nested ?? 'default';

// Dynamic imports
const loadModule = async () => {
    const { default: Module } = await import('./module.js');
    return new Module();
};

// Decorators (experimental)
@injectable()
@logger
class ServiceClass {
    @readonly
    id = generateId();
    
    @debounce(300)
    handleInput(value) {
        console.log(value);
    }
}
'''
        modern_js.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(modern_js),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'javascript'
        assert 'ModernClass' in metadata.get('classes', [])
        assert 'ServiceClass' in metadata.get('classes', [])
        assert metadata.get('imports', 0) > 0
        assert metadata.get('exports', 0) > 0
    
    @pytest.mark.asyncio
    async def test_typescript_complex_types(self, analyzer, tmp_path):
        """Test analysis of complex TypeScript type systems."""
        complex_ts = tmp_path / "complex.ts"
        content = '''// Complex TypeScript types and features

// Advanced type imports
import type { ComponentType, FC } from 'react';
import { type User, type Admin } from './types';

// Conditional types
type IsArray<T> = T extends any[] ? true : false;
type ExtractArrayType<T> = T extends (infer U)[] ? U : never;

// Mapped types with template literal types
type Getters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
};

// Utility types and intersections
interface BaseEntity {
    id: string;
    createdAt: Date;
}

type ReadonlyDeep<T> = {
    readonly [P in keyof T]: T[P] extends object ? ReadonlyDeep<T[P]> : T[P];
};

// Generic constraints and defaults
interface Repository<T extends BaseEntity = BaseEntity> {
    find(id: string): Promise<T | null>;
    findAll(): Promise<T[]>;
    save(entity: Partial<T>): Promise<T>;
}

// Function overloads
function processValue(value: string): string;
function processValue(value: number): number;
function processValue(value: string[]): string[];
function processValue(value: string | number | string[]): string | number | string[] {
    if (Array.isArray(value)) {
        return value.map(v => v.toUpperCase());
    }
    return typeof value === 'string' ? value.toUpperCase() : value * 2;
}

// Abstract class with generics
abstract class AbstractService<T, U = void> {
    abstract process(input: T): Promise<U>;
    
    protected async validate(input: T): Promise<boolean> {
        return true;
    }
}

// Decorators with metadata
function Entity(tableName: string) {
    return function <T extends { new(...args: any[]): {} }>(constructor: T) {
        return class extends constructor {
            static tableName = tableName;
        };
    };
}

@Entity('users')
class UserModel implements BaseEntity {
    id!: string;
    createdAt!: Date;
    email!: string;
    
    constructor(data: Partial<UserModel>) {
        Object.assign(this, data);
    }
}

// Const assertions and literal types
const config = {
    api: {
        baseUrl: 'https://api.example.com',
        timeout: 5000,
    },
    features: ['auth', 'payments', 'notifications'] as const,
} as const;

type FeatureName = typeof config.features[number];

// Discriminated unions
type Result<T, E = Error> =
    | { success: true; data: T }
    | { success: false; error: E };

// Namespace and module augmentation
namespace API {
    export interface Options {
        timeout?: number;
        retry?: boolean;
    }
    
    export class Client {
        constructor(private options: Options) {}
    }
}

declare module './types' {
    interface User {
        lastLogin?: Date;
    }
}
'''
        complex_ts.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(complex_ts),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'typescript'
        assert 'AbstractService' in metadata.get('classes', [])
        assert 'UserModel' in metadata.get('classes', [])
        assert 'Repository' in metadata.get('interfaces', [])
        assert len(metadata.get('types', [])) > 5  # Many type definitions
    
    # Special File Formats
    
    @pytest.mark.asyncio
    async def test_dockerfile_analysis(self, analyzer, tmp_path):
        """Test analysis of Dockerfiles."""
        dockerfile = tmp_path / "Dockerfile"
        content = '''# Multi-stage Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
ENV NODE_ENV=production
CMD ["python", "main.py"]
'''
        dockerfile.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(dockerfile),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'dockerfile'
        assert metadata['file_type'] == 'dockerfile_file'
        assert metadata.get('lines_of_code', 0) > 10
    
    @pytest.mark.asyncio
    async def test_yaml_analysis(self, analyzer, tmp_path):
        """Test analysis of YAML files."""
        yaml_file = tmp_path / "config.yaml"
        content = '''# Complex YAML configuration
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - NODE_ENV=production
    ports:
      - "8080:80"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data:ro
      - logs:/var/log
    
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: ${DB_USER:-admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?password required}
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
  logs:

networks:
  default:
    driver: bridge
'''
        yaml_file.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(yaml_file),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'yaml'
        assert metadata['file_type'] == 'yaml_file'
    
    @pytest.mark.asyncio
    async def test_sql_analysis(self, analyzer, tmp_path):
        """Test analysis of SQL files."""
        sql_file = tmp_path / "schema.sql"
        content = '''-- Database schema
CREATE DATABASE IF NOT EXISTS myapp;
USE myapp;

-- Users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Complex stored procedure
DELIMITER //
CREATE PROCEDURE GetUserActivity(
    IN user_id BIGINT,
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    DECLARE total_actions INT;
    
    SELECT COUNT(*) INTO total_actions
    FROM user_actions
    WHERE user_id = user_id
        AND action_date BETWEEN start_date AND end_date;
    
    SELECT 
        DATE(action_date) as day,
        action_type,
        COUNT(*) as count
    FROM user_actions
    WHERE user_id = user_id
        AND action_date BETWEEN start_date AND end_date
    GROUP BY DATE(action_date), action_type
    ORDER BY day DESC;
END//
DELIMITER ;

-- Trigger
CREATE TRIGGER update_user_stats
AFTER INSERT ON user_actions
FOR EACH ROW
BEGIN
    UPDATE user_statistics
    SET total_actions = total_actions + 1,
        last_action_at = NEW.created_at
    WHERE user_id = NEW.user_id;
END;
'''
        sql_file.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(sql_file),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'sql'
        assert metadata['file_type'] == 'sql_file'
    
    # Error Handling and Recovery
    
    @pytest.mark.asyncio
    async def test_malformed_utf8(self, analyzer, tmp_path):
        """Test handling of malformed UTF-8 files."""
        bad_file = tmp_path / "bad_encoding.py"
        # Write binary data that's not valid UTF-8
        bad_file.write_bytes(b'# Python file\ndef test():\n    return "test\xff\xfe"')
        
        metadata = await analyzer.collect_file_metadata(
            str(bad_file),
            ModificationType.CREATE
        )
        
        # Should handle gracefully
        assert 'metadata_error' in metadata or 'analysis_error' in metadata
    
    @pytest.mark.asyncio
    async def test_huge_single_line(self, analyzer, tmp_path):
        """Test handling of files with extremely long lines."""
        huge_line_file = tmp_path / "huge_line.js"
        # Create a file with a very long single line
        content = "const data = [" + ",".join(str(i) for i in range(10000)) + "];"
        huge_line_file.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(huge_line_file),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'javascript'
        assert metadata.get('lines_of_code', 0) == 1
    
    @pytest.mark.asyncio
    async def test_mixed_content_file(self, analyzer, tmp_path):
        """Test analysis of files with mixed content (e.g., Jupyter notebooks structure)."""
        mixed_file = tmp_path / "mixed.md"
        content = '''# Code Documentation

Here's some Python code:

```python
def calculate(x, y):
    return x + y

class Calculator:
    def add(self, a, b):
        return a + b
```

And here's some JavaScript:

```javascript
function calculate(x, y) {
    return x + y;
}

class Calculator {
    add(a, b) {
        return a + b;
    }
}
```

Some SQL queries:

```sql
SELECT * FROM users WHERE active = 1;
CREATE INDEX idx_users_email ON users(email);
```

Regular text continues here...
'''
        mixed_file.write_text(content)
        
        metadata = await analyzer.collect_file_metadata(
            str(mixed_file),
            ModificationType.CREATE
        )
        
        assert metadata['language'] == 'markdown'
        assert metadata.get('code_blocks', 0) == 3
    
    @pytest.mark.asyncio
    async def test_symlink_handling(self, analyzer, tmp_path):
        """Test handling of symbolic links."""
        # Create a real file
        real_file = tmp_path / "real.py"
        real_file.write_text("def test(): return True")
        
        # Create a symlink
        symlink = tmp_path / "link.py"
        symlink.symlink_to(real_file)
        
        metadata = await analyzer.collect_file_metadata(
            str(symlink),
            ModificationType.CREATE
        )
        
        # Should analyze the target file
        assert metadata.get('functions', []) == ['test']
    
    @pytest.mark.asyncio
    async def test_permission_denied(self, analyzer, tmp_path):
        """Test handling of files with restricted permissions."""
        import os
        import platform
        
        if platform.system() != 'Windows':  # Skip on Windows
            restricted_file = tmp_path / "restricted.py"
            restricted_file.write_text("def test(): pass")
            
            # Remove read permissions
            os.chmod(restricted_file, 0o000)
            
            try:
                metadata = await analyzer.collect_file_metadata(
                    str(restricted_file),
                    ModificationType.CREATE
                )
                
                # Should handle permission error gracefully
                assert 'metadata_error' in metadata
            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_file, 0o644)