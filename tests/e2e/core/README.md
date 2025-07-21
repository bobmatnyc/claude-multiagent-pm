# E2E Core Orchestration Tests

This directory contains comprehensive end-to-end tests for the core orchestration functionality of the Claude PM framework, with a focus on LOCAL orchestration mode.

## Test Files

### test_local_orchestration.py

Comprehensive tests for LOCAL orchestration functionality including:

- **LOCAL Mode Detection and Execution**
  - `test_local_mode_detection`: Verifies LOCAL mode is properly detected
  - `test_local_execution_without_subprocess`: Tests local execution avoids subprocess overhead
  - `test_direct_agent_method_calls`: Tests direct agent method calls in LOCAL mode

- **PM Agent Orchestration**
  - `test_pm_agent_orchestration_local_mode`: Tests PM agent orchestration in LOCAL mode
  - `test_hierarchical_delegation_pattern`: Tests hierarchical agent delegation (PM → sub-agents)

- **State Management**
  - `test_state_management_in_local_execution`: Tests state management across executions
  - `test_local_mode_state_persistence`: Tests state persistence to disk
  - `test_local_mode_rollback_on_failure`: Tests rollback capabilities

- **Integration Features**
  - `test_todowrite_integration_local_mode`: Tests TodoWrite integration
  - `test_multi_agent_workflow_orchestration`: Tests complex multi-agent workflows
  - `test_context_filtering_and_propagation`: Tests context filtering strategies

- **Performance and Scalability**
  - `test_local_mode_performance`: Tests performance characteristics
  - `test_concurrent_local_orchestrations`: Tests concurrent execution handling
  - `test_local_mode_with_large_context`: Tests handling of large contexts
  - `test_memory_efficiency_in_local_mode`: Tests memory usage patterns

- **Advanced Patterns**
  - `test_error_propagation_in_local_mode`: Tests error handling
  - `test_mode_switching_local_to_subprocess`: Tests mode switching
  - `test_agent_hierarchy_in_local_mode`: Tests agent hierarchy resolution
  - `test_local_mode_with_complex_agent_registry`: Tests complex registry interactions
  - `test_local_mode_circuit_breaker_pattern`: Tests circuit breaker implementation

### test_orchestration_patterns.py

Tests for common orchestration patterns used by PM agents including:

- **Core Workflow Patterns**
  - `test_push_pattern_delegation_flow`: Documentation → QA → Version Control
  - `test_deploy_pattern_with_validation`: Ops → QA validation
  - `test_publish_pattern_with_security`: Security → Documentation → Ops

- **Context Management Patterns**
  - `test_context_filtering_by_agent_type`: Agent-specific context filtering
  - `test_result_aggregation_pattern`: Aggregating results from multiple agents

- **Advanced Patterns**
  - `test_error_handling_and_recovery_pattern`: Error recovery strategies
  - `test_performance_optimization_patterns`: Batch, pipeline, and parallel patterns
  - `test_conditional_workflow_pattern`: Conditional execution based on results
  - `test_hierarchical_delegation_pattern`: PM agent delegating to sub-agents

## Running the Tests

### Run all core orchestration tests:
```bash
pytest tests/e2e/core/ -v
```

### Run only LOCAL orchestration tests:
```bash
pytest tests/e2e/core/test_local_orchestration.py -v
```

### Run only orchestration pattern tests:
```bash
pytest tests/e2e/core/test_orchestration_patterns.py -v
```

### Run specific test:
```bash
pytest tests/e2e/core/test_local_orchestration.py::TestLocalOrchestration::test_local_mode_detection -v
```

### Run with coverage:
```bash
pytest tests/e2e/core/ --cov=claude_pm.orchestration --cov-report=html
```

## Test Design Principles

1. **Comprehensive Coverage**: Each test covers a specific aspect of LOCAL orchestration
2. **Performance Validation**: Tests include performance assertions (e.g., < 100ms execution)
3. **Real-World Scenarios**: Tests simulate actual PM agent workflows
4. **Error Resilience**: Tests verify proper error handling and recovery
5. **State Management**: Tests ensure state consistency across orchestrations

## Key Test Patterns

### LOCAL Mode Testing
```python
# Force LOCAL mode for testing
orchestrator.set_force_mode(OrchestrationMode.LOCAL)

# Set up message bus with mock handlers
message_bus = SimpleMessageBus()
message_bus.register_handler("agent_type", handler_function)
orchestrator._local_executor._message_bus = message_bus
```

### Mock Agent Creation
```python
async def mock_agent_handler(request_data):
    # Process request
    return {"result": "processed"}

message_bus.register_handler("agent_type", mock_agent_handler)
```

### Context Filtering
```python
mock_context_manager.filter_context_for_agent = MagicMock(
    side_effect=lambda agent, ctx: filtered_context
)
```

## Integration Points

These tests validate integration with:

- **BackwardsCompatibleOrchestrator**: Main orchestration class
- **SimpleMessageBus**: Message routing for LOCAL mode
- **ContextManager**: Context filtering and management
- **AgentRegistry**: Agent discovery and selection
- **TodoWrite**: Task tracking integration

## Future Enhancements

- Add tests for distributed orchestration patterns
- Test integration with external services (MCP, etc.)
- Add performance benchmarking suite
- Test orchestration with real agent implementations
- Add chaos engineering tests for resilience