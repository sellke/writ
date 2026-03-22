# Prisma Migration Command (prisma-migration)

## Overview

A comprehensive Prisma schema migration command that manages database schema changes through proper migration workflow from development to production. This command auto-detects your current database setup, offers dev/prod separation, generates migrations interactively, and deploys to production with comprehensive safety validation.

## Command Process

### Step 1: Initialize Migration Tracking

**Create progress tracking using `todo_write`:**

```json
{
  "todos": [
    {
      "id": "detect-setup",
      "content": "Detect current database setup (single vs dev/prod)",
      "status": "in_progress"
    },
    {
      "id": "setup-validation",
      "content": "Validate or set up dev/prod database separation",
      "status": "pending"
    },
    {
      "id": "safety-checks",
      "content": "Run pre-migration safety checks",
      "status": "pending"
    },
    {
      "id": "create-migration",
      "content": "Create and apply migration interactively",
      "status": "pending"
    },
    {
      "id": "deploy-production",
      "content": "Deploy migration to production (optional)",
      "status": "pending"
    }
  ]
}
```

### Step 2: Database Setup Detection

**Update progress:** Mark "detect-setup" as `[in_progress]`

**Scan current database configuration:**

```bash
# Check if migrations directory exists
test -d prisma/migrations && echo "Migrations enabled" || echo "Using db push"

# Check DATABASE_URL configuration
grep -E "^DATABASE_URL=" .env

# Analyze migration history
pnpm prisma migrate status
```

**Detection logic:**

1. **Migrations directory exists** → Already using proper migration workflow
2. **No migrations directory** → Currently using `prisma db push`
3. **Check for multiple DATABASE_URLs** → Dev/prod separation exists
4. **Single DATABASE_URL** → Single database setup

**Output detection results:**

```
🔍 Database Setup Analysis
==========================

Current Setup:
  - Strategy: [prisma db push / prisma migrate]
  - Databases: [Single / Dev+Prod]
  - Migration Files: [X migrations found / None]
  - Last Migration: [migration name or N/A]

DATABASE_URL: postgres://...neon.tech/neondb
  └─ Detected: Single shared database (dev & prod)
```

### Step 3: Setup Validation and Dev/Prod Separation Offer

**Update progress:** Mark "detect-setup" as `[completed]` and "setup-validation" as `[in_progress]`

**If single database detected, offer dev/prod separation:**

```
⚠️  Single Database Detected

You're currently using the same Neon database for both development and production.
This means schema experiments can affect production data.

Recommendation: Set up separate dev and prod databases for safer development.

Would you like to set up dev/prod database separation? [y/N]: _
```

**If user chooses "yes" - Guide through setup:**

```
🔧 Setting Up Dev/Prod Database Separation

Step 1: Create Development Database in Neon
  → Go to: https://console.neon.tech
  → Click "New Database" 
  → Name it: neondb-dev
  → Copy connection string

Step 2: Update Local Environment
  → Current DATABASE_URL is for production
  → Create new DATABASE_URL for development
  
  Press Enter when you have the dev database URL ready...
  
  Paste development DATABASE_URL: _
  
Step 3: Initialize Development Database
  Running: prisma db push
  ✅ Development database schema synced

Step 4: Create Initial Migration
  This captures your current schema as the baseline migration.
  
  Migration name: initial_schema
  Running: prisma migrate dev --name initial_schema
  ✅ Initial migration created

Setup Complete! 🎉
  - Development: [your-dev-url]
  - Production: [stored in Vercel]
  
Next: Update .env with dev URL, add prod URL to Vercel only.
```

**If user chooses "no" - Continue with single database:**

```
⚠️  Continuing with single database setup

Safety reminder:
  - Schema changes affect production immediately
  - Test thoroughly before applying changes
  - Consider backups before major migrations

Proceeding with migration workflow...
```

### Step 4: Pre-Migration Safety Checks

**Update progress:** Mark "setup-validation" as `[completed]` and "safety-checks" as `[in_progress]`

**Run comprehensive safety validation:**

#### Check 1: Uncommitted Schema Changes
```bash
# Check if schema.prisma has uncommitted changes
git diff --name-only | grep "prisma/schema.prisma"

# Status
if changes_detected:
  ⚠️  Warning: prisma/schema.prisma has uncommitted changes
  → Recommendation: Commit schema before creating migration
  → Continue anyway? [y/N]
else:
  ✅ No uncommitted schema changes
```

