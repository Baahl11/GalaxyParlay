# 🚨 SECURITY INCIDENT REPORT

**Date:** February 5, 2026  
**Severity:** CRITICAL  
**Status:** MITIGATED

## Incident Description

GitGuardian detected an exposed Supabase service role JWT token in a git push.

## Affected Files

The following files contained hardcoded credentials:

1. `apps/worker/check_upcoming_fixtures.py`
2. `apps/worker/generate_upcoming_predictions.py`
3. `apps/worker/run_predictions_job.py`
4. `apps/worker/generate_all_predictions.py`
5. `apps/worker/run_validation_backtest.ps1`
6. `apps/worker/.env.vercel` (contains Vercel OIDC token - also needs rotation)

## Exposed Token

**Supabase Service Role JWT:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impzc2p3anN1cW1remlkaWdqcHdqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTQzNDQwMiwiZXhwIjoyMDg1MDEwNDAyfQ.iir_GtLYUZmAL66C_7BZJITxkq8rRQklWPqBS_Qp7io
```

**Decoded Info:**
- **Project:** jssjwjsuqmkzidigipwj.supabase.co
- **Role:** service_role (full admin access)
- **Issued:** 2026-01-26 (iat: 1769434402)
- **Expires:** 2036-01-24 (exp: 2085010402)

## Immediate Actions Taken

1. ✅ Removed hardcoded tokens from all Python scripts
2. ✅ Removed hardcoded tokens from PowerShell scripts
3. ✅ Updated scripts to require environment variables
4. ✅ Committed and preparing to push cleanup

## CRITICAL: Actions Required IMMEDIATELY

### 1. Rotate Supabase Service Role Key

**Go to Supabase Dashboard NOW:**

1. Visit: https://supabase.com/dashboard/project/jssjwjsuqmkzidigipwj/settings/api
2. Navigate to **Settings** → **API** → **Service role key**
3. Click **"Generate new service key"** or **"Roll key"**
4. Copy the new key
5. Update it in:
   - Railway environment variables: `SUPABASE_SERVICE_ROLE_KEY`
   - Vercel environment variables: `SUPABASE_SERVICE_ROLE_KEY`
   - Local `.env` file (DO NOT COMMIT)

### 2. Check for Unauthorized Access

**Review Supabase logs for suspicious activity:**

1. Go to: https://supabase.com/dashboard/project/jssjwjsuqmkzidigipwj/logs/explorer
2. Check for unusual queries or access patterns since January 26, 2026
3. Look for:
   - Unexpected data modifications
   - Unusual table access patterns
   - Foreign IP addresses
   - High volume requests

### 3. Rotate Vercel OIDC Token

The file `apps/worker/.env.vercel` also contains an exposed token. Delete or rotate it.

### 4. Update Deployment Environments

**Railway:**
```bash
cd apps/worker
npx railway variables set SUPABASE_SERVICE_ROLE_KEY="<NEW_TOKEN>"
```

**Vercel:**
```bash
cd apps/web
npx vercel env add SUPABASE_SERVICE_ROLE_KEY production
# Paste new token when prompted
```

### 5. Clean Git History (Optional but Recommended)

The token is now in git history. Consider using BFG Repo-Cleaner:

```bash
# Backup first!
git clone --mirror https://github.com/Baahl11/GalaxyParlay.git

# Install BFG
# https://rtyley.github.io/bfg-repo-cleaner/

# Remove sensitive data
bfg --replace-text secrets.txt GalaxyParlay.git

# Force push (WARNING: This rewrites history)
cd GalaxyParlay.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

## Prevention Measures

1. ✅ All scripts now require environment variables
2. ✅ `.env` files are in `.gitignore`
3. ✅ Created `.env.example` with placeholder values
4. 📋 **TODO:** Set up pre-commit hooks to scan for secrets
5. 📋 **TODO:** Enable GitHub secret scanning
6. 📋 **TODO:** Add GitGuardian pre-commit hook

## Lessons Learned

- Never use fallback values with real credentials in `os.getenv()`
- Always use environment variables for secrets
- Test scripts should use mock data, not production credentials
- Review code before committing for hardcoded secrets

## References

- GitGuardian Alert: [Check your email]
- Supabase Security: https://supabase.com/docs/guides/platform/going-into-prod#security
- GitHub Secret Scanning: https://docs.github.com/en/code-security/secret-scanning

---

**NEXT STEPS:**
1. ⚠️ **ROTATE THE TOKEN NOW** - Old token is compromised
2. Check Supabase logs for unauthorized access
3. Update all deployment environments
4. Consider cleaning git history
5. Set up automated secret scanning
