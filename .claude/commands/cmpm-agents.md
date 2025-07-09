# CMPM Agents Registry

Active agent types and status listing for the Claude PM Framework with MCP infrastructure support.

## Instructions

Execute the CMPM agents monitoring system to provide a comprehensive overview of all available agents:

1. **Agent Registry Loading**
   - Load agent registry from `framework/agent-roles/agents.json`
   - Parse standard agents and user-defined agents
   - Validate agent configurations and metadata

2. **Agent Status Analysis**
   - Check availability status for each agent
   - Analyze agent specializations and capabilities
   - Verify coordination roles and tool access

3. **Agent Classification**
   - Standard agents (framework-provided)
   - User-defined agents (custom implementations)
   - MCP-enabled agents (multi-agent coordination)

4. **Agent Capabilities Assessment**
   - List agent specializations and domains
   - Show available tools and integrations
   - Display coordination roles and responsibilities

5. **Agent Distribution Summary**
   - Total agent count and availability statistics
   - Agent type distribution and categorization
   - Coordination role mapping and analysis

**Technical Implementation:**
- Use `python -m claude_pm.cmpm_commands cmpm:agents` to execute the agents dashboard
- Leverage existing `CMPMAgentMonitor` class for agent registry analysis
- Generate Rich-formatted table with agent details
- Include agent availability and capability information

**Expected Output:**
- Rich console table with agent listing
- Agent type, status, and specialization columns
- Tools and capabilities summary
- Agent distribution statistics
- MCP coordination framework integration status

Run the agents registry check now to see all available agents.