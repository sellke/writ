# Test Database Command (test-database)

## Overview

A comprehensive database diagnostic and auto-fixing command that validates and repairs the entire database stack - from PostgreSQL containers through Prisma ORM to Next.js application connectivity. This command identifies common database setup issues and automatically resolves safe problems while requesting permission for potentially destructive fixes.

## Command Process

### Step 1: Initialize Diagnostic Tracking

**Create diagnostic todos using `todo_write`:**

```json
{
  "todos": [
    {
      "id": "scan-database-stack",
      "content": "Scan database infrastructure (Docker, Prisma, environment)",
      "status": "in_progress"
    },
    {
      "id": "test-connectivity",
      "content": "Test connectivity at each layer (PostgreSQL → Prisma → Next.js)",
      "status": "pending"
    },
    {
      "id": "auto-fix-safe-issues",
      "content": "Auto-fix safe issues (containers, client generation)",
      "status": "pending"
    },
    {
      "id": "request-destructive-fixes",
      "content": "Request permission for destructive fixes (data/env changes)",
      "status": "pending"
    },
    {
      "id": "validate-end-to-end",
      "content": "Validate end-to-end connectivity and report final status",
      "status": "pending"
    }
  ]
}
```

### Step 2: Database Infrastructure Scanning

**Update progress:** Mark "scan-database-stack" as `[in_progress]`

**Scan for database configuration:**

- **Docker Setup**: Check for `docker-compose.yml` and database service configuration
- **Prisma Configuration**: Validate `prisma/schema.prisma` exists and is properly configured
- **Environment Variables**: Check `.env` file and validate database URL format
- **Package Scripts**: Verify database-related npm/pnpm scripts exist
- **Migration Status**: Check for existing migrations and their current state

**Detection targets:**

```bash
# Docker configuration
- docker-compose.yml (database service definition)
- Docker container status (running/stopped/missing)

# Prisma setup
- prisma/schema.prisma (schema definition)
- prisma/migrations/ (migration history)
- node_modules/.prisma/client (generated client)

# Environment configuration
- .env file existence and DATABASE_URL format
- Environment variable consistency across schema and env files

# Project scripts
- package.json database scripts (db:up, db:migrate, etc.)
```

### Step 3: Multi-Layer Connectivity Testing

**Update progress:** Mark "scan-database-stack" as `[completed]` and "test-connectivity" as `[in_progress]`

**Test connectivity at each layer:**

#### Layer 1: Docker Container Connectivity
```bash
# Check if database container exists and is running
docker ps --filter "name=*postgres*" --format "table {{.Names}}\t{{.Status}}"

# Test direct database connection
docker exec -it [container-name] pg_isready -U [username]
```

#### Layer 2: Prisma ORM Connectivity
```bash
# Test Prisma client can connect
npx prisma db pull --preview-feature || echo "Prisma connection failed"

# Validate schema sync
npx prisma migrate status
```

#### Layer 3: Next.js Application Connectivity
```bash
# Test application-level database queries
# Create temporary test script to validate Prisma client works in app context
```

**Connectivity validation:**
- **PostgreSQL**: Direct container connectivity test
- **Prisma**: Schema validation and client generation test
- **Application**: Environment variable resolution and Prisma client instantiation

### Step 4: Safe Auto-Fixes

**Update progress:** Mark "test-connectivity" as `[completed]` and "auto-fix-safe-issues" as `[in_progress]`

**Automatically fix safe issues (no data loss risk):**

#### Container Management
```bash
# Start stopped database containers
if container_stopped; then
  echo "🔧 Starting database container..."
  pnpm run db:up || docker-compose up -d postgres
fi
```

#### Prisma Client Issues
```bash
# Regenerate Prisma client if missing or outdated
if prisma_client_outdated; then
  echo "🔧 Regenerating Prisma client..."
  pnpm run db:generate || npx prisma generate
fi
```

#### Environment Variable Consistency
```bash
# Fix environment variable name mismatches (safe string replacements)
if env_var_mismatch_detected; then
  echo "🔧 Fixing environment variable references..."
  # Update schema.prisma to use consistent variable names
  # Add missing environment variables to .env (non-destructive)
fi
```

#### Package Script Validation
```bash
# Verify database scripts are functional
test_script_execution "db:generate"
test_script_execution "db:up"
```

### Step 5: Destructive Fix Requests

