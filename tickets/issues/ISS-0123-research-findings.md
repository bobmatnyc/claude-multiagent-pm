# ISS-0123 Research Findings: Agent Selection Implementation Analysis

[Research Agent] Analysis Complete: Found root causes of 53% agent selection failure rate

## Executive Summary

After deep analysis of the agent selection implementation, I've identified the exact code locations and mechanisms causing the selection failures. The issue stems from a disconnect between the CLAUDE.md keyword mappings and the actual implementation in LOCAL mode.

## Key Findings

### 1. Agent Selection Flow in LOCAL Mode

**File**: `/claude_pm/orchestration/backwards_compatible_orchestrator.py`

The selection flow works as follows:
1. PM (or caller) passes an `agent_type` string to `delegate_to_agent()` (line 156)
2. LOCAL mode is now the default (lines 414-415)
3. In `_execute_local_orchestration()`, it tries to get agent prompt from registry (line 452)
4. If no prompt found, it falls back to hardcoded default prompts (lines 457-476)

**Critical Issue**: The `agent_type` parameter must exactly match the dictionary keys. There's NO keyword parsing or semantic understanding happening.

### 2. Hardcoded Agent Mappings (Line 457-476)

The LOCAL mode only recognizes these exact agent types:
- `security`
- `engineer` 
- `documentation`
- `qa`
- `research`
- `ops`
- `version_control`
- `ticketing`
- `data_engineer`

**Problem**: Any other agent type (like `pm`, `architect`, `ui_ux`) falls back to a generic prompt (line 478).

### 3. Missing Keyword-to-Agent Mapping

**Expected (from CLAUDE.md lines 247-273)**:
- "code" → Engineer Agent
- "implement" → Engineer Agent  
- "optimize" → Performance Agent
- "architect" → Architecture Agent
- "ticket" → Ticketing Agent

**Actual**: No keyword parsing exists. The caller must know the exact agent type string.

### 4. Registry Integration Issues

**File**: `/claude_pm/services/agent_registry.py`

The AgentRegistry properly implements:
- Two-tier hierarchy (user → system) (lines 166-182)
- Agent discovery across directories (lines 140-200)
- Proper precedence handling (line 179)

**But**: The LOCAL mode orchestrator doesn't use the registry for agent selection, only for loading prompts AFTER selection.

### 5. Model Selection Works Correctly

**File**: `/claude_pm/services/model_selector.py`

The model selector properly maps agents to models (lines 212-264):
- Orchestrator/Engineer → Opus 4
- Documentation/QA/Research → Sonnet 4

This part is working as designed.

## Root Causes

1. **No Keyword Parser**: There's no component that translates task descriptions or keywords into agent types
2. **Rigid Agent Type Matching**: Must use exact strings like "engineer", not "code" or "implement"
3. **Registry Not Used for Selection**: AgentRegistry is only used for loading prompts, not discovering available agents
4. **Hardcoded Fallbacks**: Only 9 agents have hardcoded prompts in LOCAL mode
5. **Missing Semantic Understanding**: No NLP or pattern matching for task-to-agent mapping

## Specific Code Locations Needing Fixes

1. **Add Keyword Parser**: Need new method in `backwards_compatible_orchestrator.py` before line 156
   ```python
   def _parse_agent_type_from_keywords(self, task_description: str) -> str:
       # Implement keyword matching from CLAUDE.md patterns
   ```

2. **Use Registry for Discovery**: Modify `_execute_local_orchestration()` around line 450 to:
   - List available agents from registry
   - Match task to best agent
   - Fall back intelligently

3. **Dynamic Prompt Loading**: Replace hardcoded prompts (lines 457-476) with registry-based loading

4. **Hierarchy Respect**: Ensure project → user → system precedence is honored in selection

## Impact Analysis

- 9/17 agents work = 53% failure rate confirmed
- Custom agents (PM, Architecture, etc.) completely inaccessible in LOCAL mode
- Users must know exact agent type strings, keywords don't work
- Project-specific agents ignored due to hardcoded defaults

## Recommended Fix Priority

1. **High**: Implement keyword parser for CLAUDE.md patterns
2. **High**: Use AgentRegistry for dynamic agent discovery
3. **Medium**: Remove hardcoded agent prompts
4. **Medium**: Add semantic task understanding
5. **Low**: Improve fallback behavior for unknown agents

---

This analysis provides the exact technical details needed to implement fixes for ISS-0123. The core issue is that LOCAL mode bypasses the sophisticated agent discovery system and relies on hardcoded mappings that don't match user expectations from CLAUDE.md.