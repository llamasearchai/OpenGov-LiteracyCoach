# Operational Runbooks

## Quick Reference

### Start Services
```bash
# Development
docker compose up --build

# Production
docker compose -f docker-compose.prod.yml up -d

# Individual service
uv run -m uvicorn litcoach.services.gateway.app:app --reload --port 8000
```

### Check Health
```bash
# All services
litcoach-cli doctor

# Individual service
curl http://localhost:8000/health

# Docker health
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f gateway

# Production with Loki
curl http://localhost:3100/loki/api/v1/query
```

## Service Management

### Gateway Service (Port 8000)

**Purpose:** Web interface and voice interaction handling

**Start:**
```bash
uv run -m uvicorn litcoach.services.gateway.app:app --host 0.0.0.0 --port 8000 --reload
```

**Health Check:**
```bash
curl http://localhost:8000/health
# Expected: {"ok": true, "service": "gateway"}
```

**Common Issues:**
- Port conflicts: Check if port 8000 is in use
- Static files not loading: Verify `litcoach.services.gateway.static` directory exists
- Audio processing failures: Check OpenAI API key and Whisper model

### Agent Service (Port 8001)

**Purpose:** OpenAI agent orchestration with tool calling

**Start:**
```bash
uv run -m uvicorn litcoach.services.agent.app:app --host 0.0.0.0 --port 8001 --reload
```

**Health Check:**
```bash
curl http://localhost:8001/health
# Expected: {"ok": true, "service": "agent"}
```

**Dependencies:** Content and Assessment services must be running

**Common Issues:**
- Tool call failures: Check Content and Assessment service URLs
- OpenAI API errors: Verify API key and model availability
- Memory usage: Monitor for large conversation histories

### Content Service (Port 8002)

**Purpose:** Text catalog and RAG search

**Start:**
```bash
uv run -m uvicorn litcoach.services.content.app:app --host 0.0.0.0 --port 8002 --reload
```

**Health Check:**
```bash
curl http://localhost:8002/health
# Expected: {"ok": true, "service": "content"}
```

**Initialization:** Automatically ingests texts from `data/texts/texts.json` on startup

**Common Issues:**
- Database errors: Check SQLite file permissions
- Embedding failures: Verify OpenAI API key and embedding model
- Missing texts: Ensure `data/texts/texts.json` exists and is valid

### Assessment Service (Port 8003)

**Purpose:** Reading and writing evaluation

**Start:**
```bash
uv run -m uvicorn litcoach.services.assessment.app:app --host 0.0.0.0 --port 8003 --reload
```

**Health Check:**
```bash
curl http://localhost:8003/health
# Expected: {"ok": true, "service": "assessment"}
```

**Common Issues:**
- OpenAI API errors: Check API key and GPT model availability
- Assessment timeouts: Monitor for long text processing

### Teacher Service (Port 8004)

**Purpose:** Roster management and analytics

**Start:**
```bash
uv run -m uvicorn litcoach.services.teacher_api.app:app --host 0.0.0.0 --port 8004 --reload
```

**Health Check:**
```bash
curl http://localhost:8004/health
# Expected: {"ok": true, "service": "teacher"}
```

**Common Issues:**
- Database errors: Check SQLite file permissions
- CSV import failures: Verify CSV format and column names

## Monitoring and Alerting

### Health Checks

**Automated Health Checks:**
```bash
# Set up cron job for health monitoring
*/5 * * * * curl -f http://localhost:8000/health || echo "Gateway unhealthy" | mail admin@domain.com
```

**Docker Health Checks:**
- All containers have built-in health checks
- Failed containers are automatically restarted
- Health status visible in `docker compose ps`

### Metrics Collection

**Prometheus Metrics:**
- Services expose metrics at `/metrics` endpoint
- Configure Prometheus to scrape all service ports
- Default retention: 200 hours

**Key Metrics to Monitor:**
- Response times (gateway, agent, content, assessment)
- Error rates by service
- Memory usage per container
- CPU utilization
- Database connection pools

### Log Aggregation

**Loki Configuration:**
- Centralized logging for all services
- Query logs with LogQL: `{service="gateway"} |= "error"`
- Retention configurable per environment

**Log Levels:**
- INFO: General operational messages
- WARNING: Recoverable issues
- ERROR: Failed operations requiring attention
- DEBUG: Detailed troubleshooting information

## Troubleshooting

### Common Issues

#### OpenAI API Issues
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API connectivity
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# Check rate limits
curl https://api.openai.com/v1/dashboard/billing/usage -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### Service Communication Issues
```bash
# Test service connectivity
curl http://localhost:8001/health  # Agent
curl http://localhost:8002/health  # Content
curl http://localhost:8003/health  # Assessment
curl http://localhost:8004/health  # Teacher

# Check network configuration
docker network ls
docker network inspect literacy-coach_default
```

#### Database Issues
```bash
# Check SQLite integrity
sqlite3 data/content.db "PRAGMA integrity_check;"

# Backup database
cp data/content.db data/content.db.backup

# Check file permissions
ls -la data/
```

#### Memory Issues
```bash
# Check container memory usage
docker stats

# Monitor system memory
free -h

# Check for memory leaks
python -m tracemalloc script.py
```

