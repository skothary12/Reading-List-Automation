# GitHub Actions Setup Guide

This guide helps you fix common GitHub Actions errors.

## Error 1: "Permission denied" (403)

**Solution:** Enable write permissions for GitHub Actions.

## Solution: Enable Workflow Permissions

### Step 1: Go to Repository Settings

1. Go to your repository: https://github.com/skothary12/Reading-List-Automation
2. Click **Settings** (top menu)
3. In the left sidebar, click **Actions** → **General**

### Step 2: Configure Workflow Permissions

Scroll down to **"Workflow permissions"** section and:

1. Select **"Read and write permissions"** (instead of "Read repository contents and packages permissions")
2. ✅ Check the box for **"Allow GitHub Actions to create and approve pull requests"** (optional but recommended)
3. Click **Save**

### Step 3: Re-run the Failed Workflow

1. Go to the **Actions** tab
2. Click on the failed workflow run
3. Click **"Re-run all jobs"**

---

## Alternative: Remove Push Step (Simpler)

If you don't want to grant write permissions, I can modify the workflow to **not track sent articles**. This means:
- ✅ Simpler setup (no permissions needed)
- ✅ Works immediately
- ❌ May send duplicate articles randomly

Would you like me to implement this alternative?

---

## Verification

After enabling permissions, the workflow should:
1. ✅ Run the daily reading script
2. ✅ Send you an email
3. ✅ Commit updated `sent_links.json`
4. ✅ Push to repository (no more 403 error)

---

## Error 2: "Updates were rejected" (fetch first)

**Error message:**
```
! [rejected]        HEAD -> main (fetch first)
error: failed to push some refs
hint: Updates were rejected because the remote contains work that you do not have locally
```

**Solution:** This is a merge conflict. The workflow has been updated to automatically handle this by:
1. Fetching latest changes from remote
2. Rebasing your changes on top
3. Pushing successfully

✅ **This is already fixed in the latest workflow** - just re-run the failed job.

---

## Still Getting Errors?

If you're still getting errors after enabling permissions:

1. Make sure the latest workflow file was pushed (check the Actions tab to see which version is running)
2. Try creating a **new** manual workflow run (not re-running an old one)
3. Check that your default branch is `main` (Settings → General → Default branch)
4. Ensure you've added all 7 required secrets (see main README.md)
