# Vercel Deployment Operations Guide

## Platform Overview
Vercel is a cloud platform for static sites and serverless functions, optimized for frontend frameworks and full-stack applications.

## Local Development

### Prerequisites
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Link project to Vercel (run in project directory)
vercel link
```

### Local Development Server
```bash
# Start local development server
vercel dev

# Specify port (optional)
vercel dev --listen 3001

# Run with specific environment
vercel dev --env .env.local
```

### Project Configuration

#### Basic vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/node"
    }
  ]
}
```

#### Next.js Configuration
```json
{
  "version": 2,
  "framework": "nextjs"
}
```

#### Python/FastAPI Configuration
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

## Remote Deployment

### Deployment Commands
```bash
# Deploy to preview (staging)
vercel

# Deploy to production
vercel --prod

# Deploy specific directory
vercel --cwd ./my-app --prod

# Deploy with environment variables
vercel --prod --env NEXT_PUBLIC_API_URL=https://api.example.com
```

### Environment Variables

#### Setting via CLI
```bash
# Set environment variable
vercel env add API_KEY

# Set for specific environment
vercel env add API_KEY production

# List environment variables
vercel env ls

# Remove environment variable
vercel env rm API_KEY
```

#### Setting via Dashboard
1. Go to project dashboard
2. Navigate to Settings → Environment Variables
3. Add key-value pairs for each environment

#### Common Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...
MONGODB_URI=mongodb://...

# APIs
OPENAI_API_KEY=sk-...
MEM0_API_KEY=...

# Next.js
NEXT_PUBLIC_API_URL=https://api.example.com
NEXTAUTH_SECRET=...
NEXTAUTH_URL=https://your-app.vercel.app

# Custom
NODE_ENV=production
PORT=3000
```

## Project Types

### Static Sites
```json
{
  "version": 2,
  "builds": [
    {
      "src": "build/**",
      "use": "@vercel/static"
    }
  ]
}
```

### Serverless Functions
```bash
# Directory structure
api/
├── hello.js          # /api/hello
├── users/
│   └── [id].js       # /api/users/[id]
└── auth/
    └── login.js      # /api/auth/login
```

### Full-Stack Applications
```json
{
  "version": 2,
  "functions": {
    "app/**/*.js": {
      "runtime": "nodejs18.x"
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/app/$1"
    }
  ]
}
```

## Domain Management

### Custom Domains
```bash
# Add domain
vercel domains add example.com

# Add domain to project
vercel --prod --alias example.com

# List domains
vercel domains ls

# Remove domain
vercel domains rm example.com
```

### DNS Configuration
```bash
# Get DNS records for domain
vercel dns ls example.com

# Add DNS record
vercel dns add example.com A 192.168.1.1

# Remove DNS record
vercel dns rm example.com rec_id
```

## Monitoring & Analytics

### Deployment Status
```bash
# List deployments
vercel ls

# Get deployment info
vercel inspect [deployment-url]

# View deployment logs
vercel logs [deployment-url]

# Cancel deployment
vercel cancel [deployment-url]
```

### Analytics Dashboard
- Visit project dashboard on vercel.com
- View visitor analytics, performance metrics
- Monitor function execution and edge requests

## Advanced Configuration

### Build Settings
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/node",
      "config": {
        "maxLambdaSize": "50mb",
        "runtime": "nodejs18.x"
      }
    }
  ]
}
```

### Redirects & Rewrites
```json
{
  "redirects": [
    {
      "source": "/old-page",
      "destination": "/new-page",
      "permanent": true
    }
  ],
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://api.example.com/$1"
    }
  ]
}
```

### Headers
```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        }
      ]
    }
  ]
}
```

## CI/CD Integration

### GitHub Integration
1. Connect GitHub repository in Vercel dashboard
2. Configure auto-deployments for branches
3. Set up preview deployments for pull requests

### Custom Build Process
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install --legacy-peer-deps"
}
```

## Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check build logs
vercel logs [deployment-url]

# Run build locally
vercel build

# Debug with verbose output
vercel --debug
```

#### Function Timeouts
- Default timeout: 10 seconds (Hobby), 60 seconds (Pro)
- Optimize function performance
- Consider using Edge Functions for faster response

#### Environment Variable Issues
```bash
# Verify environment variables
vercel env ls

# Test locally with environment
vercel dev --env .env.local
```

#### Domain/SSL Issues
- Verify DNS records are correct
- Check SSL certificate status in dashboard
- Allow time for DNS propagation (up to 48 hours)

### Debug Commands
```bash
# Verbose deployment
vercel --debug --prod

# Local function testing
vercel dev --debug

# Check project configuration
vercel inspect

# Test function locally
curl http://localhost:3000/api/test
```

## Security Best Practices

### Environment Variables
- Use environment variables for secrets
- Never commit sensitive data to repository
- Use different variables for different environments

### Function Security
- Validate all inputs
- Implement rate limiting
- Use CORS headers appropriately
- Sanitize user data

### Domain Security
- Use HTTPS only
- Implement proper CORS policies
- Set security headers

## Cost Optimization

### Function Usage
- Monitor function execution time
- Optimize bundle sizes
- Use Edge Functions when possible
- Implement caching strategies

### Bandwidth
- Optimize images and assets
- Use CDN for static content
- Implement compression

---

**Platform**: Vercel
**CLI Version**: Latest
**Last Updated**: 2025-07-05
**Integration Status**: Ready for deployment