#### Check 2: Migration State
```bash
# Check if migrations are in sync
pnpm prisma migrate status

# Interpret results
if "Database schema is up to date":
  ✅ Database matches migration history
elif "Pending migrations detected":
  ⚠️  Warning: Pending migrations not applied
  → Migrations pending: [list]
  → Apply pending migrations first? [Y/n]
elif "Drift detected":
  ⚠️  Schema drift detected
  → Database schema differs from migration files
  → Reset to migration baseline? [y/N]
```

#### Check 3: Prisma Client Sync
```bash
# Check if Prisma client is up to date
test -d node_modules/.prisma/client || echo "Client not generated"

# Verify generation timestamp
stat node_modules/.prisma/client

# Status
if client_outdated:
  🔄 Regenerating Prisma client...
  pnpm prisma generate
  ✅ Prisma client updated
else:
  ✅ Prisma client is current
```

#### Check 4: Git Status
```bash
# Ensure working directory is clean for migration tracking
git status --porcelain

# Status
if untracked_migration_files:
  ⚠️  Warning: Migration files not committed
  → Stage and commit migration files after creation
else:
  ✅ Working directory clean
```

**Safety Check Summary:**

```
✅ Safety Checks Passed
  ✅ No uncommitted schema changes
  ✅ Database matches migration history  
  ✅ Prisma client is current
  ✅ Ready for migration

Proceeding to migration creation...
```

### Step 5: Interactive Migration Creation

**Update progress:** Mark "safety-checks" as `[completed]` and "create-migration" as `[in_progress]`

**Interactive conversation to understand changes:**

```
📝 Migration Creation Workflow

What schema changes are you making?
Examples:
  - "Adding location field to Event model"
  - "Making email field unique on Participant"
  - "Creating new Settings model"

Describe your changes: _

[User provides description]

Analyzing schema changes...

📊 Detected Changes:
  - Model: Event
    └─ Added field: location (String, optional)
  
Migration Impact:
  - New column added to events table
  - Non-breaking change (nullable field)
  - No data migration required

Suggested migration name: add_event_location_field

Use this name? [Y/n]: _

[If no, prompt: "Enter custom name: _"]

Creating migration...
```

**Execute migration creation:**

```bash
# Create and apply migration
pnpm prisma migrate dev --name add_event_location_field

# Output shown to user
Environment variables loaded from .env
Prisma schema loaded from prisma/schema.prisma
Datasource "db": PostgreSQL database "neondb-dev"

Applying migration `20241003120000_add_event_location_field`

The following migration(s) have been created and applied from new schema changes:

migrations/
  └─ 20241003120000_add_event_location_field/
    └─ migration.sql

✔ Generated Prisma Client (v6.15.0)

✅ Migration created and applied successfully!
```

**Show migration SQL:**

```
📄 Migration SQL (prisma/migrations/20241003120000_add_event_location_field/migration.sql):

-- AlterTable
ALTER TABLE "events" ADD COLUMN "location" TEXT;

Review migration? [Y/n]: _
```

### Step 6: Local Validation

**Test changes in local environment:**

```
🧪 Testing Migration Changes

Starting development server...
pnpm dev

Testing API endpoints:
  → GET /api/health
    ✅ Database: healthy
    ✅ Tables exist: true
    
  → GET /api/events
    ✅ Query successful
    ✅ New field accessible: location

Migration validated locally! ✅

Stop dev server and continue? [Y/n]: _
```

### Step 7: Production Deployment Offer

**Update progress:** Mark "create-migration" as `[completed]` and "deploy-production" as `[in_progress]`

**Present deployment options:**

```
🚀 Production Deployment

Your migration is ready for production deployment.

Migration Details:
  - Name: add_event_location_field
  - Changes: Added location field to events table
  - Risk Level: Low (non-breaking change)
  - Rollback: Available

Production Database:
  - Location: Vercel Environment Variables
  - DATABASE_URL: postgres://...neon.tech/neondb

Options:
  1. Deploy now (recommended for non-breaking changes)
  2. Deploy later (provide deployment instructions)
  3. Create deployment checklist

Choose option [1/2/3]: _
```

