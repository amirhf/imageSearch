# Multi-Tenant Implementation Guide

Complete guide for transforming imageSearch from single-tenant to multi-tenant SaaS with Supabase Auth.

## 📚 Documentation Structure

1. **[00_OVERVIEW.md](./00_OVERVIEW.md)** - Executive summary, architecture, and timeline
2. **[01_DATABASE_SCHEMA.md](./01_DATABASE_SCHEMA.md)** - Database migrations and schema changes
3. **[02_AUTHENTICATION.md](./02_AUTHENTICATION.md)** - Supabase Auth integration and JWT validation
4. **[03_API_ENDPOINTS.md](./03_API_ENDPOINTS.md)** - API endpoint updates with access control
5. **[04_VECTOR_STORES.md](./04_VECTOR_STORES.md)** - PgVector and Qdrant filtering implementation
6. **[05_FRONTEND.md](./05_FRONTEND.md)** - Next.js frontend with Supabase client
7. **[06_MIGRATION_TESTING.md](./06_MIGRATION_TESTING.md)** - Data migration and testing

## 🚀 Quick Start

### Prerequisites

1. **Supabase Project**
   - Create project at [supabase.com](https://supabase.com)
   - Note your project URL and keys
   - Create an admin user

2. **Environment Setup**
   ```bash
   # Add to .env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_JWT_SECRET=your-jwt-secret
   SUPABASE_SECRET_KEY=sb_secret_your-secret-key
   ADMIN_USER_ID=admin-user-uuid
   ```

3. **Install Dependencies**
   ```bash
   # Backend
   pip install supabase==2.3.0 python-jose[cryptography]==3.3.0
   
   # Frontend
   cd apps/ui
   npm install @supabase/supabase-js @supabase/auth-helpers-nextjs
   ```

### Implementation Order

Follow the phases in order:

```bash
# Phase 1: Database Schema (2-3 days)
psql $DATABASE_URL -f apps/api/storage/migrations/001_add_profiles.sql
psql $DATABASE_URL -f apps/api/storage/migrations/002_add_multi_tenant_fields.sql
psql $DATABASE_URL -f apps/api/storage/migrations/003_backfill_existing_images.sql

# Phase 2: Authentication (3-4 days)
# Implement auth dependencies and endpoints
# See 02_AUTHENTICATION.md

# Phase 3: API Endpoints (4-5 days)
# Update all endpoints with access control
# See 03_API_ENDPOINTS.md

# Phase 4: Vector Stores (3-4 days)
# Update pgvector and Qdrant with filtering
# See 04_VECTOR_STORES.md

# Phase 5: Frontend (5-6 days)
# Build auth UI and multi-tenant features
# See 05_FRONTEND.md

# Phase 6: Migration & Testing (2-3 days)
python scripts/migrate_to_multi_tenant.py
pytest tests/test_multi_tenant_e2e.py -v
```

## 📋 Key Features

### User Authentication
- Email/password signup and login via Supabase
- JWT-based API authentication
- Session management
- Role-based access (user/admin)

### Image Ownership
- Each image has an `owner_user_id`
- Users can only modify their own images
- Admins can manage all images

### Visibility Control
- **Private**: Only owner can see
- **Public**: All authenticated users can see
- **Public Admin**: System-seeded public content

### Scoped Search
- `scope=mine`: User's private images only
- `scope=public`: All public images
- `scope=all`: User's private + all public

### Access Control
- Anonymous users: Public images only
- Authenticated users: Own private + all public
- Admins: Full access to all images

## 🎯 Timeline

**Total: 19-25 days (4-5 weeks)**

- Week 1: Database + Authentication
- Week 2: API + Vector Stores
- Week 3: Frontend
- Week 4: Migration + Testing + Polish

## ✅ Success Criteria

- [ ] Users can sign up and log in
- [ ] Authenticated users can upload private images
- [ ] Users can toggle image visibility
- [ ] Search respects ownership and visibility
- [ ] Anonymous users see only public images
- [ ] Users can view their library (scope=mine)
- [ ] Users can explore public images (scope=public)
- [ ] Soft deletion works correctly
- [ ] All existing images migrated successfully
- [ ] Test coverage > 80%

## 🔧 Testing

```bash
# Run all tests
pytest tests/ -v

# Specific test suites
pytest tests/test_auth.py -v
pytest tests/test_api_multi_tenant.py -v
pytest tests/test_vector_stores.py -v
pytest tests/test_multi_tenant_e2e.py -v

# Performance tests
pytest tests/test_performance.py -v
```

## 📊 Architecture Diagram

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ JWT Token
       ▼
┌─────────────┐     ┌──────────────┐
│  Next.js UI │────▶│  Supabase    │
│  (Frontend) │     │  Auth        │
└──────┬──────┘     └──────────────┘
       │ Bearer Token
       ▼
┌─────────────┐     ┌──────────────┐
│  FastAPI    │────▶│  PostgreSQL  │
│  (Backend)  │     │  + pgvector  │
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│   Qdrant    │
│  (Optional) │
└─────────────┘
```

## 🔐 Security Considerations

1. **JWT Validation**
   - Always validate JWT signature
   - Check expiration and audience
   - Never trust client-supplied user IDs

2. **Access Control**
   - Enforce ownership checks on all mutations
   - Filter queries by ownership/visibility
   - Use database-level RLS when possible

3. **API Keys**
   - Store in environment variables
   - Never commit to version control
   - Rotate regularly

4. **CORS**
   - Whitelist specific origins
   - Enable credentials
   - Validate Authorization header

## 🐛 Troubleshooting

### Common Issues

**JWT validation fails**
- For legacy/shared-secret `HS256` tokens, check `SUPABASE_JWT_SECRET` matches the dashboard
- For asymmetric `ES256`/`RS256` tokens, check `SUPABASE_URL` and API access to the Supabase JWKS endpoint
- Verify token hasn't expired
- Ensure `aud` claim is "authenticated"

**Slow queries**
- Check indexes with `EXPLAIN ANALYZE`
- Ensure `deleted_at IS NULL` filter is first
- Consider composite indexes

**CORS errors**
- Add frontend URL to allowed origins
- Enable credentials in CORS config
- Check Authorization header is allowed

**Migration fails**
- Backup database first
- Ensure admin user exists in profiles
- Run migrations in order

## 📈 Performance Tips

1. **Database Indexes**
   - Index `owner_user_id` and `visibility`
   - Use composite indexes for common queries
   - Monitor query performance

2. **Caching**
   - Cache public image lists
   - Use Redis for session data
   - Implement CDN for images

3. **Query Optimization**
   - Limit result sets
   - Use pagination
   - Avoid N+1 queries

## 🚢 Deployment

1. **Backup Database**
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

2. **Test on Staging**
   - Run all migrations
   - Run full test suite
   - Manual testing

3. **Deploy Order**
   - Database migrations
   - Backend API
   - Frontend

4. **Monitor**
   - Error logs
   - Performance metrics
   - User feedback

## 🔮 Future Extensions

### Phase 7: Organization Multi-Tenancy
- Add `tenants` table for organizations
- Implement org-level access control
- Per-tenant quotas and billing

### Phase 8: Advanced Features
- Image sharing via links
- Collaborative collections
- Comments and annotations
- Activity feeds

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the specific phase documentation
3. Check Supabase documentation
4. Open an issue in the repository

## 📝 License

MIT License - See main project LICENSE file

---

**Ready to get started?** Begin with [00_OVERVIEW.md](./00_OVERVIEW.md) for the complete architecture overview.