**Update progress:** Mark "auto-fix-safe-issues" as `[completed]` and "request-destructive-fixes" as `[in_progress]`

**Request permission for potentially destructive fixes:**

#### Database Reset (Data Loss)
```
⚠️  Database schema mismatch detected.

Current: 3 pending migrations
Issue: Schema drift detected between database and migration files

DESTRUCTIVE FIX REQUIRED:
Run `pnpm run db:reset` to reset database and apply all migrations.
⚠️  This will DELETE ALL existing data.

Reset database? [y/N]: 
```

#### Environment File Modifications
```
⚠️  Environment variable conflicts detected.

Found: DATABASE_URL and NSEMBLE_DATABASE_URL
Issue: Schema expects DATABASE_URL but both variables exist

PROPOSED FIX:
- Remove NSEMBLE_DATABASE_URL from .env
- Update schema.prisma to use DATABASE_URL consistently

Modify environment configuration? [y/N]:
```

#### Migration Application
```
⚠️  Pending migrations detected.

Found: 2 unapplied migrations
- 20240115_add_user_table
- 20240116_add_posts_relation

PROPOSED FIX:
Run `pnpm run db:migrate` to apply pending migrations.
⚠️  This will modify database schema.

Apply migrations? [y/N]:
```

### Step 6: End-to-End Validation

**Update progress:** Mark "request-destructive-fixes" as `[completed]` and "validate-end-to-end" as `[in_progress]`

**Comprehensive connectivity validation:**

#### Full Stack Test
```typescript
// Test actual database operations through the application stack
const testQuery = `
  SELECT COUNT(*) as table_count 
  FROM information_schema.tables 
  WHERE table_schema = 'public'
`;

// Test Prisma client functionality
const userCount = await prisma.user.count();
const postCount = await prisma.post.count();
```

#### Service Integration Test
```bash
# Test that all database-related services can start
test_service_startup "database"
test_service_startup "prisma_studio" 
test_application_database_connectivity
```

#### Performance Validation
```bash
# Basic performance checks
measure_query_response_time "SELECT 1"
validate_connection_pool_size
check_database_resource_usage
```

### Step 7: Comprehensive Status Report

**Update progress:** Mark "validate-end-to-end" as `[completed]`

**Present detailed diagnostic results:**

```
🔍 Database Stack Diagnostic Complete

=== INFRASTRUCTURE STATUS ===
✅ PostgreSQL Container: Running (port 5433)
✅ Docker Compose: Configured correctly
✅ Prisma Schema: Valid and consistent
✅ Environment Variables: Properly configured
✅ Package Scripts: All functional

=== CONNECTIVITY TESTS ===
✅ PostgreSQL: Direct connection successful
✅ Prisma ORM: Client generated and functional  
✅ Next.js App: Database queries working
✅ Prisma Studio: Available at http://localhost:5555

=== FIXES APPLIED ===
🔧 Started database container (was stopped)
🔧 Regenerated Prisma client (was outdated)
🔧 Fixed environment variable mismatch (DATABASE_URL)

=== DATA VALIDATION ===
📊 Tables: 3 (users, posts, _prisma_migrations)
📊 Users: 1 record
📊 Posts: 1 record
📊 Migrations: 2 applied, 0 pending

=== PERFORMANCE ===
⚡ Query Response: 12ms average
⚡ Connection Pool: 5/10 connections active
⚡ Memory Usage: 45MB (normal)

🎉 Database stack is fully operational!

Next steps:
- Access Prisma Studio: http://localhost:5555
- Run application: pnpm dev
- View database logs: docker-compose logs postgres
```

**If issues remain unfixed:**

```
⚠️  Database Stack Issues Detected

=== REMAINING ISSUES ===
❌ Migration Error: Cannot apply migration_20240115
   → Manual intervention required
   → See: docs/DATABASE_SETUP.md#troubleshooting

❌ Port Conflict: 5433 already in use
   → Stop conflicting service or change port in docker-compose.yml
   → Run: lsof -i :5433 to identify conflicting process

❌ Permission Denied: Cannot write to .env file
   → Check file permissions: chmod 644 .env
   → Ensure file is not readonly

=== MANUAL STEPS REQUIRED ===
1. Resolve migration conflict in prisma/migrations/
2. Free up port 5433 or reconfigure database port
3. Fix file permissions for environment configuration

Re-run /test-database after resolving manual issues.
```

## Core Rules