**Option 1: Deploy Now**

```
Deploying migration to production...

⚠️  PRODUCTION DEPLOYMENT CONFIRMATION

This will modify your production database schema.
  
Migration: add_event_location_field
Action: ALTER TABLE "events" ADD COLUMN "location" TEXT
Impact: Non-breaking (adds optional field)

Current production data:
  - Events: 2
  - Participants: 4
  - Expenses: 2

✅ Backup available via Neon (automatic)

Type 'DEPLOY' to confirm: _

[User types DEPLOY]

Deploying...
pnpm prisma migrate deploy

Environment variables loaded from .env
Prisma schema loaded from prisma/schema.prisma
Datasource "db": PostgreSQL database "neondb"

1 migration found in prisma/migrations

Applying migration `20241003120000_add_event_location_field`

The following migration has been applied:

migrations/
  └─ 20241003120000_add_event_location_field/
    └─ migration.sql
      
✅ Migration deployed successfully!

Verifying production deployment...
curl https://your-app.vercel.app/api/health

{
  "status": "healthy",
  "database": {
    "connected": true,
    "tablesExist": true,
    "eventCount": 2
  }
}

✅ Production database healthy!

Deployment Complete! 🎉
```

**Option 2: Deploy Later**

```
📋 Deployment Instructions

To deploy this migration to production later:

1. Ensure migration is committed:
   git add prisma/migrations/
   git add prisma/schema.prisma
   git commit -m "Add location field to events"
   git push origin main

2. Deploy to Vercel:
   - Automatic via git push (Vercel will build)
   - Or: vercel --prod

3. Apply migration to production database:
   
   # Set production DATABASE_URL
   export DATABASE_URL="your-production-url"
   
   # Deploy migration
   pnpm prisma migrate deploy

4. Verify deployment:
   curl https://your-app.vercel.app/api/health

Migration ready for deployment when you are! ✅
```

**Option 3: Create Deployment Checklist**

```
Creating deployment checklist...

📄 Deployment checklist created:
  → .writ/docs/migrations/20241003_add_event_location_deployment.md

Contains:
  - Pre-deployment verification
  - Step-by-step deployment process
  - Rollback procedures
  - Post-deployment validation
  - Troubleshooting guide

Review checklist before deploying to production.
```

### Step 8: Post-Migration Summary

**Update progress:** Mark "deploy-production" as `[completed]`

**Present comprehensive summary:**

```
✅ Migration Workflow Complete!

📊 Summary:
  - Migration: add_event_location_field
  - Status: ✅ Created and tested locally
  - Production: ✅ Deployed successfully
  - Files created: 1 migration file

📁 Files Modified:
  - prisma/schema.prisma (updated)
  - prisma/migrations/20241003120000_add_event_location_field/migration.sql (created)
  - node_modules/.prisma/client (regenerated)

🔄 Next Steps:
  1. Commit migration files: git add prisma/
  2. Push to repository: git push origin main
  3. Update application code to use new field
  4. Deploy application changes to Vercel

📚 Migration History:
  - Total migrations: 2
  - Last migration: add_event_location_field (just now)
  - Previous: initial_schema (baseline)

🎯 Development Tips:
  - Always test migrations locally first
  - Review generated SQL before production deployment
  - Use descriptive migration names
  - Commit migrations immediately after creation

Run /prisma-migration again for your next schema change! 🚀
```

## Core Rules

1. **Safety First** - Always run comprehensive safety checks before creating migrations
2. **Interactive Guidance** - Use conversational flow to understand schema changes and suggest migration names
3. **Auto-Detection** - Intelligently detect single vs dev/prod database setup
4. **Optional Separation** - Offer but don't force dev/prod database separation
5. **Deployment Flexibility** - Provide multiple deployment options (now, later, checklist)
6. **Validation Required** - Test migrations locally before production deployment
7. **Clear Communication** - Show SQL changes, explain impact, provide rollback information
8. **Progress Tracking** - Use `todo_write` to track multi-phase workflow

## Tool Integration

**Primary Writ tools:**

