# Security Audit Command (security-audit)

## Overview

Perform a comprehensive security audit of the codebase. Goes far deeper than the review agent's security checklist — this is a dedicated, multi-phase analysis covering dependency vulnerabilities, code-level security patterns, secrets detection, infrastructure configuration, and compliance posture.

## Modes

| Invocation | Mode | Behavior |
|---|---|---|
| `/security-audit` | Full audit | All phases, complete report |
| `/security-audit --quick` | Quick scan | Dependencies + secrets only (~2 min) |
| `/security-audit --deps` | Dependencies only | Vulnerability scan of all dependencies |
| `/security-audit --code` | Code only | Static analysis of source code |
| `/security-audit --infra` | Infrastructure only | Config files, env vars, deployment |
| `/security-audit --diff` | Changed files only | Audit only files changed since last release/tag |

## Command Process

### Phase 0: Environment Detection

**Detect project stack and available tools:**

```bash
# Package manager & language
ls package.json Cargo.toml pyproject.toml go.mod requirements.txt 2>/dev/null

# Available security tools (use what's installed, don't require anything)
which npm npx pnpm bun 2>/dev/null          # Node dependency audit
which cargo 2>/dev/null                       # Rust audit
which pip pip-audit safety 2>/dev/null        # Python audit
which govulncheck 2>/dev/null                 # Go audit
which trivy grype snyk 2>/dev/null            # General scanners
which gitleaks trufflehog 2>/dev/null         # Secrets scanners
```

**Initialize tracking:**
```json
{
  "todos": [
    { "id": "deps", "content": "Dependency vulnerability scan", "status": "in_progress" },
    { "id": "secrets", "content": "Secrets & credential detection", "status": "pending" },
    { "id": "code", "content": "Code-level security analysis", "status": "pending" },
    { "id": "infra", "content": "Infrastructure & configuration review", "status": "pending" },
    { "id": "report", "content": "Generate audit report", "status": "pending" }
  ]
}
```

---

### Phase 1: Dependency Vulnerability Scan

**Run all available dependency auditors:**

```bash
# Node/Bun
npm audit --json 2>/dev/null || npx audit-ci 2>/dev/null
# Also check for outdated packages with known CVEs
npm outdated --json 2>/dev/null

# Python
pip-audit --format=json 2>/dev/null || \
  safety check --json 2>/dev/null || \
  python -m pip_audit 2>/dev/null

# Rust
cargo audit --json 2>/dev/null

# Go
govulncheck ./... 2>/dev/null

# General (if installed)
trivy fs --security-checks vuln . 2>/dev/null
```

**If no scanner is installed, fall back to manual analysis:**
- Read lock files (package-lock.json, bun.lock, Cargo.lock, etc.)
- Check key dependencies against known vulnerability databases via web search
- Focus on: auth libraries, crypto, HTTP clients, ORMs, file upload handlers

**Categorize findings:**
| Severity | Definition | Action |
|---|---|---|
| Critical | Known exploit available, RCE, data breach risk | Must fix immediately |
| High | Exploitable vulnerability, no known exploit yet | Fix before next release |
| Medium | Requires specific conditions to exploit | Plan fix within 30 days |
| Low | Theoretical risk, defense in depth | Track, fix when convenient |

---

### Phase 2: Secrets & Credential Detection

**Scan for hardcoded secrets:**

```bash
# If gitleaks/trufflehog available:
gitleaks detect --source . --report-format json 2>/dev/null
trufflehog filesystem . --json 2>/dev/null

# Manual pattern scan (always run):
rg -n --no-heading -i \
  '(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]\s*["\x27][^"\x27]{8,}' \
  --type-not binary \
  -g '!node_modules' -g '!.git' -g '!*.lock' -g '!dist' -g '!build' \
  . 2>/dev/null
```

**Check for common secret patterns:**

| Pattern | Regex | Risk |
|---|---|---|
| AWS keys | `AKIA[0-9A-Z]{16}` | Critical |
| Private keys | `-----BEGIN (RSA\|EC\|OPENSSH) PRIVATE KEY-----` | Critical |
| JWT secrets | `jwt[_-]?secret\s*[:=]` | High |
| Database URLs | `(postgres\|mysql\|mongodb)://[^@]+@` | High |
| API tokens | `(gh[ps]_[A-Za-z0-9]{36}\|sk-[A-Za-z0-9]{48})` | High |
| Generic passwords | `password\s*[:=]\s*["'][^"']+["']` | Medium |

