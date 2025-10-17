# Critical Fixes Needed - Summary

## Issues to Fix:

### 1. Users Tab 500 Error ✅
- **Problem:** `/gitlab/users` endpoint returning 500 error
- **Fix:** Added try/catch with better error logging
- **Status:** FIXED - restart server to test

### 2. Cannot Add Custom File Types ❌
- **Problem:** File types hardcoded as checkboxes
- **Solution:** Make it dynamic - allow admin to add any file extension
- **Implementation:** Add text input field with "Add Extension" button

### 3. Main Repo Should Not Be Deletable ❌
- **Problem:** Admin can delete "main" repository
- **Solution:** Add validation to prevent deleting repo with id="main"
- **Implementation:** Backend validation in DELETE endpoint

### 4. User Selection Should Be Dropdown ❌
- **Problem:** Admin types username (prone to errors)
- **Solution:** Dropdown populated from GitLab users
- **Implementation:** Replace prompt with modal containing select element

### 5. Repo Selection Should Be Dropdown ❌
- **Problem:** Admin types comma-separated repo IDs
- **Solution:** Multi-select checkboxes for repositories
- **Implementation:** Modal with checkboxes for each repo

---

## Implementation Plan:

### Fix 1: Prevent Main Repo Deletion
**File:** `backend/app/api/routers/admin_config.py`
**Add to DELETE /repositories/{repo_id}:**
```python
# Prevent deleting main repository
if repo_id == "main":
    raise HTTPException(400, "Cannot delete the main repository")
```

### Fix 2: Dynamic File Extensions
**File:** `backend/static/index.html` - Repository Modal
**Current:** Hardcoded checkboxes
**New:** Dynamic extension list with add/remove

### Fix 3: User Assignment Modal with Dropdown
**Replace prompt with proper modal:**
- Dropdown of all GitLab users
- Multi-select checkboxes for repositories
- Save button

### Fix 4: Repository Update with Dynamic Extensions
**File:** `backend/static/index.html`
**Add to repository modal:**
```html
<div>
  <label>File Extensions:</label>
  <div id="extensionsList">
    <!-- Dynamic list of extensions -->
  </div>
  <button id="addExtensionBtn">+ Add Extension</button>
</div>
```

---

## Quick Wins (Do These First):

1. ✅ Fix Users tab 500 error (DONE)
2. Prevent main repo deletion (5 min)
3. Make file extensions dynamic (15 min)
4. Create user assignment modal (20 min)

Total: ~40 minutes

Let's implement these NOW.
