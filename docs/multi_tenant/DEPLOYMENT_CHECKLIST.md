# Multi-Tenant Deployment Checklist

This checklist ensures a smooth deployment of the multi-tenant image search application.

## Pre-Deployment

### 1. Environment Configuration

#### Backend (.env)
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `QDRANT_URL` - Qdrant server URL (if using)
- [ ] `VECTOR_BACKEND` - Set to `pgvector` or `qdrant`
- [ ] `SUPABASE_URL` - Supabase project URL
- [ ] `SUPABASE_JWT_SECRET` - JWT secret from Supabase settings
- [ ] `SUPABASE_SECRET_KEY` - Secret API key (`sb_secret_...`) for backend/admin operations only
- [ ] `ADMIN_USER_ID` - UUID of admin user
- [ ] Storage configuration (S3/MinIO/R2)
- [ ] Model configuration (embedder, captioner)

#### Frontend (.env.local)
- [ ] `NEXT_PUBLIC_API_BASE` - Backend API URL
- [ ] `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- [ ] `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` - Supabase publishable key (`sb_publishable_...`)

### 2. Database Setup

- [ ] PostgreSQL database created
- [ ] Run migrations:
  ```bash
  # Inside Docker container or with local psql
  psql $DATABASE_URL < apps/api/storage/migrations/001_add_profiles.sql
  psql $DATABASE_URL < apps/api/storage/migrations/002_add_multi_tenant_fields.sql
  ```
- [ ] Verify tables exist: `profiles`, `images` with multi-tenant columns
- [ ] Create indexes (should be in migrations)
- [ ] Verify pgvector extension installed

### 3. Supabase Configuration

- [ ] Supabase project created
- [ ] Email authentication enabled
- [ ] Redirect URLs configured:
  - Development: `http://localhost:3100/auth/callback`
  - Production: `https://yourdomain.com/auth/callback`
- [ ] JWT secret obtained from settings
- [ ] Service role key obtained
- [ ] Email templates customized (optional)

### 4. Data Migration

- [ ] Backup existing database
- [ ] Run migration script:
  ```bash
  python scripts/migrate_to_multitenant.py
  ```
- [ ] Verify all images have owners
- [ ] Verify visibility distribution
- [ ] If using Qdrant, verify metadata synced

### 5. Testing

- [ ] Run all backend tests:
  ```bash
  pytest tests/ -v
  ```
- [ ] Run E2E tests:
  ```bash
  pytest tests/test_e2e_multitenant.py -v
  ```
- [ ] Manual testing:
  - [ ] User signup/login
  - [ ] Upload private image
  - [ ] Upload public image
  - [ ] View library
  - [ ] Toggle visibility
  - [ ] Delete image
  - [ ] Browse explore page
  - [ ] Search with different scopes

## Deployment Steps

### 1. Backend Deployment

#### Docker Deployment
```bash
# Build and deploy
cd infra
docker-compose up -d

# Verify services
docker-compose ps
docker-compose logs api
```

#### Cloud Run / Kubernetes
- [ ] Build Docker image
- [ ] Push to container registry
- [ ] Deploy with environment variables
- [ ] Configure health checks
- [ ] Set up autoscaling
- [ ] Configure load balancer

### 2. Frontend Deployment

#### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd apps/ui
vercel --prod
```

- [ ] Set environment variables in Vercel dashboard
- [ ] Configure custom domain
- [ ] Enable automatic deployments from Git

#### Docker / Self-Hosted
```bash
# Build
cd apps/ui
npm run build