**Check .gitignore coverage:**
```bash
# Ensure sensitive files are gitignored
for f in .env .env.local .env.production *.pem *.key credentials.json; do
  git check-ignore "$f" 2>/dev/null || echo "⚠️ $f is NOT gitignored"
done
```

**Check git history for leaked secrets:**
```bash
# Search recent commits for accidentally committed secrets
git log --all --diff-filter=A --name-only --pretty=format:'' -- '*.env' '*.pem' '*.key' 2>/dev/null
```

---

### Phase 3: Code-Level Security Analysis

**Systematic scan of source code for vulnerability patterns:**

#### 3.1: Injection Vulnerabilities

```bash
# SQL Injection — string concatenation in queries
rg -n 'query\s*\(`[^`]*\$\{' --type ts --type js -g '!*.test.*' -g '!*.spec.*'
rg -n "execute\s*\(\s*f['\"]" --type py  # Python f-string in SQL
rg -n '\.raw\s*\(' --type ts --type js   # ORM raw queries

# Command Injection — user input in exec/spawn
rg -n '(exec|spawn|execSync|spawnSync)\s*\(' --type ts --type js -g '!node_modules'
rg -n 'subprocess\.(run|call|Popen)\(' --type py
rg -n 'os\.system\(' --type py

# XSS — dangerouslySetInnerHTML, innerHTML, document.write
rg -n '(dangerouslySetInnerHTML|innerHTML|document\.write)' --type ts --type js --type tsx

# Path Traversal — user input in file paths
rg -n '(readFile|writeFile|createReadStream|fs\.).*req\.(params|query|body)' --type ts --type js

# Template Injection — unescaped template rendering
rg -n '(\{\{\{|\{!!|<%-)' --type html  # Handlebars/EJS unescaped
```

#### 3.2: Authentication & Authorization

```bash
# Missing auth middleware on routes
rg -n '(app|router)\.(get|post|put|patch|delete)\s*\(' --type ts --type js -g '!*.test.*'
# Cross-reference with auth middleware usage

# Session configuration issues
rg -n '(secure:\s*false|httpOnly:\s*false|sameSite.*none)' --type ts --type js

# Weak crypto
rg -n '(md5|sha1|Math\.random)\(' --type ts --type js --type py
rg -n "createHash\s*\(\s*['\"]md5['\"]" --type ts --type js
```

#### 3.3: Data Exposure

```bash
# Sensitive data in logs
rg -n 'console\.(log|info|debug|warn)\(.*\b(password|token|secret|key|credit.?card)\b' \
  --type ts --type js -i -g '!*.test.*'

# Sensitive data in error responses
rg -n '(res\.json|res\.send|Response)\s*\(.*\b(stack|sql|query)\b' --type ts --type js

# Overly permissive CORS
rg -n "origin:\s*['\"]?\*['\"]?" --type ts --type js
rg -n 'Access-Control-Allow-Origin.*\*' --type ts --type js
```

#### 3.4: Cryptographic Issues

```bash
# Weak or missing encryption
rg -n '(createCipher\b|DES|RC4|ECB)' --type ts --type js  # Deprecated/weak
rg -n 'verify\s*=\s*False' --type py  # SSL verification disabled
rg -n 'rejectUnauthorized.*false' --type ts --type js  # TLS bypass

# Hardcoded salts or IVs
rg -n '(salt|iv)\s*[:=]\s*["\x27]' --type ts --type js --type py
```

#### 3.5: Miscellaneous

```bash
# Debug mode in production configs
rg -n '(DEBUG\s*[:=]\s*[Tt]rue|debug:\s*true)' -g '!*.test.*' -g '!*.spec.*'

# TODO/FIXME security items
rg -n -i '(TODO|FIXME|HACK|XXX).*(security|auth|vuln|inject|sanitiz)' --type-not binary

# Eval usage
rg -n '\beval\s*\(' --type ts --type js --type py

# Prototype pollution patterns
rg -n '(Object\.assign|__proto__|constructor\[)' --type ts --type js
```

---

### Phase 4: Infrastructure & Configuration Review

#### 4.1: Environment & Secrets Management

```bash
# Check .env files exist and are gitignored
ls -la .env* 2>/dev/null
git check-ignore .env .env.local .env.production 2>/dev/null

# Check for .env.example (should exist for documentation)
test -f .env.example && echo "✅ .env.example exists" || echo "⚠️ No .env.example"

# Verify sensitive env vars are not in checked-in configs
rg -n '(DATABASE_URL|API_KEY|SECRET|PASSWORD|TOKEN)' \
  -g '*.json' -g '*.yaml' -g '*.yml' -g '*.toml' \
  -g '!package*.json' -g '!*.lock' \
  --no-heading
```

#### 4.2: HTTP Security Headers

```bash
# Check for security headers in server config
rg -n '(helmet|x-frame-options|x-content-type|strict-transport|content-security-policy)' \
  --type ts --type js -i

# Check for HTTPS enforcement
rg -n '(force.*https|redirect.*https|HSTS|Strict-Transport)' --type ts --type js -i

# Check rate limiting
rg -n '(rate.?limit|throttle|express-rate-limit|bottleneck)' --type ts --type js -i
```

#### 4.3: Docker & Deployment

```bash
# Dockerfile security
if [ -f Dockerfile ] || [ -f docker-compose.yml ]; then
  # Running as root?
  rg -n '^USER' Dockerfile 2>/dev/null || echo "⚠️ Dockerfile doesn't set USER (runs as root)"
  
  # Sensitive data in build args
  rg -n '(ARG|ENV).*(SECRET|PASSWORD|TOKEN|KEY)' Dockerfile 2>/dev/null
  
  # Latest tag usage
  rg -n 'FROM.*:latest' Dockerfile 2>/dev/null
  
  # .dockerignore exists?
  test -f .dockerignore && echo "✅ .dockerignore exists" || echo "⚠️ No .dockerignore"
fi
```

#### 4.4: CI/CD Security

```bash
# Check GitHub Actions for security issues
if [ -d .github/workflows ]; then
  # Secrets in plaintext
  rg -n '(password|token|secret|key)\s*:' .github/workflows/ -i
  
  # pull_request_target (dangerous)
  rg -n 'pull_request_target' .github/workflows/
  
  # Unpinned actions
  rg -n 'uses:.*@(main|master|latest)' .github/workflows/
fi
```

---

### Phase 5: Audit Report Generation

**Generate comprehensive report at `.writ/security/audit-YYYY-MM-DD.md`:**

```markdown
# Security Audit Report

> **Date:** YYYY-MM-DD
> **Project:** [project name]
> **Auditor:** Writ /security-audit
> **Scope:** [Full / Quick / Deps / Code / Infra / Diff]

## Executive Summary

**Overall Risk Level:** [🟢 Low / 🟡 Medium / 🟠 High / 🔴 Critical]

| Category | Findings | Critical | High | Medium | Low |
|----------|----------|----------|------|--------|-----|
| Dependencies | X | 0 | 1 | 2 | 3 |
| Secrets | X | 0 | 0 | 1 | 0 |
| Code | X | 0 | 2 | 3 | 5 |
| Infrastructure | X | 0 | 0 | 2 | 1 |
| **Total** | **X** | **0** | **3** | **8** | **9** |

## Critical & High Findings (Action Required)

### [FINDING-001] SQL Injection in Search Endpoint
- **Severity:** Critical
- **Category:** Code — Injection
- **Location:** `src/routes/search.ts:34`
- **Description:** User input concatenated directly into SQL query string
- **Impact:** Attacker can read/modify/delete database contents
- **Remediation:** Use parameterized queries
- **Example Fix:**
  ```typescript
  // Before (vulnerable)
  db.query(`SELECT * FROM items WHERE name LIKE '%${query}%'`)
  
  // After (safe)
  db.query('SELECT * FROM items WHERE name LIKE $1', [`%${query}%`])
  ```

### [FINDING-002] ...

## Medium & Low Findings

### [FINDING-010] Outdated dependency: lodash@4.17.20
- **Severity:** Medium
- **Category:** Dependencies
- **CVE:** CVE-2021-23337 (prototype pollution)
- **Remediation:** `npm update lodash`

### [FINDING-011] ...

## Dependency Summary

### Vulnerable Dependencies
| Package | Current | Patched | Severity | CVE |
|---------|---------|---------|----------|-----|
| lodash | 4.17.20 | 4.17.21 | Medium | CVE-2021-23337 |

### Outdated Dependencies (Security-Relevant)
| Package | Current | Latest | Risk |
|---------|---------|--------|------|
| express | 4.18.2 | 4.21.0 | Low (no known vulns) |

## Secrets Scan Results

- **Hardcoded secrets found:** X
- **Gitignore coverage:** [Complete / Gaps found]
- **Git history leaks:** [None / X files found]

## Security Posture Checklist

### Authentication & Authorization
- [ ] Auth middleware on all protected routes
- [ ] Session cookies: httpOnly, secure, sameSite
- [ ] Password hashing with bcrypt/argon2 (not MD5/SHA1)
- [ ] Rate limiting on auth endpoints
- [ ] CSRF protection enabled

### Input Validation
- [ ] All user inputs validated (zod/joi/yup or equivalent)
- [ ] File uploads restricted (type, size)
- [ ] SQL queries parameterized
- [ ] No eval() or equivalent on user input

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced (HSTS)
- [ ] Secrets in environment variables (not code)
- [ ] Logs don't contain sensitive data
- [ ] Error messages don't leak internals

### Infrastructure
- [ ] Security headers configured (helmet or equivalent)
- [ ] CORS properly restricted
- [ ] Docker runs as non-root user
- [ ] CI/CD actions pinned to SHA
- [ ] .env files gitignored

## Recommendations

### Immediate (This Sprint)
1. [Fix critical/high findings]

### Short-Term (Next 30 Days)
1. [Fix medium findings]
2. [Add missing security controls]

### Long-Term (Roadmap)
1. [Security improvements to consider]
2. [Monitoring and alerting setup]

---

*Generated by Writ /security-audit on YYYY-MM-DD*
*Re-run periodically or before each release.*
```

**Present summary to user:**

```
🔒 Security Audit Complete

Overall Risk: 🟡 Medium

┌──────────────┬──────────┬──────┬──────┬────────┬─────┐
│ Category     │ Findings │ Crit │ High │ Medium │ Low │
├──────────────┼──────────┼──────┼──────┼────────┼─────┤
│ Dependencies │ 6        │ 0    │ 1    │ 2      │ 3   │
│ Secrets      │ 1        │ 0    │ 0    │ 1      │ 0   │
│ Code         │ 10       │ 0    │ 2    │ 3      │ 5   │
│ Infra        │ 3        │ 0    │ 0    │ 2      │ 1   │
├──────────────┼──────────┼──────┼──────┼────────┼─────┤
│ Total        │ 20       │ 0    │ 3    │ 8      │ 9   │
└──────────────┴──────────┴──────┴──────┴────────┴─────┘

Full report: .writ/security/audit-2026-02-22.md

3 High-severity issues require attention before next release.
```

```
AskQuestion({
  title: "Security Audit Actions",
  questions: [
    {
      id: "action",
      prompt: "What would you like to do?",
      options: [
        { id: "fix_critical", label: "Auto-fix critical & high findings" },
        { id: "fix_deps", label: "Auto-fix dependency vulnerabilities only" },
        { id: "create_issues", label: "Create issues for all findings" },
        { id: "create_adr", label: "Create ADR for security decisions" },
        { id: "done", label: "Review report later" }
      ]
    }
  ]
})
```

---

## Auto-Fix Capabilities

When the user selects "Auto-fix", the command can automatically resolve:

| Finding Type | Auto-Fix | Method |
|---|---|---|
| Outdated dependency (patch) | ✅ | `npm update`, `cargo update` |
| Outdated dependency (major) | ❌ | May have breaking changes — create issue |
| Missing .gitignore entry | ✅ | Append to .gitignore |
| Missing security headers | ✅ | Add helmet/equivalent middleware |
| SQL string concatenation | ⚠️ | Suggest fix, require confirmation |
| Hardcoded secret | ⚠️ | Move to .env, require confirmation |
| Missing rate limiting | ❌ | Architecture decision — create ADR |
| Debug mode enabled | ✅ | Set to false in production configs |

Auto-fixes use the coding agent for non-trivial changes:
```
Task({
  subagent_type: "generalPurpose",
  description: "Fix security findings",
  prompt: "Fix the following security issues: [findings]. 
           Run tests after each fix to ensure nothing breaks.
           Commit each fix separately with 'security: ' prefix."
})
```

---

## Scheduling

**Recommended cadence:**
- `/security-audit --quick` — before every release (via `/release` pre-check)
- `/security-audit` — monthly, or after major dependency updates
- `/security-audit --diff` — during code review of large PRs

**Cron integration (OpenClaw):**
```bash
openclaw cron add \
  --name "weekly-security-audit" \
  --cron "0 9 * * 1" \
  --tz UTC \
  --session isolated \
  --message "/security-audit --quick for the project at ~/project. Report findings only if Critical or High issues found. Otherwise reply HEARTBEAT_OK." \
  --timeout-seconds 120
```

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/implement-story` | Review agent runs lightweight security checks per story |
| `/release` | Consider running `--quick` audit before releasing |
| `/create-adr` | Security decisions should be documented as ADRs |
| `/create-issue` | Findings can be captured as issues for tracking |
