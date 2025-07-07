module.exports = {
  apps: [
    {
      name: 'claude-multiagent-pm-health-monitor',
      script: 'scripts/automated-health-monitor.js',
      args: 'monitor --interval=5 --threshold=60',
      cwd: '/Users/masa/Projects/claude-multiagent-pm',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      env_development: {
        NODE_ENV: 'development'
      },
      error_file: 'logs/health-monitor-error.log',
      out_file: 'logs/health-monitor-out.log',
      log_file: 'logs/health-monitor-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      kill_timeout: 3000,
      listen_timeout: 3000,
      restart_delay: 1000
    }
  ]
};