# CMPM Health Dashboard

Comprehensive system health dashboard for the Claude PM Framework with ai-trackdown integration.

## Instructions

Execute the CMPM health monitoring system to provide a comprehensive dashboard of framework components:

1. **Framework Health Check**
   - Execute the health dashboard orchestrator
   - Check framework version and response time
   - Validate core services operational status

2. **AI-Trackdown Integration Status**
   - Test ai-trackdown-tools CLI functionality
   - Verify ticket system connectivity
   - Check epic and issue counts

3. **Memory System Health**
   - Test mem0AI integration connectivity
   - Validate memory service response times
   - Check memory system operational status

4. **Task Management System**
   - Verify task system operational status
   - Count active epics and issues
   - Test trackdown CLI responsiveness

5. **System Reliability Score**
   - Calculate overall system reliability (0-100%)
   - Provide color-coded status indicators
   - Generate comprehensive summary

**Technical Implementation:**
- Use `python -m claude_pm.cmpm_commands cmpm:health` to execute the health dashboard
- Leverage existing `CMPMHealthMonitor` class for comprehensive health checking
- Generate Rich-formatted dashboard with real-time metrics
- Include system reliability scoring and component status

**Expected Output:**
- Rich console dashboard with health status table
- System reliability score percentage
- Component-by-component health breakdown
- Performance metrics and response times
- Framework version and operational summary

Run the health check now to get current system status.