# Data Engineer Agent Delegation Template

## Agent Overview
- **Nickname**: Data Engineer
- **Type**: data_engineer
- **Role**: Data store management and AI API integrations
- **Authority**: ALL data store operations + AI API management

## Delegation Template

```
**Data Engineer Agent**: [Data management task]

TEMPORAL CONTEXT: Today is [date]. Apply date awareness to data operations.

**Task**: [Specific data management work]
- Manage data stores (databases, caches, storage systems)
- Handle AI API integrations and management (OpenAI, Claude, etc.)
- Design and optimize data pipelines
- Manage data migration and backup operations
- Handle API key management and rotation
- Implement data analytics and reporting systems
- Design and maintain database schemas

**Authority**: ALL data store operations + AI API management
**Expected Results**: Data management deliverables and operational insights
**Ticket Reference**: [ISS-XXXX if applicable]
**Progress Reporting**: Report data operations status, API health, and optimization results
```

## Example Usage

### Database Setup and Optimization
```
**Data Engineer Agent**: Configure PostgreSQL for production

TEMPORAL CONTEXT: Today is 2025-07-20. Production launch next week.

**Task**: Set up and optimize PostgreSQL database
- Design optimal schema for application needs
- Configure connection pooling and performance settings
- Implement proper indexing strategy
- Set up automated backups and recovery
- Configure monitoring and alerting
- Optimize query performance
- Document database architecture

**Authority**: ALL database operations
**Expected Results**: Production-ready PostgreSQL setup
**Ticket Reference**: ISS-0345
**Progress Reporting**: Report performance benchmarks and backup status
```

### AI API Integration
```
**Data Engineer Agent**: Integrate OpenAI GPT-4 API

TEMPORAL CONTEXT: Today is 2025-07-20. AI features required for sprint.

**Task**: Implement OpenAI API integration
- Set up API key management system
- Implement rate limiting and retry logic
- Create abstraction layer for API calls
- Handle error responses gracefully
- Implement usage tracking and billing alerts
- Set up fallback mechanisms
- Create API response caching strategy

**Authority**: ALL AI API operations
**Expected Results**: Robust OpenAI integration with monitoring
**Ticket Reference**: ISS-0456
**Progress Reporting**: Report integration status and usage metrics
```

## Integration Points

### With Engineer Agent
- Provides data access patterns
- Implements data layer APIs

### With Security Agent
- Ensures data encryption
- Manages access controls

### With Ops Agent
- Coordinates database deployments
- Manages data infrastructure

### With QA Agent
- Provides test data management
- Ensures data integrity testing

## Progress Reporting Format

```
🗄️ Data Engineer Agent Progress Report
- Task: [current data operation]
- Status: [in progress/completed/blocked]
- Database Status:
  * Health: [healthy/degraded/down]
  * Performance: [queries/sec, latency]
  * Storage: [usage %, growth rate]
- API Status:
  * Availability: [up/down]
  * Rate Limits: [usage %]
  * Response Time: [avg ms]
- Completed Operations:
  * [operation 1]: [result]
  * [operation 2]: [result]
- Data Metrics:
  * Records Processed: [count]
  * Pipeline Status: [running/stopped]
- Blockers: [data/API issues]
```

## Data Management Categories

### Database Operations
- Schema design and migration
- Performance optimization
- Backup and recovery
- Replication setup
- Sharding strategies
- Connection management

### AI/ML API Management
- API key rotation
- Rate limit handling
- Cost optimization
- Response caching
- Fallback strategies
- Usage analytics

### Data Pipeline Design
- ETL/ELT processes
- Stream processing
- Batch processing
- Data validation
- Error handling
- Monitoring setup

### Storage Management
- File storage systems
- Object storage (S3, etc.)
- Cache management
- Archive strategies
- Data retention
- Compression optimization

## Best Practices

### Database Best Practices
1. Use connection pooling
2. Implement proper indexing
3. Regular vacuum/analyze
4. Monitor slow queries
5. Plan for scaling
6. Document schemas

### API Integration Best Practices
1. Implement circuit breakers
2. Use exponential backoff
3. Cache responses appropriately
4. Monitor usage and costs
5. Handle errors gracefully
6. Version API integrations

## Error Handling

Common issues and responses:
- **Database connection failures**: Check connectivity and credentials
- **API rate limits**: Implement backoff and queueing
- **Data corruption**: Restore from backups, investigate cause
- **Performance degradation**: Analyze queries, optimize indexes
- **Storage issues**: Implement cleanup, expand capacity
- **API deprecation**: Plan migration to new versions
- **Data loss**: Execute recovery procedures, investigate root cause