#!/bin/bash

# Claude PM Framework Health Check Script
# Validates framework status and project health across all milestones

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_PROJECTS=0
HEALTHY_PROJECTS=0
WARNING_PROJECTS=0
CRITICAL_PROJECTS=0

echo -e "${BLUE}🔍 Claude PM Framework Health Check${NC}"
echo "=================================================="
echo "Timestamp: $(date)"
echo ""

# Check framework structure
echo -e "${BLUE}📁 Framework Structure Check${NC}"
echo "--------------------------------------------------"

REQUIRED_DIRS=(
    ".claude/commands"
    ".claude/templates" 
    ".claude/workflows"
    "scripts"
    "docs"
    "M01_Foundation"
    "M02_Automation"
    "M03_Orchestration"
    "trackdown"
    "trackdown/scripts"
    "trackdown/templates"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "/Users/masa/Projects/$dir" ]; then
        echo -e "✅ $dir"
    else
        echo -e "❌ $dir ${RED}MISSING${NC}"
    fi
done

echo ""

# Check MCP configuration
echo -e "${BLUE}🔌 MCP Integration Check${NC}"
echo "--------------------------------------------------"

if [ -f "/Users/masa/Projects/.mcp.json" ]; then
    echo -e "✅ .mcp.json configuration exists"
    
    # Validate JSON syntax
    if python3 -m json.tool "/Users/masa/Projects/.mcp.json" > /dev/null 2>&1; then
        echo -e "✅ .mcp.json syntax valid"
    else
        echo -e "❌ .mcp.json syntax invalid"
    fi
else
    echo -e "❌ .mcp.json ${RED}MISSING${NC}"
fi

echo ""

# Check TrackDown system
echo -e "${BLUE}📋 TrackDown System Check${NC}"
echo "--------------------------------------------------"

TRACKDOWN_FILES=(
    "trackdown/README.md"
    "trackdown/BACKLOG.md"
    "trackdown/MILESTONES.md"
)

for file in "${TRACKDOWN_FILES[@]}"; do
    if [ -f "/Users/masa/Projects/$file" ]; then
        echo -e "✅ $file"
    else
        echo -e "❌ $file ${RED}MISSING${NC}"
    fi
done

echo ""

# Function to check project health
check_project_health() {
    local project_path="$1"
    local project_name=$(basename "$project_path")
    local status="HEALTHY"
    local issues=()
    
    TOTAL_PROJECTS=$((TOTAL_PROJECTS + 1))
    
    # Skip if not a directory or if it's a special directory
    if [ ! -d "$project_path" ] || [[ "$project_name" == .* ]] || [[ "$project_name" == "node_modules" ]] || [[ "$project_name" == "trackdown" ]]; then
        return
    fi
    
    # Check for CLAUDE.md
    if [ ! -f "$project_path/CLAUDE.md" ]; then
        issues+=("No CLAUDE.md configuration")
        status="WARNING"
    fi
    
    # Check for recent git activity (if it's a git repo)
    if [ -d "$project_path/.git" ]; then
        # Check if there are commits in the last 30 days
        cd "$project_path"
        recent_commits=$(git log --since="30 days ago" --oneline 2>/dev/null | wc -l)
        if [ "$recent_commits" -eq 0 ]; then
            issues+=("No recent git activity (30 days)")
            if [ "$status" == "HEALTHY" ]; then
                status="WARNING"
            fi
        fi
        cd "/Users/masa/Projects"
    fi
    
    # Check for common dependency files
    dependency_files=("package.json" "requirements.txt" "pyproject.toml" "Cargo.toml")
    has_dependencies=false
    for dep_file in "${dependency_files[@]}"; do
        if [ -f "$project_path/$dep_file" ]; then
            has_dependencies=true
            break
        fi
    done
    
    # Check for README
    if [ ! -f "$project_path/README.md" ]; then
        issues+=("No README.md")
        if [ "$status" == "HEALTHY" ]; then
            status="WARNING"
        fi
    fi
    
    # Count and categorize
    case $status in
        "HEALTHY")
            HEALTHY_PROJECTS=$((HEALTHY_PROJECTS + 1))
            echo -e "  ✅ ${GREEN}$project_name${NC}"
            ;;
        "WARNING")
            WARNING_PROJECTS=$((WARNING_PROJECTS + 1))
            echo -e "  ⚠️  ${YELLOW}$project_name${NC} - ${issues[*]}"
            ;;
        "CRITICAL")
            CRITICAL_PROJECTS=$((CRITICAL_PROJECTS + 1))
            echo -e "  ❌ ${RED}$project_name${NC} - ${issues[*]}"
            ;;
    esac
}

# Check M01 Foundation projects
echo -e "${BLUE}🏗️  M01 Foundation Projects Health${NC}"
echo "--------------------------------------------------"

