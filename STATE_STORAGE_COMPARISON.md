# State Storage Comparison

## The Question: Where to Store `sent_links.json`?

This file tracks which articles have been sent to avoid duplicates.

---

## ❌ Previous Approach: Git Commits

**How it worked:**
- Workflow commits `sent_links.json` after each run
- Pushes to repository
- Next run pulls the updated file

**Problems:**
- ❌ Creates unnecessary commits (clutters git history)
- ❌ Requires write permissions (security concern)
- ❌ Can cause merge conflicts
- ❌ Not the intended use of git
- ❌ Pollutes repository with automated commits

**Verdict:** This is an anti-pattern. Don't store runtime state in git.

---

## ✅ Current Approach: GitHub Actions Cache

**How it works:**
- After workflow runs, save `sent_links.json` to GitHub Actions cache
- Next run restores from cache
- No git commits needed

**Advantages:**
- ✅ No commits to repository (clean git history)
- ✅ No write permissions needed (better security)
- ✅ No merge conflicts
- ✅ Proper separation of code vs. runtime state
- ✅ Simpler workflow

**Trade-offs:**
- ⚠️ Cache expires after 7 days of inactivity
- ⚠️ Might get duplicate articles if you don't run workflow for 7+ days

**Verdict:** Best solution for this use case. GitHub Actions cache is designed exactly for this purpose.

---

## Alternative Options (Not Implemented)

### Option 1: GitHub Variables
Store sent URLs as a repository variable.

**Pros:** Permanent storage
**Cons:**
- Limited to 48KB
- Can't auto-update (needs API calls)
- More complex

### Option 2: External Database
Use Firebase, Supabase, DynamoDB, etc.

**Pros:** Professional, unlimited storage
**Cons:**
- Requires additional setup
- Need more credentials
- Overkill for this use case

### Option 3: No Tracking
Just send random articles without tracking.

**Pros:** Simplest possible
**Cons:** Will send duplicates

---

## Recommendation

**Use GitHub Actions Cache** (current implementation)

It's the perfect balance of:
- ✅ Simplicity
- ✅ No security concerns
- ✅ Clean git history
- ✅ Designed for this exact use case

The 7-day cache expiration is a non-issue since the workflow runs daily.

---

## For Future Reference

If you ever need permanent state storage (beyond 7 days inactivity), consider:
1. **GitHub Variables API** - Good for small data
2. **Cloud Storage (S3, GCS)** - Good for larger data
3. **Database (Firebase, Supabase)** - Good for complex queries

But for this daily automation, cache is perfect! 🎉