- `todo_write` - Track migration workflow progress across all phases
- `run_terminal_cmd` - Execute Prisma CLI commands (migrate, generate, status)
- `read_file` - Inspect schema.prisma, migration files, and .env configuration
- `codebase_search` - Analyze current database setup and migration patterns
- `write` - Create deployment checklists and documentation
- `grep` - Search for DATABASE_URL and migration-related configuration

**Parallel execution opportunities:**

- Safety checks (git status, migration status, client verification)
- Local validation (health check, API endpoint tests)
- Production verification (multiple endpoint health checks)

## Error Handling & Recovery

**Common failure scenarios:**

### Migration Creation Fails
```
❌ Migration creation failed

Error: P3006
The migration failed to apply cleanly to the database.

Possible causes:
  - Database schema drift (manual changes made)
  - Conflicting constraints
  - Data incompatibility

Solutions:
  1. Check migration status: pnpm prisma migrate status
  2. Resolve drift: pnpm prisma migrate resolve
  3. Reset and retry: pnpm prisma migrate reset (⚠️  data loss)

Need help? Run /test-database to diagnose issues.
```

### Deployment Fails in Production
```
❌ Production deployment failed

Error: Migration cannot be applied to production database

Possible causes:
  - DATABASE_URL not set correctly
  - Network connectivity issues
  - Database permissions
  - Schema conflicts

Recovery steps:
  1. Verify DATABASE_URL: echo $DATABASE_URL
  2. Check database access: pnpm prisma db pull
  3. Review error logs
  4. Rollback if needed: prisma migrate resolve --rolled-back

Migration can be retried after resolving issues.
```

### Schema Drift Detected
```
⚠️  Schema Drift Detected

Your database schema differs from migration files.
This usually happens when:
  - Manual database changes were made
  - prisma db push was used alongside migrations
  - Migrations were not applied

Current state:
  - Migrations recorded: 2
  - Database matches: ❌ No (drift detected)

Options:
  1. Generate migration from current state (captures drift)
  2. Reset to last migration (⚠️  loses manual changes)
  3. Manually resolve differences

Choose option [1/2/3]: _
```

### Uncommitted Changes Warning
```
⚠️  Uncommitted Schema Changes

prisma/schema.prisma has uncommitted changes.

Recommendation: Commit schema before migration to track changes properly.

Options:
  1. Commit changes now
  2. Continue without committing (not recommended)
  3. Cancel and commit manually

Choose option [1/2/3]: _
```

## Integration Notes

This command integrates with the existing Writ ecosystem:

1. **Complements test-database** - While `/test-database` diagnoses connection issues, `/prisma-migration` manages schema evolution
2. **Uses standard tools** - Follows same `run_terminal_cmd` and `todo_write` patterns
3. **Works with existing setup** - Integrates with current Neon + Vercel deployment
4. **Respects state.json** - Uses platform-specific commands based on user's environment
5. **Documentation location** - Stores deployment checklists in `.writ/docs/migrations/`

## Best Practices

### When to Use This Command
- ✅ Adding new models or fields to schema
- ✅ Modifying existing field constraints
- ✅ Creating new relationships between models
- ✅ Renaming fields or tables
- ✅ Any production schema change

### When NOT to Use
- ❌ Quick experimental changes (use `prisma db push` manually)
- ❌ Prototyping with throwaway data
- ❌ Schema changes that will be reverted immediately

### Migration Naming Conventions
- ✅ Use descriptive, action-oriented names
- ✅ Include model name: `add_event_location`
- ✅ Use underscores, not hyphens: `modify_user_email`
- ✅ Be specific: `make_email_unique_on_user` not `update_user`

### Deployment Timing
- ✅ Deploy non-breaking changes immediately
- ✅ Schedule breaking changes during low-traffic periods
- ✅ Test migrations on copy of production data first
- ✅ Have rollback plan ready for major changes

## Future Enhancements

Potential improvements (not in initial version):

- **Migration rollback command** - Automated rollback with data preservation
- **Schema diff visualization** - Visual comparison of before/after states
- **Migration testing** - Automated test generation for schema changes
- **Multi-database support** - Handle MySQL, SQLite, and other databases
- **Team coordination** - Detect and merge migration conflicts
- **Backup integration** - Automatic backups before major migrations

But for now: Focus on core workflow - safe, guided migration creation and deployment with comprehensive validation and flexible deployment options.

