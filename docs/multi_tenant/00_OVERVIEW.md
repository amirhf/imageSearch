# Multi-Tenant Implementation Plan - Overview

## Executive Summary

Transform the imageSearch application from single-tenant to multi-tenant SaaS by integrating **Supabase Auth** and implementing **per-user ownership** with **visibility controls**. This enables users to manage private image libraries while maintaining a shared public search space.

## Architecture Changes

### Current State
- Single-tenant application
- No user authentication
- All images are publicly accessible
- No ownership or access control

### Target State
- Multi-tenant SaaS application
- Supabase-based authentication
- Per-user private image libraries
- Three visibility levels: `private`, `public`, `public_admin`
- Scoped search: `mine`, `public`, `all`
- Soft deletion support

## Key Features

1. **User Authentication** (Supabase Auth)
   - Email/password signup and login
   - JWT-based API authentication
   - Session management

2. **Image Ownership**
   - Each image has an `owner_user_id`
   - Users can only modify their own images
   - Admin users can manage all images

3. **Visibility Control**
   - `private`: Only owner can see
   - `public`: All authenticated users can see
   - `public_admin`: Admin-seeded public content

4. **Scoped Search**
   - `scope=mine`: User's private images only
   - `scope=public`: All public images
   - `scope=all`: User's private + all public images

5. **Access Control**
   - Anonymous users: Can only view public images
   - Authenticated users: Can view own private + all public
   - Admins: Can view and manage all images

## Implementation Phases

### Phase 1: Database Schema (2-3 days)
- Add `profiles` table for user metadata
- Extend `images` table with ownership and visibility fields
- Create indexes for performance
- Backfill existing data

**File:** `01_DATABASE_SCHEMA.md`

### Phase 2: Authentication & Authorization (3-4 days)
- Install Supabase dependencies
- Create JWT validation middleware
- Implement auth dependencies (get_current_user, require_auth, require_admin)
- Add auth endpoints

**File:** `02_AUTHENTICATION.md`

### Phase 3: API Endpoints (4-5 days)
- Update POST /images (require auth, add visibility)
- Update GET /images/{id} (access control)
- Update GET /search (scoped search)
- Add PATCH /images/{id} (update visibility)
- Add DELETE /images/{id} (soft delete)

**File:** `03_API_ENDPOINTS.md`

### Phase 4: Vector Stores (3-4 days)
- Update PgVectorStore with ownership filtering
- Update QdrantStore with payload-based filtering
- Implement scoped search queries
- Add visibility update and soft delete methods

**File:** `04_VECTOR_STORES.md`

### Phase 5: Frontend Integration (5-6 days)
- Install Supabase client libraries
- Create auth context and providers
- Build login/signup pages
- Update upload page with visibility control
- Create library and explore pages
- Update navigation based on auth state

**File:** `05_FRONTEND.md`

### Phase 6: Migration & Testing (2-3 days)
- Create database migration scripts
- Update Qdrant payloads
- Write comprehensive test suite
- Perform end-to-end testing
- Document deployment process

**File:** `06_MIGRATION_TESTING.md`

## Timeline

**Total Estimated Time:** 19-25 days (4-5 weeks)

- Week 1: Database schema + Authentication
- Week 2: API endpoints + Vector stores
- Week 3: Frontend integration
- Week 4: Migration, testing, and polish

## Prerequisites

### Environment Setup
1. Supabase project created
2. JWT secret configured
3. Admin user created in Supabase
4. Environment variables updated

### Dependencies
```bash
# Backend
pip install supabase==2.3.0 python-jose[cryptography]==3.3.0

# Frontend
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs
```

### Environment Variables
```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_SECRET_KEY=sb_secret_your-secret-key
ADMIN_USER_ID=uuid-of-admin-user
```

## Success Criteria

- [ ] Users can sign up and log in via Supabase
- [ ] Authenticated users can upload private images
- [ ] Users can toggle image visibility (private/public)
- [ ] Search respects ownership and visibility
- [ ] Anonymous users can only see public images
- [ ] Users can view their library (scope=mine)
- [ ] Users can explore public images (scope=public)
- [ ] Soft deletion works correctly
- [ ] All existing images migrated successfully
- [ ] Comprehensive test coverage (>80%)

## Risk Mitigation

### Data Migration Risks
- **Risk:** Existing images lose data during migration
- **Mitigation:** Backup database before migration, test on staging first

### Performance Risks
- **Risk:** Filtering by ownership slows down queries
- **Mitigation:** Proper indexing on `owner_user_id` and `visibility`

### Security Risks
- **Risk:** JWT validation bypass
- **Mitigation:** Thorough testing of auth middleware, use Supabase's proven libraries

### Backward Compatibility
- **Risk:** Breaking changes for existing API clients
- **Mitigation:** Version API endpoints, maintain backward compatibility for public images

## Future Extensions

### Phase 7: Organization Multi-Tenancy
- Add `tenants` table for organizations
- Add `user_tenants` join table
- Implement org-level access control
- Per-tenant quotas and billing

### Phase 8: Advanced Features
- Image sharing via links
- Collaborative collections
- Image comments and annotations
- Activity feeds and notifications

## Next Steps

1. Review this overview with the team
2. Set up Supabase project
3. Begin Phase 1: Database Schema
4. Follow implementation guides in order

## Documentation Structure

```
docs/multi_tenant/
├── 00_OVERVIEW.md (this file)
├── 01_DATABASE_SCHEMA.md
├── 02_AUTHENTICATION.md
├── 03_API_ENDPOINTS.md
├── 04_VECTOR_STORES.md
├── 05_FRONTEND.md
└── 06_MIGRATION_TESTING.md
```

Each phase document contains:
- Detailed implementation steps
- Code examples
- Testing guidelines
- Troubleshooting tips