# Check managed projects first
echo -e "${BLUE}📁 Managed Projects${NC}"
if [ -d "/Users/masa/Projects/managed" ]; then
    for project_path in /Users/masa/Projects/managed/*/; do
        if [ -d "$project_path" ]; then
            check_project_health "$project_path"
        fi
    done
else
    echo -e "  ⚠️  ${YELLOW}No managed directory found${NC}"
fi

echo ""
echo -e "${BLUE}📦 Other M01 Foundation Projects${NC}"

M01_PROJECTS=(
    "ai-code-review"
    "mcp-desktop-gateway"
    "zen-mcp-server"
    "eva-agent"
    "eva-monorepo"
    "scraper-engine"
    "ai-power-rankings"
    "matsuoka-com"
    "hot-flash"
)

for project in "${M01_PROJECTS[@]}"; do
    if [ -d "/Users/masa/Projects/$project" ]; then
        check_project_health "/Users/masa/Projects/$project"
    else
        echo -e "  ❌ ${RED}$project${NC} - Project directory not found"
        CRITICAL_PROJECTS=$((CRITICAL_PROJECTS + 1))
        TOTAL_PROJECTS=$((TOTAL_PROJECTS + 1))
    fi
done

echo ""

# Check other active projects
echo -e "${BLUE}📦 Other Active Projects${NC}"
echo "--------------------------------------------------"

# Find all directories in Projects (excluding special ones)
for project_path in /Users/masa/Projects/*/; do
    project_name=$(basename "$project_path")
    
    # Skip special directories and M01 projects (already checked)
    if [[ "$project_name" == "_archive" ]] || [[ "$project_name" == "_temp" ]] || \
       [[ "$project_name" == "M01_Foundation" ]] || [[ "$project_name" == "M02_Automation" ]] || \
       [[ "$project_name" == "M03_Orchestration" ]] || [[ "$project_name" == "S01_M01_Core_Structure" ]] || \
       [[ "$project_name" == "trackdown" ]] || [[ "$project_name" == "scripts" ]] || \
       [[ "$project_name" == "docs" ]] || [[ "$project_name" == ".claude" ]] || \
       [[ "$project_name" == "data" ]] || [[ "$project_name" == "node_modules" ]] || \
       [[ "$project_name" == "Github" ]] || [[ "$project_name" == "Clients" ]]; then
        continue
    fi
    
    # Skip M01 projects (already checked above)
    skip_project=false
    for m01_project in "${M01_PROJECTS[@]}"; do
        if [[ "$project_name" == "$m01_project" ]]; then
            skip_project=true
            break
        fi
    done
    
    if [ "$skip_project" = false ]; then
        check_project_health "$project_path"
    fi
done

echo ""

# Summary
echo -e "${BLUE}📊 Health Summary${NC}"
echo "=================================================="
echo -e "Total Projects Checked: $TOTAL_PROJECTS"
echo -e "Healthy Projects: ${GREEN}$HEALTHY_PROJECTS${NC}"
echo -e "Warning Projects: ${YELLOW}$WARNING_PROJECTS${NC}"  
echo -e "Critical Projects: ${RED}$CRITICAL_PROJECTS${NC}"
echo ""

# Calculate health percentage
if [ $TOTAL_PROJECTS -gt 0 ]; then
    health_percentage=$(( (HEALTHY_PROJECTS * 100) / TOTAL_PROJECTS ))
    echo -e "Overall Framework Health: $health_percentage%"
    
    if [ $health_percentage -ge 80 ]; then
        echo -e "Status: ${GREEN}EXCELLENT${NC} 🎉"
    elif [ $health_percentage -ge 60 ]; then
        echo -e "Status: ${GREEN}GOOD${NC} ✅"
    elif [ $health_percentage -ge 40 ]; then
        echo -e "Status: ${YELLOW}NEEDS ATTENTION${NC} ⚠️"
    else
        echo -e "Status: ${RED}CRITICAL${NC} 🚨"
    fi
else
    echo -e "Status: ${RED}NO PROJECTS FOUND${NC}"
fi

echo ""

# Recommendations
echo -e "${BLUE}💡 Recommendations${NC}"
echo "=================================================="

if [ $WARNING_PROJECTS -gt 0 ] || [ $CRITICAL_PROJECTS -gt 0 ]; then
    echo "1. Add CLAUDE.md configuration files to projects missing them"
    echo "2. Update README.md files for better project documentation"
    echo "3. Review projects with no recent activity for archival"
    echo "4. Consider running git-portfolio-manager for automated tracking"
else
    echo "✅ Framework is in excellent health!"
    echo "💡 Consider implementing automated monitoring for continuous health tracking"
fi

echo ""
echo -e "${BLUE}🔗 Next Steps${NC}"
echo "=================================================="
echo "1. Review critical issues immediately"
echo "2. Plan resolution for warning items in next sprint"
echo "3. Update TrackDown BACKLOG.md with any new tasks identified"
echo "4. Run this health check weekly for continuous monitoring"

echo ""
echo "Health check completed at $(date)"