1. **Hybrid Auto-Fixing** - Automatically fix safe issues, request permission for destructive changes
2. **Full Stack Coverage** - Test entire database stack from Docker to application layer
3. **Non-Destructive by Default** - Never delete data or modify configs without explicit permission
4. **Comprehensive Reporting** - Provide detailed status of all components and fixes applied
5. **Actionable Guidance** - When manual intervention needed, provide specific steps to resolve
6. **Performance Aware** - Include basic performance validation in diagnostic results

## Tool Integration

**Primary Writ tools:**

- `todo_write` - Progress tracking throughout diagnostic process
- `run_terminal_cmd` - Execute database commands, Docker operations, and connectivity tests
- `read_file` - Load configuration files (docker-compose.yml, schema.prisma, .env, package.json)
- `search_replace` - Fix environment variable mismatches and configuration issues
- `codebase_search` - Discover database-related files and configuration patterns
- `list_dir` - Explore project structure for database setup components

**Parallel execution opportunities:**

- Configuration file analysis (docker-compose.yml, schema.prisma, package.json)
- Multi-layer connectivity testing (Docker, Prisma, application)
- Service status checks (container status, client generation, script validation)

## AI Implementation Prompt

```
You are a database infrastructure specialist diagnosing and fixing database stack issues.

MISSION: Validate and repair the complete database stack from PostgreSQL containers through Prisma ORM to Next.js application connectivity.

DIAGNOSTIC SCOPE:
- Docker containers and database services
- Prisma ORM configuration and client generation
- Environment variable consistency and format
- Database connectivity at all stack layers
- Migration status and schema synchronization
- Application-level database integration
- Performance and resource utilization

AUTO-FIX RULES:
SAFE (automatic):
- Start stopped database containers
- Regenerate outdated Prisma clients
- Fix environment variable name consistency
- Validate and repair package script functionality

DESTRUCTIVE (request permission):
- Database resets or data deletion
- Environment file modifications
- Migration application or rollback
- Schema changes or drift resolution

CONNECTIVITY TESTING:
1. PostgreSQL: Direct container connectivity and query execution
2. Prisma: Client generation, schema validation, migration status
3. Application: Environment resolution, Prisma client instantiation, actual queries

REPORTING FORMAT:
- Clear status for each stack layer
- Detailed list of fixes applied automatically
- Specific manual steps required for remaining issues
- Performance metrics and resource usage
- Next steps and service access information

CRITICAL: Always provide actionable guidance for manual intervention when automated fixes cannot resolve issues.
```

## Integration Notes

This command integrates with the existing Writ ecosystem by:

1. **Following established patterns** - Uses same markdown structure and tool integration as other commands
2. **Leveraging project standards** - Works with existing database setup patterns (Prisma + PostgreSQL + Docker)
3. **Complementing other commands** - Supports development workflow alongside `status`, `execute-task`, and `swab`
4. **Respecting user control** - Asks permission for destructive changes while auto-fixing safe issues
5. **Progress transparency** - Uses `todo_write` for visibility into diagnostic and repair process
6. **Comprehensive coverage** - Addresses full database stack rather than individual components

## Error Handling & Recovery

**Common failure scenarios:**

- **No database configuration found**: Guide to database setup documentation
- **Docker not available**: Provide Docker installation guidance
- **Port conflicts**: Identify conflicting processes and suggest resolution
- **Permission issues**: Specific file permission fixes
- **Migration conflicts**: Manual intervention guidance with specific steps

**Recovery strategies:**

1. **Graceful degradation**: Continue diagnostic even if some tests fail
2. **Clear error reporting**: Specific error messages with actionable solutions
3. **Manual intervention guidance**: Detailed steps when automation cannot proceed
4. **Re-run capability**: Command can be safely re-executed after manual fixes
5. **Rollback information**: How to undo changes if issues arise

## Future Enhancements

Potential improvements (not in initial version):

- **Multi-database support**: Handle MySQL, SQLite, and other database types
- **Cloud database testing**: Validate connections to hosted database services
- **Performance benchmarking**: Comprehensive database performance analysis
- **Backup validation**: Verify backup and restore procedures
- **Security scanning**: Check for common database security issues
- **Monitoring integration**: Set up database monitoring and alerting

But for now: Focus on core PostgreSQL + Prisma + Next.js stack with comprehensive diagnostic and auto-fixing capabilities.

