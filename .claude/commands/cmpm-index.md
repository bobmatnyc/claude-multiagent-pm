# CMPM Project Index

Comprehensive project discovery index with documentation agent delegation for the Claude PM Framework.

## Instructions

Execute the CMPM project indexing system to provide a comprehensive discovery and analysis of all projects:

1. **Project Discovery**
   - Scan current directory and subdirectories for projects
   - Identify project types (Node.js, Python, Git repositories)
   - Extract project metadata and descriptions

2. **Documentation Agent Delegation**
   - Delegate comprehensive project analysis to documentation agent
   - Calculate documentation scores (0-100%) for each project
   - Assess project health status (Excellent, Good, Fair, Poor)

3. **Project Complexity Analysis**
   - Calculate complexity scores based on file counts and structure
   - Analyze multi-language projects and dependencies
   - Evaluate project structure and organization

4. **Project Health Assessment**
   - Check for version control, dependency management
   - Verify testing infrastructure and CI/CD presence
   - Assess documentation quality and completeness

5. **Comprehensive Project Index**
   - Generate detailed project listing with metadata
   - Provide project type distribution and health statistics
   - Include documentation and complexity scoring

**Technical Implementation:**
- Use `python -m claude_pm.cmpm_commands cmpm:index` to execute the index dashboard
- Leverage existing `CMPMIndexOrchestrator` class for project discovery
- Generate Rich-formatted table with project details
- Include documentation agent delegation for enhanced analysis

**Expected Output:**
- Rich console table with project listing
- Project name, type, health status, and scores
- Documentation and complexity metrics
- Project statistics and distribution analysis
- Agent delegation confirmation and analysis summary

**Optional Parameters:**
- Add `--json` flag for JSON output format
- Add `--verbose` flag for detailed project descriptions

Run the project index now to discover and analyze all projects.