### Performance Issues

#### Slow Response Times
```bash
# Check service load
htop

# Monitor OpenAI API latency
curl -w "@curl-format.txt" -o /dev/null -s "https://api.openai.com/v1/chat/completions" -H "Authorization: Bearer $OPENAI_API_KEY"

# Check database query performance
sqlite3 data/content.db "EXPLAIN QUERY PLAN SELECT * FROM texts WHERE lexile > 500;"
```

#### High Memory Usage
```bash
# Identify memory-intensive processes
ps aux --sort=-%mem | head -10

# Check vector store size
du -sh data/vector_store/

# Monitor garbage collection
python -c "import gc; gc.set_debug(gc.DEBUG_STATS); gc.collect()"
```

### Recovery Procedures

#### Service Restart
```bash
# Restart single service
docker compose restart gateway

# Restart all services
docker compose down && docker compose up -d

# Emergency restart
killall python && docker compose up -d
```

#### Database Recovery
```bash
# Restore from backup
cp data/content.db.backup data/content.db

# Reinitialize database
rm data/content.db && uv run python -m litcoach.services.content.ingest
```

#### Cache Issues
```bash
# Clear application caches
rm -rf data/runtime/

# Clear vector store
rm -rf data/vector_store/
```

## Backup and Recovery

### Backup Strategy

**Daily Backups:**
```bash
# Create backup directory
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup databases
cp data/content.db "$BACKUP_DIR/"
cp data/teacher.db "$BACKUP_DIR/"

# Backup configuration
cp .env "$BACKUP_DIR/"
cp docker-compose*.yml "$BACKUP_DIR/"

# Backup vector store
cp -r data/vector_store "$BACKUP_DIR/"

# Create archive
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR/"
```

**Automated Backup:**
```bash
# Add to cron
0 2 * * * /path/to/backup-script.sh
```

### Recovery Procedures

**Full System Recovery:**
```bash
# Stop all services
docker compose down

# Restore data
tar -xzf backup_20240101_020000.tar.gz

# Restore databases
cp backup/data/content.db data/
cp backup/data/teacher.db data/

# Start services
docker compose up -d
```

**Database-Only Recovery:**
```bash
# Restore specific database
cp backups/content_db_backup data/content.db

# Restart affected services
docker compose restart content agent
```

## Security Operations

### Certificate Management
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout docker/ssl/key.pem -out docker/ssl/cert.pem -days 365 -nodes

# Renew certificate
openssl x509 -in docker/ssl/cert.pem -noout -dates
```

### Secret Rotation
```bash
# Rotate OpenAI API key
litcoach-cli key-rotate --new-key "sk-new-key"

# Update environment
cp .env .env.backup
# Edit .env with new key
```

### Security Monitoring
```bash
# Check for failed login attempts
docker logs gateway | grep "401"

# Monitor for suspicious activity
docker logs gateway | grep -E "(attack|suspicious|exploit)"

# Check firewall logs
sudo journalctl -u fail2ban
```

## Scaling and Performance

### Horizontal Scaling

**Gateway Scaling:**
```bash
# Multiple gateway instances
docker compose -f docker-compose.prod.yml up -d --scale gateway=3
```

**Database Scaling:**
```yaml
# Use external database for production
services:
  content:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/literacy
```

### Performance Optimization

**Caching:**
```bash
# Enable Redis caching
docker compose -f docker-compose.prod.yml up -d redis
```

**CDN Configuration:**
```nginx
# Nginx configuration for static assets
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Emergency Procedures

### System Outage
```bash
# Immediate actions
1. Check system status: docker compose ps
2. Check logs: docker compose logs -f
3. Check resource usage: docker stats
4. Restart services: docker compose restart
5. Alert team if needed
```

### Data Loss
```bash
# Immediate actions
1. Stop all services: docker compose down
2. Restore from latest backup
3. Verify data integrity
4. Restart services
5. Notify stakeholders
```

### Security Incident
```bash
# Immediate actions
1. Isolate affected systems
2. Preserve evidence (logs, snapshots)
3. Change all credentials
4. Scan for malware
5. Notify security team
6. Follow incident response plan
```

## Maintenance Windows

### Weekly Maintenance
- Review and archive old logs
- Update system packages
- Check disk space usage
- Verify backup integrity
- Review security logs

### Monthly Maintenance
- Update Docker images
- Review and optimize database indexes
- Clean up old sessions/data
- Update SSL certificates
- Performance testing

### Quarterly Maintenance
- Security audit and penetration testing
- Dependency updates
- Performance optimization review
- Disaster recovery testing
- Documentation updates

## Support Contacts

### Development Team
- **On-call:** dev-team@opengov.org
- **Issues:** https://github.com/opengov/literacy-coach/issues
- **Documentation:** https://github.com/opengov/literacy-coach/wiki

### Infrastructure Team
- **Cloud issues:** infra@opengov.org
- **Network problems:** netops@opengov.org

### Security Team
- **Security incidents:** security@opengov.org
- **Vulnerability reports:** security@opengov.org

## Runbook Maintenance

This runbook should be reviewed and updated:
- After any significant system changes
- When new services are added
- After incident resolution
- During quarterly maintenance

Last updated: 2024-01-15