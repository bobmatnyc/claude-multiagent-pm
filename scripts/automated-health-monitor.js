#!/usr/bin/env node

/**
 * Claude PM Framework - Enhanced Automated Project Health Monitor (M01-006)
 * 
 * Comprehensive health monitoring system that tracks:
 * - Project structure compliance
 * - Git activity and repository health
 * - Framework adherence (CLAUDE.md files, TrackDown system)
 * - Service availability (mem0ai on port 8002, portfolio manager on port 3000, etc.)
 * - Performance metrics and response times
 * - TrackDown system status and ticket progress
 * - Managed projects health across ~/Projects/managed/
 * - Automated alerting for critical issues
 * - Background monitoring capabilities
 * 
 * Features:
 * - JSON and markdown health reports
 * - Continuous background monitoring
 * - Service status checks with response times
 * - Framework compliance validation
 * - Intelligent alerting and recommendations
 * - PM2/systemd compatible service mode
 */

const fs = require('fs');
const path = require('path');
const { execSync, exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

// Memory management and leak prevention
const MEMORY_THRESHOLD = 512 * 1024 * 1024; // 512MB threshold for health monitor
let memoryMonitorInterval = null;

function setupMemoryMonitoring() {
    memoryMonitorInterval = setInterval(() => {
        const usage = process.memoryUsage();
        if (usage.heapUsed > MEMORY_THRESHOLD) {
            console.log(`⚠️  High memory usage detected: ${Math.round(usage.heapUsed / 1024 / 1024)}MB`);
            if (global.gc) {
                global.gc();
                console.log(`🔄 Garbage collection triggered, new usage: ${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`);
            }
        }
    }, 30000); // Check every 30 seconds
}

function cleanupMemoryMonitoring() {
    if (memoryMonitorInterval) {
        clearInterval(memoryMonitorInterval);
        memoryMonitorInterval = null;
    }
    // Force garbage collection on cleanup
    if (global.gc) {
        global.gc();
    }
}

// Setup memory monitoring immediately
setupMemoryMonitoring();

// Cleanup on process exit
process.on('exit', cleanupMemoryMonitoring);
process.on('SIGINT', () => {
    cleanupMemoryMonitoring();
    process.exit(0);
});
process.on('SIGTERM', () => {
    cleanupMemoryMonitoring();
    process.exit(0);
});

class ClaudePMHealthMonitor {
  constructor(options = {}) {
    this.basePath = path.join(process.env.HOME, 'Projects');
    this.claudePMPath = path.join(this.basePath, 'Claude-PM');
    this.managedPath = path.join(this.basePath, 'managed');
    this.servicesPath = path.join(process.env.HOME, 'Services');
    
    // Configuration options
    this.config = {
      checkInterval: options.interval || 5 * 60 * 1000, // 5 minutes default
      alertThreshold: options.alertThreshold || 60, // Alert if health below 60%
      enableAlerting: options.enableAlerting !== false, // Default true
      enableServiceChecks: options.enableServiceChecks !== false, // Default true
      enableGitChecks: options.enableGitChecks !== false, // Default true
      verboseLogging: options.verbose || false,
      ...options
    };
    
    this.healthReport = {
      timestamp: new Date().toISOString(),
      version: '2.0.0',
      config: this.config,
      summary: {
        total_projects: 0,
        healthy_projects: 0,
        warning_projects: 0,
        critical_projects: 0,
        framework_compliance: 0,
        overall_health_percentage: 0
      },
      services: {},
      projects: {},
      framework: {},
      recommendations: [],
      alerts: []
    };
    
    this.logFile = path.join(this.claudePMPath, 'logs/health-monitor.log');
    this.statusFile = path.join(this.claudePMPath, 'logs/monitor-status.json');
    this.alertLog = path.join(this.claudePMPath, 'logs/health-alerts.log');
    
    // Ensure logs directory exists
    this.ensureLogsDirectory();
    
    // Initialize status tracking
    this.monitorStatus = {
      pid: process.pid,
      startTime: new Date().toISOString(),
      lastCheck: null,
      checksRun: 0,
      alertsSent: 0
    };
  }

  ensureLogsDirectory() {
    const logsDir = path.dirname(this.logFile);
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }
  }

  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data
    };
    
    const logLine = `[${timestamp}] ${level.toUpperCase()}: ${message}${data ? ' | ' + JSON.stringify(data) : ''}\n`;
    
    console.log(logLine.trim());
    
    try {
      fs.appendFileSync(this.logFile, logLine);
    } catch (err) {
      console.error('Failed to write to log file:', err.message);
    }
  }

  async checkServiceHealth() {
    this.log('info', 'Checking service health...');
    
    if (!this.config.enableServiceChecks) {
      this.log('info', 'Service checks disabled');
      return;
    }
    
    const services = {
      mem0ai_mcp: { 
        port: 8002, 
        path: '/health',
        description: 'mem0AI MCP Service',
        critical: true,
        processCheck: () => this.checkMem0AIService()
      },
      portfolio_manager: { 
        port: 3000, 
        path: '/',
        description: 'Claude PM Portfolio Manager',
        critical: false
      },
      git_portfolio_manager: { 
        port: 3001, 
        path: '/health',
        description: 'Git Portfolio Manager',
        critical: false
      },
      claude_pm_dashboard: {
        port: 5173,
        path: '/',
        description: 'Claude PM Dashboard (Vite)',
        critical: false
      }
    };

    for (const [serviceName, config] of Object.entries(services)) {
      try {
        const startTime = Date.now();
        const serviceCheck = {
          name: serviceName,
          description: config.description,
          port: config.port,
          critical: config.critical || false,
          last_check: new Date().toISOString()
        };

        // Check if port is listening
        const portCheck = await this.checkPort(config.port);
        
        if (portCheck.listening) {
          // Port is listening, check HTTP endpoint
          const response = await this.httpCheck(`http://localhost:${config.port}${config.path}`);
          const responseTime = Date.now() - startTime;
          
          serviceCheck.status = response.success ? 'healthy' : 'unhealthy';
          serviceCheck.response_time = responseTime;
          serviceCheck.http_status = response.statusCode;
          serviceCheck.error = response.error || null;
          
          // Add performance rating
          if (response.success) {
            if (responseTime < 100) serviceCheck.performance = 'excellent';
            else if (responseTime < 500) serviceCheck.performance = 'good';
            else if (responseTime < 2000) serviceCheck.performance = 'fair';
            else serviceCheck.performance = 'poor';
          }
        } else {
          serviceCheck.status = 'down';
          serviceCheck.error = 'Port not listening';
          
          // Check if process should be running
          if (config.processCheck) {
            const processInfo = await config.processCheck();
            serviceCheck.process_info = processInfo;
          }
        }
        
        this.healthReport.services[serviceName] = serviceCheck;
        
        // Generate alert for critical services that are down
        if (config.critical && serviceCheck.status !== 'healthy') {
          this.addAlert('critical', `Critical service ${serviceName} is ${serviceCheck.status}`, {
            service: serviceName,
            error: serviceCheck.error
          });
        }
        
        this.log('info', `Service ${serviceName}`, {
          status: serviceCheck.status,
          response_time: serviceCheck.response_time,
          performance: serviceCheck.performance
        });
        
      } catch (err) {
        this.healthReport.services[serviceName] = {
          name: serviceName,
          status: 'error',
          error: err.message,
          last_check: new Date().toISOString(),
          critical: config.critical || false
        };
        
        if (config.critical) {
          this.addAlert('critical', `Critical service check failed for ${serviceName}: ${err.message}`);
        }
        
        this.log('error', `Service ${serviceName} check failed`, { error: err.message });
      }
    }
  }

  async checkPort(port) {
    return new Promise((resolve) => {
      const net = require('net');
      const socket = new net.Socket();
      
      socket.setTimeout(1000);
      
      socket.on('connect', () => {
        socket.destroy();
        resolve({ listening: true });
      });
      
      socket.on('timeout', () => {
        socket.destroy();
        resolve({ listening: false, error: 'Connection timeout' });
      });
      
      socket.on('error', (err) => {
        resolve({ listening: false, error: err.message });
      });
      
      socket.connect(port, 'localhost');
    });
  }

  async checkMem0AIService() {
    try {
      const servicePath = path.join(this.servicesPath, 'mem0ai-mcp');
      if (fs.existsSync(servicePath)) {
        const makefilePath = path.join(servicePath, 'Makefile');
        if (fs.existsSync(makefilePath)) {
          const originalCwd = process.cwd();
          process.chdir(servicePath);
          try {
            const status = execSync('make status 2>/dev/null || echo "Status check failed"', { encoding: 'utf8' });
            process.chdir(originalCwd);
            return {
              service_directory: servicePath,
              status_output: status.trim(),
              makefile_exists: true
            };
          } catch (err) {
            process.chdir(originalCwd);
            return {
              service_directory: servicePath,
              error: err.message,
              makefile_exists: true
            };
          }
        }
        return {
          service_directory: servicePath,
          makefile_exists: false
        };
      }
      return {
        service_directory: servicePath,
        directory_exists: false
      };
    } catch (err) {
      return {
        error: err.message
      };
    }
  }

  addAlert(level, message, data = null) {
    const alert = {
      timestamp: new Date().toISOString(),
      level: level,
      message: message,
      data: data
    };
    
    this.healthReport.alerts.push(alert);
    
    // Log alert
    const alertLine = `[${alert.timestamp}] ${level.toUpperCase()}: ${message}${data ? ' | ' + JSON.stringify(data) : ''}\n`;
    
    try {
      fs.appendFileSync(this.alertLog, alertLine);
      this.monitorStatus.alertsSent++;
    } catch (err) {
      this.log('error', 'Failed to write alert to log file', { error: err.message });
    }
    
    if (this.config.enableAlerting) {
      console.log(`🚨 ALERT: ${alertLine.trim()}`);
    }
  }

  async httpCheck(url, timeout = 5000) {
    return new Promise((resolve) => {
      const http = require('http');
      const urlObj = new URL(url);
      
      const req = http.get({
        hostname: urlObj.hostname,
        port: urlObj.port,
        path: urlObj.pathname,
        timeout: timeout
      }, (res) => {
        resolve({
          success: res.statusCode >= 200 && res.statusCode < 400,
          statusCode: res.statusCode,
          error: null
        });
      });

      req.on('error', (err) => {
        resolve({
          success: false,
          error: err.message
        });
      });

      req.on('timeout', () => {
        req.destroy();
        resolve({
          success: false,
          error: 'Request timeout'
        });
      });
    });
  }

  async checkFrameworkCompliance() {
    this.log('info', 'Checking framework compliance...');
    
    const requiredFiles = [
      'trackdown/BACKLOG.md',
      'trackdown/MILESTONES.md', 
      'CLAUDE.md',
      'README.md',
      'package.json'
    ];

    const requiredDirectories = [
      'trackdown',
      'docs',
      'scripts',
      'logs'
    ];

    const optionalFiles = [
      'trackdown/README.md',
      'trackdown/METRICS.md',
      'trackdown/RETROSPECTIVES.md',
      'docs/TOOLCHAIN.md',
      'docs/INSTRUCTIONS.md'
    ];

    let compliance = 0;
    let total = requiredFiles.length + requiredDirectories.length;
    let optionalCompliance = 0;

    // Check required files
    const fileChecks = {};
    for (const file of requiredFiles) {
      const filePath = path.join(this.claudePMPath, file);
      const exists = fs.existsSync(filePath);
      fileChecks[file] = {
        exists: exists,
        path: filePath,
        required: true
      };
      
      if (exists) {
        compliance++;
        this.log('debug', `Found required file: ${file}`);
        
        // Additional content checks for critical files
        if (file === 'trackdown/BACKLOG.md') {
          const stats = fs.statSync(filePath);
          fileChecks[file].size = stats.size;
          fileChecks[file].lastModified = stats.mtime;
          fileChecks[file].contentHealth = await this.checkBacklogHealth(filePath);
        }
      } else {
        this.log('warning', `Missing required file: ${file}`);
        this.healthReport.recommendations.push(`Create missing file: ${file}`);
      }
    }

    // Check required directories
    const directoryChecks = {};
    for (const dir of requiredDirectories) {
      const dirPath = path.join(this.claudePMPath, dir);
      const exists = fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory();
      directoryChecks[dir] = {
        exists: exists,
        path: dirPath,
        required: true
      };
      
      if (exists) {
        compliance++;
        this.log('debug', `Found required directory: ${dir}`);
        
        // Check directory contents
        const files = fs.readdirSync(dirPath);
        directoryChecks[dir].fileCount = files.length;
        directoryChecks[dir].files = files;
      } else {
        this.log('warning', `Missing required directory: ${dir}`);
        this.healthReport.recommendations.push(`Create missing directory: ${dir}`);
      }
    }

    // Check optional files for bonus compliance
    for (const file of optionalFiles) {
      const filePath = path.join(this.claudePMPath, file);
      if (fs.existsSync(filePath)) {
        optionalCompliance++;
      }
    }

    this.healthReport.framework = {
      compliance_percentage: Math.round((compliance / total) * 100),
      total_checks: total,
      passed_checks: compliance,
      optional_compliance: optionalCompliance,
      optional_total: optionalFiles.length,
      file_checks: fileChecks,
      directory_checks: directoryChecks,
      last_check: new Date().toISOString()
    };
    
    // Check managed projects compliance
    await this.checkManagedProjectsCompliance();
    
    // Check TrackDown system health
    await this.checkTrackDownHealth();
    
    // Generate framework-specific alerts
    const compliancePercentage = this.healthReport.framework.compliance_percentage;
    if (compliancePercentage < 80) {
      this.addAlert('warning', `Framework compliance is ${compliancePercentage}% (below 80% threshold)`);
    }
  }

  async checkBacklogHealth(backlogPath) {
    try {
      const content = fs.readFileSync(backlogPath, 'utf8');
      
      const totalTickets = (content.match(/^\- \[/gm) || []).length;
      const completedTickets = (content.match(/^\- \[x\]/gm) || []).length;
      const inProgressTickets = (content.match(/^\- \[>]/gm) || []).length;
      const pendingTickets = (content.match(/^\- \[ ]/gm) || []).length;
      
      // Count priority tickets
      const highPriorityTickets = (content.match(/HIGH/g) || []).length;
      const criticalTickets = (content.match(/CRITICAL/g) || []).length;
      
      // Check for recent updates
      const lines = content.split('\n');
      const recentlyUpdated = lines.filter(line => {
        const dateMatch = line.match(/\d{4}-\d{2}-\d{2}/);
        if (dateMatch) {
          const lineDate = new Date(dateMatch[0]);
          const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
          return lineDate > weekAgo;
        }
        return false;
      }).length;

      return {
        total_tickets: totalTickets,
        completed_tickets: completedTickets,
        in_progress_tickets: inProgressTickets,
        pending_tickets: pendingTickets,
        high_priority_tickets: highPriorityTickets,
        critical_tickets: criticalTickets,
        recently_updated_lines: recentlyUpdated,
        completion_rate: totalTickets > 0 ? Math.round((completedTickets / totalTickets) * 100) : 0,
        health_status: this.calculateBacklogHealthStatus(totalTickets, completedTickets, recentlyUpdated)
      };
    } catch (err) {
      this.log('error', 'Failed to analyze backlog health', { error: err.message });
      return { error: err.message };
    }
  }

  calculateBacklogHealthStatus(total, completed, recentUpdates) {
    if (total === 0) return 'empty';
    
    const completionRate = (completed / total) * 100;
    const hasRecentActivity = recentUpdates > 0;
    
    if (completionRate >= 80 && hasRecentActivity) return 'excellent';
    if (completionRate >= 60 && hasRecentActivity) return 'good';
    if (completionRate >= 40 || hasRecentActivity) return 'fair';
    return 'poor';
  }

  async checkManagedProjectsCompliance() {
    this.log('info', 'Checking managed projects framework compliance...');
    
    if (!fs.existsSync(this.managedPath)) {
      this.log('warning', 'Managed projects directory not found');
      return;
    }

    const managedProjects = fs.readdirSync(this.managedPath)
      .filter(name => {
        const projectPath = path.join(this.managedPath, name);
        return fs.statSync(projectPath).isDirectory() && !name.startsWith('.');
      });

    let compliantProjects = 0;
    const projectCompliance = {};

    for (const projectName of managedProjects) {
      const projectPath = path.join(this.managedPath, projectName);
      const compliance = await this.checkSingleProjectCompliance(projectPath);
      
      projectCompliance[projectName] = compliance;
      
      if (compliance.score >= 80) {
        compliantProjects++;
      }
    }

    this.healthReport.framework.managed_projects = {
      total_projects: managedProjects.length,
      compliant_projects: compliantProjects,
      compliance_rate: managedProjects.length > 0 ? Math.round((compliantProjects / managedProjects.length) * 100) : 0,
      project_details: projectCompliance
    };
  }

  async checkSingleProjectCompliance(projectPath) {
    const projectName = path.basename(projectPath);
    const requiredFiles = ['CLAUDE.md', 'README.md'];
    const recommendedFiles = ['trackdown/BACKLOG.md', 'docs/INSTRUCTIONS.md', 'package.json'];
    
    let score = 0;
    let maxScore = 0;
    const checks = {};

    // Check required files (70% of score)
    for (const file of requiredFiles) {
      const filePath = path.join(projectPath, file);
      const exists = fs.existsSync(filePath);
      checks[file] = { exists, required: true, weight: 35 };
      maxScore += 35;
      if (exists) score += 35;
    }

    // Check recommended files (30% of score)  
    for (const file of recommendedFiles) {
      const filePath = path.join(projectPath, file);
      const exists = fs.existsSync(filePath);
      checks[file] = { exists, required: false, weight: 10 };
      maxScore += 10;
      if (exists) score += 10;
    }

    const finalScore = Math.round((score / maxScore) * 100);

    return {
      project_name: projectName,
      score: finalScore,
      max_score: maxScore,
      checks: checks,
      status: finalScore >= 80 ? 'compliant' : finalScore >= 60 ? 'partial' : 'non-compliant'
    };
  }

  async checkTrackDownHealth() {
    try {
      const backlogPath = path.join(this.claudePMPath, 'trackdown/BACKLOG.md');
      if (fs.existsSync(backlogPath)) {
        const backlogContent = fs.readFileSync(backlogPath, 'utf8');
        
        // Count tickets by status
        const totalTickets = (backlogContent.match(/^\- \[/gm) || []).length;
        const completedTickets = (backlogContent.match(/^\- \[x\]/gm) || []).length;
        const pendingTickets = (backlogContent.match(/^\- \[ \]/gm) || []).length;
        
        // Check last modification
        const stats = fs.statSync(backlogPath);
        const lastModified = stats.mtime;
        const daysSinceUpdate = Math.floor((Date.now() - lastModified.getTime()) / (1000 * 60 * 60 * 24));
        
        this.healthReport.framework.trackdown = {
          total_tickets: totalTickets,
          completed_tickets: completedTickets,
          pending_tickets: pendingTickets,
          completion_rate: totalTickets > 0 ? Math.round((completedTickets / totalTickets) * 100) : 0,
          last_update_days: daysSinceUpdate,
          health_status: daysSinceUpdate <= 7 ? 'active' : daysSinceUpdate <= 30 ? 'moderate' : 'stale'
        };

        if (daysSinceUpdate > 7) {
          this.healthReport.recommendations.push(`TrackDown system hasn't been updated in ${daysSinceUpdate} days - consider reviewing progress`);
        }
      }
    } catch (err) {
      this.log('error', 'Failed to check TrackDown health', { error: err.message });
    }
  }

  async checkProjectHealth(projectPath) {
    const projectName = path.basename(projectPath);
    const health = {
      name: projectName,
      path: projectPath,
      status: 'healthy',
      issues: [],
      metrics: {},
      last_check: new Date().toISOString()
    };

    try {
      // Check for required files
      const requiredFiles = ['CLAUDE.md', 'README.md'];
      for (const file of requiredFiles) {
        if (!fs.existsSync(path.join(projectPath, file))) {
          health.issues.push(`Missing ${file}`);
          health.status = 'warning';
        }
      }

      // Check git health
      if (fs.existsSync(path.join(projectPath, '.git'))) {
        try {
          const gitHealth = await this.checkGitHealth(projectPath);
          health.metrics.git = gitHealth;
          
          if (gitHealth.days_since_last_commit > 30) {
            health.issues.push(`No commits in ${gitHealth.days_since_last_commit} days`);
            if (health.status === 'healthy') health.status = 'warning';
          }
        } catch (err) {
          health.issues.push(`Git check failed: ${err.message}`);
          health.status = 'error';
        }
      }

      // Check dependency health
      const depHealth = await this.checkDependencyHealth(projectPath);
      if (depHealth) {
        health.metrics.dependencies = depHealth;
        if (depHealth.outdated_count > 5) {
          health.issues.push(`${depHealth.outdated_count} outdated dependencies`);
          if (health.status === 'healthy') health.status = 'warning';
        }
      }

      // Check for build/test configuration
      const buildConfigs = ['package.json', 'pyproject.toml', 'Cargo.toml', 'Makefile'];
      const hasBuildConfig = buildConfigs.some(config => fs.existsSync(path.join(projectPath, config)));
      
      if (!hasBuildConfig) {
        health.issues.push('No build configuration found');
        if (health.status === 'healthy') health.status = 'warning';
      }

      // Update summary counters
      this.healthReport.summary.total_projects++;
      if (health.status === 'healthy') {
        this.healthReport.summary.healthy_projects++;
      } else if (health.status === 'warning') {
        this.healthReport.summary.warning_projects++;
      } else {
        this.healthReport.summary.critical_projects++;
      }

    } catch (err) {
      health.status = 'error';
      health.issues.push(`Health check failed: ${err.message}`);
      this.healthReport.summary.critical_projects++;
      this.log('error', `Project health check failed for ${projectName}`, { error: err.message });
    }

    return health;
  }

  async checkGitHealth(projectPath) {
    const originalCwd = process.cwd();
    process.chdir(projectPath);

    try {
      // Get last commit info
      const lastCommitCmd = 'git log -1 --format="%H|%cd|%s" --date=iso';
      const lastCommitOutput = execSync(lastCommitCmd, { encoding: 'utf8' }).trim();
      const [hash, date, message] = lastCommitOutput.split('|');
      
      const lastCommitDate = new Date(date);
      const daysSinceLastCommit = Math.floor((Date.now() - lastCommitDate.getTime()) / (1000 * 60 * 60 * 24));

      // Get branch info
      const currentBranch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
      const branchCount = execSync('git branch -r', { encoding: 'utf8' }).split('\n').filter(b => b.trim()).length;

      // Get commit count in last 30 days
      const recentCommitsCmd = 'git log --since="30 days ago" --oneline';
      const recentCommits = execSync(recentCommitsCmd, { encoding: 'utf8' }).split('\n').filter(l => l.trim()).length;

      // Check for uncommitted changes
      const gitStatusOutput = execSync('git status --porcelain', { encoding: 'utf8' });
      const hasUncommittedChanges = gitStatusOutput.trim().length > 0;

      return {
        last_commit_hash: hash,
        last_commit_date: date,
        last_commit_message: message,
        days_since_last_commit: daysSinceLastCommit,
        current_branch: currentBranch,
        branch_count: branchCount,
        recent_commits_30d: recentCommits,
        has_uncommitted_changes: hasUncommittedChanges,
        health_status: daysSinceLastCommit <= 7 ? 'active' : daysSinceLastCommit <= 30 ? 'moderate' : 'stale'
      };
    } finally {
      process.chdir(originalCwd);
    }
  }

  async checkDependencyHealth(projectPath) {
    // Check Node.js projects
    const packageJsonPath = path.join(projectPath, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      return this.checkNodeDependencies(projectPath);
    }

    // Check Python projects
    const pyprojectPath = path.join(projectPath, 'pyproject.toml');
    const requirementsPath = path.join(projectPath, 'requirements.txt');
    if (fs.existsSync(pyprojectPath) || fs.existsSync(requirementsPath)) {
      return this.checkPythonDependencies(projectPath);
    }

    return null;
  }

  async checkNodeDependencies(projectPath) {
    try {
      const originalCwd = process.cwd();
      process.chdir(projectPath);

      const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
      const totalDeps = Object.keys(packageJson.dependencies || {}).length + 
                       Object.keys(packageJson.devDependencies || {}).length;

      let outdatedCount = 0;
      try {
        const outdatedOutput = execSync('npm outdated --json', { encoding: 'utf8' });
        const outdatedPackages = JSON.parse(outdatedOutput);
        outdatedCount = Object.keys(outdatedPackages).length;
      } catch (err) {
        // npm outdated returns exit code 1 when packages are outdated
        if (err.stdout) {
          try {
            const outdatedPackages = JSON.parse(err.stdout);
            outdatedCount = Object.keys(outdatedPackages).length;
          } catch (parseErr) {
            // If we can't parse, assume no outdated packages
            outdatedCount = 0;
          }
        }
      }

      process.chdir(originalCwd);

      return {
        type: 'node',
        total_dependencies: totalDeps,
        outdated_count: outdatedCount,
        health_status: outdatedCount === 0 ? 'healthy' : outdatedCount <= 5 ? 'moderate' : 'critical'
      };
    } catch (err) {
      this.log('warning', 'Failed to check Node.js dependencies', { error: err.message });
      return null;
    }
  }

  async checkPythonDependencies(projectPath) {
    try {
      const originalCwd = process.cwd();
      process.chdir(projectPath);

      let totalDeps = 0;
      
      // Try to count dependencies from pyproject.toml or requirements.txt
      if (fs.existsSync('requirements.txt')) {
        const requirements = fs.readFileSync('requirements.txt', 'utf8');
        totalDeps = requirements.split('\n').filter(line => line.trim() && !line.startsWith('#')).length;
      } else if (fs.existsSync('pyproject.toml')) {
        // Basic parsing - could be enhanced with a proper TOML parser
        const pyproject = fs.readFileSync('pyproject.toml', 'utf8');
        const depMatches = pyproject.match(/dependencies\s*=\s*\[([\s\S]*?)\]/);
        if (depMatches) {
          totalDeps = depMatches[1].split(',').filter(dep => dep.trim()).length;
        }
      }

      process.chdir(originalCwd);

      return {
        type: 'python',
        total_dependencies: totalDeps,
        outdated_count: 0, // Would need pip-outdated or similar tool
        health_status: 'unknown'
      };
    } catch (err) {
      this.log('warning', 'Failed to check Python dependencies', { error: err.message });
      return null;
    }
  }

  async scanAllProjects() {
    this.log('info', 'Scanning all projects...');
    
    // Scan managed projects
    if (fs.existsSync(this.managedPath)) {
      const managedProjects = fs.readdirSync(this.managedPath)
        .filter(name => {
          const projectPath = path.join(this.managedPath, name);
          return fs.statSync(projectPath).isDirectory() && !name.startsWith('.');
        });

      for (const projectName of managedProjects) {
        const projectPath = path.join(this.managedPath, projectName);
        const health = await this.checkProjectHealth(projectPath);
        this.healthReport.projects[`managed/${projectName}`] = health;
      }
    }

    // Scan other projects in base directory
    const allProjects = fs.readdirSync(this.basePath)
      .filter(name => {
        const projectPath = path.join(this.basePath, name);
        return fs.statSync(projectPath).isDirectory() && 
               !name.startsWith('.') && 
               !['managed', 'Claude-PM', 'node_modules'].includes(name);
      });

    for (const projectName of allProjects) {
      const projectPath = path.join(this.basePath, projectName);
      const health = await this.checkProjectHealth(projectPath);
      this.healthReport.projects[projectName] = health;
    }
  }

  generateRecommendations() {
    const { summary } = this.healthReport;
    
    // Calculate framework compliance
    summary.framework_compliance = this.healthReport.framework.compliance_percentage || 0;

    // Generate recommendations based on findings
    if (summary.critical_projects > 0) {
      this.healthReport.recommendations.push(`Address ${summary.critical_projects} critical project issues immediately`);
    }
    
    if (summary.warning_projects > summary.healthy_projects) {
      this.healthReport.recommendations.push('More than half of projects have warnings - consider a framework compliance review');
    }
    
    if (summary.framework_compliance < 80) {
      this.healthReport.recommendations.push('Framework compliance below 80% - review and update framework structure');
    }

    // Service-specific recommendations
    const downServices = Object.entries(this.healthReport.services)
      .filter(([_, service]) => service.status !== 'healthy')
      .map(([name, _]) => name);
    
    if (downServices.length > 0) {
      this.healthReport.recommendations.push(`Restart or fix services: ${downServices.join(', ')}`);
    }
  }

  saveHealthReport() {
    const reportPath = path.join(this.claudePMPath, 'logs/health-report.json');
    const summaryPath = path.join(this.claudePMPath, 'logs/health-summary.md');
    
    try {
      // Save detailed JSON report
      fs.writeFileSync(reportPath, JSON.stringify(this.healthReport, null, 2));
      
      // Generate markdown summary
      const summary = this.generateMarkdownSummary();
      fs.writeFileSync(summaryPath, summary);
      
      this.log('info', 'Health report saved', { 
        json_report: reportPath, 
        markdown_summary: summaryPath 
      });
    } catch (err) {
      this.log('error', 'Failed to save health report', { error: err.message });
    }
  }

  generateMarkdownSummary() {
    const { summary, framework } = this.healthReport;
    const timestamp = new Date(this.healthReport.timestamp).toLocaleString();
    
    return `# Claude PM Framework Health Report

**Generated**: ${timestamp}

## Summary

- **Total Projects**: ${summary.total_projects}
- **Healthy**: ${summary.healthy_projects} (${Math.round((summary.healthy_projects / summary.total_projects) * 100)}%)
- **Warning**: ${summary.warning_projects} (${Math.round((summary.warning_projects / summary.total_projects) * 100)}%)
- **Critical**: ${summary.critical_projects} (${Math.round((summary.critical_projects / summary.total_projects) * 100)}%)
- **Framework Compliance**: ${summary.framework_compliance}%

## Framework Status

${framework.trackdown ? `
### TrackDown System
- **Total Tickets**: ${framework.trackdown.total_tickets}
- **Completed**: ${framework.trackdown.completed_tickets} (${framework.trackdown.completion_rate}%)
- **Pending**: ${framework.trackdown.pending_tickets}
- **Last Update**: ${framework.trackdown.last_update_days} days ago
- **Status**: ${framework.trackdown.health_status}
` : ''}

## Services Status

${Object.entries(this.healthReport.services).map(([name, service]) => 
  `- **${name}**: ${service.status} ${service.response_time ? `(${service.response_time}ms)` : ''}`
).join('\n')}

## Recommendations

${this.healthReport.recommendations.map(rec => `- ${rec}`).join('\n')}

## Critical Issues

${Object.entries(this.healthReport.projects)
  .filter(([_, project]) => project.status === 'error' || project.status === 'critical')
  .map(([name, project]) => `- **${name}**: ${project.issues.join(', ')}`)
  .join('\n') || 'None'}

---
*Report generated by Claude PM Automated Health Monitor*
`;
  }

  async runHealthCheck() {
    this.log('info', 'Starting comprehensive health check...');
    
    try {
      // Clear previous health report to prevent memory accumulation
      if (this.healthReport) {
        // Clear large objects
        this.healthReport.services = null;
        this.healthReport.projects = null;
        this.healthReport.framework = null;
        this.healthReport.recommendations = null;
        this.healthReport.alerts = null;
        this.healthReport = null;
      }
      
      // Force garbage collection before creating new report
      if (global.gc) {
        global.gc();
      }
      
      // Reset health report
      this.healthReport = {
        timestamp: new Date().toISOString(),
        version: '2.0.0',
        config: this.config,
        summary: {
          total_projects: 0,
          healthy_projects: 0,
          warning_projects: 0,
          critical_projects: 0,
          framework_compliance: 0,
          overall_health_percentage: 0
        },
        services: {},
        projects: {},
        framework: {},
        recommendations: [],
        alerts: []
      };

      // Update monitor status
      this.monitorStatus.lastCheck = new Date().toISOString();
      this.monitorStatus.checksRun++;

      // Run all health checks in parallel where possible
      const startTime = Date.now();
      
      await Promise.all([
        this.checkServiceHealth(),
        this.checkFrameworkCompliance()
      ]);
      
      await this.scanAllProjects();
      
      // Calculate overall health
      this.calculateOverallHealth();
      
      // Generate recommendations
      this.generateRecommendations();
      
      // Check for critical alerts
      this.checkCriticalThresholds();
      
      // Save reports and status
      this.saveHealthReport();
      this.saveMonitorStatus();
      
      const duration = Date.now() - startTime;
      
      this.log('info', 'Health check completed', {
        duration_ms: duration,
        total_projects: this.healthReport.summary.total_projects,
        healthy: this.healthReport.summary.healthy_projects,
        warnings: this.healthReport.summary.warning_projects,
        critical: this.healthReport.summary.critical_projects,
        framework_compliance: this.healthReport.summary.framework_compliance,
        overall_health: this.healthReport.summary.overall_health_percentage,
        alerts_generated: this.healthReport.alerts.length
      });
      
    } catch (err) {
      this.log('error', 'Health check failed', { error: err.message });
      this.addAlert('critical', `Health check failed: ${err.message}`);
    }
  }

  calculateOverallHealth() {
    const { summary, services, framework } = this.healthReport;
    
    // Calculate project health percentage
    let projectHealthPercentage = 0;
    if (summary.total_projects > 0) {
      projectHealthPercentage = Math.round((summary.healthy_projects / summary.total_projects) * 100);
    }
    
    // Calculate service health percentage
    const totalServices = Object.keys(services).length;
    const healthyServices = Object.values(services).filter(s => s.status === 'healthy').length;
    const serviceHealthPercentage = totalServices > 0 ? Math.round((healthyServices / totalServices) * 100) : 100;
    
    // Calculate framework compliance percentage
    const frameworkCompliance = framework.compliance_percentage || 0;
    
    // Weighted overall health score
    const weights = {
      projects: 0.4,      // 40% weight
      services: 0.35,     // 35% weight  
      framework: 0.25     // 25% weight
    };
    
    const overallHealth = Math.round(
      (projectHealthPercentage * weights.projects) +
      (serviceHealthPercentage * weights.services) +
      (frameworkCompliance * weights.framework)
    );
    
    summary.overall_health_percentage = overallHealth;
    summary.project_health_percentage = projectHealthPercentage;
    summary.service_health_percentage = serviceHealthPercentage;
    summary.framework_compliance = frameworkCompliance;
  }

  checkCriticalThresholds() {
    const { summary } = this.healthReport;
    
    // Check overall health threshold
    if (summary.overall_health_percentage < this.config.alertThreshold) {
      this.addAlert('critical', 
        `Overall health ${summary.overall_health_percentage}% is below alert threshold ${this.config.alertThreshold}%`
      );
    }
    
    // Check for critical projects
    if (summary.critical_projects > 0) {
      this.addAlert('critical', 
        `${summary.critical_projects} project(s) have critical issues requiring immediate attention`
      );
    }
    
    // Check service availability
    const criticalServices = Object.values(this.healthReport.services)
      .filter(s => s.critical && s.status !== 'healthy');
    
    if (criticalServices.length > 0) {
      criticalServices.forEach(service => {
        this.addAlert('critical', 
          `Critical service ${service.name} is ${service.status}`,
          { service: service.name, error: service.error }
        );
      });
    }
    
    // Check framework compliance
    if (summary.framework_compliance < 50) {
      this.addAlert('critical', 
        `Framework compliance ${summary.framework_compliance}% is critically low`
      );
    }
  }

  saveMonitorStatus() {
    try {
      fs.writeFileSync(this.statusFile, JSON.stringify(this.monitorStatus, null, 2));
    } catch (err) {
      this.log('error', 'Failed to save monitor status', { error: err.message });
    }
  }

  getMonitorStatus() {
    try {
      if (fs.existsSync(this.statusFile)) {
        return JSON.parse(fs.readFileSync(this.statusFile, 'utf8'));
      }
    } catch (err) {
      this.log('warning', 'Failed to read monitor status', { error: err.message });
    }
    return null;
  }

  startContinuousMonitoring() {
    this.log('info', 'Starting continuous health monitoring', { 
      interval_minutes: this.checkInterval / (60 * 1000) 
    });
    
    // Run initial check
    this.runHealthCheck();
    
    // Set up periodic monitoring
    setInterval(() => {
      this.runHealthCheck();
    }, this.checkInterval);
  }

  // Graceful shutdown
  setupGracefulShutdown() {
    process.on('SIGINT', () => {
      this.log('info', 'Received SIGINT, shutting down gracefully...');
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      this.log('info', 'Received SIGTERM, shutting down gracefully...');
      process.exit(0);
    });
  }
}

// CLI interface
if (require.main === module) {
  const command = process.argv[2];
  const options = {};
  
  // Parse command line options
  for (let i = 3; i < process.argv.length; i++) {
    const arg = process.argv[i];
    if (arg === '--verbose' || arg === '-v') {
      options.verbose = true;
    } else if (arg === '--no-alerts') {
      options.enableAlerting = false;
    } else if (arg === '--no-services') {
      options.enableServiceChecks = false;
    } else if (arg === '--no-git') {
      options.enableGitChecks = false;
    } else if (arg.startsWith('--interval=')) {
      options.interval = parseInt(arg.split('=')[1]) * 60 * 1000; // Convert minutes to ms
    } else if (arg.startsWith('--threshold=')) {
      options.alertThreshold = parseInt(arg.split('=')[1]);
    }
  }
  
  const monitor = new ClaudePMHealthMonitor(options);
  monitor.setupGracefulShutdown();
  
  switch (command) {
    case 'once':
      monitor.runHealthCheck().then(() => {
        console.log('\n📊 Health check completed. Reports saved to:');
        console.log(`  📝 JSON Report: ${monitor.claudePMPath}/logs/health-report.json`);
        console.log(`  📋 Summary: ${monitor.claudePMPath}/logs/health-summary.md`);
        console.log(`  📈 Monitor Log: ${monitor.claudePMPath}/logs/health-monitor.log`);
        if (monitor.healthReport.alerts.length > 0) {
          console.log(`  🚨 Alerts Log: ${monitor.claudePMPath}/logs/health-alerts.log`);
        }
        process.exit(0);
      }).catch(err => {
        console.error('Health check failed:', err.message);
        process.exit(1);
      });
      break;
      
    case 'monitor':
    case 'continuous':
      console.log('🔄 Starting continuous health monitoring...');
      console.log(`📊 Check interval: ${options.interval || monitor.config.checkInterval} ms`);
      console.log(`🚨 Alert threshold: ${options.alertThreshold || monitor.config.alertThreshold}%`);
      console.log('💡 Use Ctrl+C to stop monitoring\n');
      monitor.startContinuousMonitoring();
      break;
      
    case 'status':
      const status = monitor.getMonitorStatus();
      if (status) {
        console.log('📊 Monitor Status:');
        console.log(`  PID: ${status.pid}`);
        console.log(`  Started: ${new Date(status.startTime).toLocaleString()}`);
        console.log(`  Last Check: ${status.lastCheck ? new Date(status.lastCheck).toLocaleString() : 'Never'}`);
        console.log(`  Checks Run: ${status.checksRun}`);
        console.log(`  Alerts Sent: ${status.alertsSent}`);
        
        // Show latest health summary if available
        const reportPath = path.join(monitor.claudePMPath, 'logs/health-report.json');
        if (fs.existsSync(reportPath)) {
          try {
            const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
            console.log('\n📈 Latest Health Summary:');
            console.log(`  Overall Health: ${report.summary.overall_health_percentage}%`);
            console.log(`  Total Projects: ${report.summary.total_projects}`);
            console.log(`  Healthy Projects: ${report.summary.healthy_projects}`);
            console.log(`  Warning Projects: ${report.summary.warning_projects}`);
            console.log(`  Critical Projects: ${report.summary.critical_projects}`);
            console.log(`  Framework Compliance: ${report.summary.framework_compliance}%`);
            console.log(`  Last Updated: ${new Date(report.timestamp).toLocaleString()}`);
            
            if (report.alerts && report.alerts.length > 0) {
              console.log(`\n🚨 Recent Alerts: ${report.alerts.length}`);
              report.alerts.slice(-3).forEach(alert => {
                console.log(`  [${alert.level.toUpperCase()}] ${alert.message}`);
              });
            }
          } catch (err) {
            console.log('  Error reading health report:', err.message);
          }
        }
      } else {
        console.log('❌ No monitoring status found. Monitor may not be running.');
      }
      break;
      
    case 'reports':
      // Show available reports
      const logsDir = path.join(monitor.claudePMPath, 'logs');
      if (fs.existsSync(logsDir)) {
        console.log('📁 Available Health Reports:');
        const files = fs.readdirSync(logsDir).filter(f => f.includes('health'));
        files.forEach(file => {
          const filePath = path.join(logsDir, file);
          const stats = fs.statSync(filePath);
          console.log(`  📄 ${file} (${stats.size} bytes, ${stats.mtime.toLocaleString()})`);
        });
      } else {
        console.log('❌ No logs directory found.');
      }
      break;
      
    case 'alerts':
      // Show recent alerts
      const alertPath = path.join(monitor.claudePMPath, 'logs/health-alerts.log');
      if (fs.existsSync(alertPath)) {
        console.log('🚨 Recent Health Alerts:');
        const alerts = fs.readFileSync(alertPath, 'utf8').split('\n').filter(l => l.trim());
        alerts.slice(-10).forEach(alert => console.log(`  ${alert}`));
      } else {
        console.log('✅ No alerts found.');
      }
      break;
      
    default:
      console.log(`
🏥 Claude PM Enhanced Automated Health Monitor v2.0.0

Usage:
  node automated-health-monitor.js <command> [options]

Commands:
  once                          # Run single health check
  monitor|continuous           # Start continuous monitoring  
  status                       # Show monitor status and latest health summary
  reports                      # List available health reports
  alerts                       # Show recent alerts

Options:
  --verbose, -v                # Enable verbose logging
  --no-alerts                  # Disable alert notifications
  --no-services                # Skip service health checks
  --no-git                     # Skip git repository checks
  --interval=<minutes>         # Set monitoring interval (default: 5)
  --threshold=<percentage>     # Set alert threshold (default: 60)

Examples:
  node automated-health-monitor.js once --verbose
  node automated-health-monitor.js monitor --interval=10 --threshold=70
  node automated-health-monitor.js status

Output Files:
  📝 JSON Report: ~/Projects/Claude-PM/logs/health-report.json
  📋 Markdown Summary: ~/Projects/Claude-PM/logs/health-summary.md  
  📈 Monitor Log: ~/Projects/Claude-PM/logs/health-monitor.log
  🚨 Alerts Log: ~/Projects/Claude-PM/logs/health-alerts.log
  📊 Status File: ~/Projects/Claude-PM/logs/monitor-status.json

Features:
  ✅ Service availability monitoring (mem0ai, portfolio manager, etc.)
  ✅ Framework compliance validation (CLAUDE.md, TrackDown system)
  ✅ Managed projects health assessment
  ✅ Git repository activity tracking
  ✅ Intelligent alerting and recommendations
  ✅ Background monitoring with PM2/systemd compatibility
  ✅ Performance metrics and response time tracking
      `);
      process.exit(1);
  }
}

module.exports = ClaudePMHealthMonitor;