# Deploy with Docker
docker build -t image-search-ui .
docker run -p 3100:3100 image-search-ui
```

### 3. Database

- [ ] Production database provisioned
- [ ] Connection pooling configured
- [ ] Backups enabled
- [ ] Monitoring set up
- [ ] SSL/TLS enabled

### 4. Storage

- [ ] S3/MinIO/R2 bucket created
- [ ] CORS configured for frontend
- [ ] Lifecycle policies set (optional)
- [ ] CDN configured (optional)

### 5. Vector Store

#### PgVector
- [ ] Included in PostgreSQL setup
- [ ] Indexes created
- [ ] Performance tuned

#### Qdrant
- [ ] Qdrant server deployed
- [ ] Collection created
- [ ] Metadata synced
- [ ] Backups configured

## Post-Deployment

### 1. Verification

- [ ] Health checks passing
- [ ] All services responding
- [ ] Database connections working
- [ ] Authentication working
- [ ] Image upload working
- [ ] Search working
- [ ] Visibility controls working

### 2. Monitoring

- [ ] Application logs configured
- [ ] Error tracking (Sentry, etc.)
- [ ] Performance monitoring (New Relic, DataDog, etc.)
- [ ] Uptime monitoring
- [ ] Database monitoring
- [ ] Alert rules configured

### 3. Security

- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] CSRF tokens configured
- [ ] Secrets not in code
- [ ] Environment variables secured

### 4. Performance

- [ ] CDN configured for static assets
- [ ] Image optimization enabled
- [ ] Database query optimization
- [ ] Caching strategy implemented
- [ ] Connection pooling configured

### 5. Backup & Recovery

- [ ] Database backups automated
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] RTO/RPO defined

## Rollback Plan

If issues occur during deployment:

### 1. Backend Rollback
```bash
# Docker
docker-compose down
docker-compose up -d --build <previous-version>

# Cloud
# Deploy previous version from container registry
```

### 2. Database Rollback
```bash
# Restore from backup
pg_restore -d $DATABASE_URL backup.dump

# Or revert migrations (if needed)
# Note: This may cause data loss
```

### 3. Frontend Rollback
```bash
# Vercel
vercel rollback

# Docker
docker run <previous-image>
```

## Monitoring Checklist

### Application Metrics
- [ ] Request rate
- [ ] Error rate
- [ ] Response time
- [ ] Upload success rate
- [ ] Search latency

### Infrastructure Metrics
- [ ] CPU usage
- [ ] Memory usage
- [ ] Disk usage
- [ ] Network traffic
- [ ] Database connections

### Business Metrics
- [ ] Active users
- [ ] Images uploaded
- [ ] Searches performed
- [ ] Public vs private images
- [ ] User retention

## Troubleshooting

### Common Issues

#### "Invalid JWT" errors
- For legacy/shared-secret `HS256` tokens, verify `SUPABASE_JWT_SECRET` matches Supabase settings
- For asymmetric `ES256`/`RS256` tokens, verify `SUPABASE_URL` is correct and the API can reach Supabase's JWKS endpoint
- Check token expiration
- Verify token format

#### CORS errors
- Check API CORS configuration
- Verify frontend URL in allowed origins
- Check preflight requests

#### Upload failures
- Verify storage credentials
- Check file size limits
- Verify embedder/captioner working

#### Search not working
- Verify vector store connection
- Check embedder is working
- Verify indexes exist

#### Images not appearing
- Check visibility settings
- Verify user authentication
- Check deleted_at field

## Performance Optimization

### Database
- [ ] Indexes on frequently queried columns
- [ ] Connection pooling configured
- [ ] Query optimization
- [ ] Vacuum and analyze scheduled

### API
- [ ] Response caching
- [ ] Rate limiting
- [ ] Request compression
- [ ] Keep-alive connections

### Frontend
- [ ] Image lazy loading
- [ ] Code splitting
- [ ] Asset optimization
- [ ] Service worker (PWA)

### Vector Search
- [ ] Appropriate index type (HNSW)
- [ ] Optimized vector dimensions
- [ ] Batch operations
- [ ] Query result caching

## Security Hardening

- [ ] Change default admin credentials
- [ ] Rotate secrets regularly
- [ ] Enable audit logging
- [ ] Implement rate limiting
- [ ] Set up WAF (Web Application Firewall)
- [ ] Regular security scans
- [ ] Dependency updates
- [ ] Security headers configured

## Documentation

- [ ] API documentation updated
- [ ] User guide created
- [ ] Admin guide created
- [ ] Troubleshooting guide
- [ ] Architecture diagrams
- [ ] Runbooks for common tasks

## Sign-Off

- [ ] Development team approval
- [ ] QA team approval
- [ ] Security team approval
- [ ] Operations team approval
- [ ] Stakeholder approval

## Post-Launch

- [ ] Monitor for 24 hours
- [ ] Address any issues
- [ ] Gather user feedback
- [ ] Plan next iteration
- [ ] Document lessons learned

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Version:** _________________

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
