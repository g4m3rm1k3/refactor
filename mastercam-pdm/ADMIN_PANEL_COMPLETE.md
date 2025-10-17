# Complete Admin Panel - All Features Restored & Enhanced! ✅

## Overview

The admin panel has been completely rewritten to combine:
1. **Original Admin Features** (User Management, Repository Maintenance)
2. **New Configuration System** (Patterns, Repositories, Access Control)
3. **Future-Ready Architecture** (Extensible and customizable)

---

## How to Access

1. **Login as an admin user**
2. Click the **Settings** button (gear icon) in the top right
3. You'll see two admin tabs appear:
   - **Admin** tab - Configuration management (Patterns, Repos, Access, Maintenance)
   - **Users** tab - User account management

---

## Admin Tab - 4 Sub-Sections

### 1. Patterns Tab 🎨

**Purpose:** Define regex patterns for filename validation

**Features:**
- ✅ Add/Edit/Delete filename patterns
- ✅ Define separate patterns for links vs regular files
- ✅ Set maximum filename length
- ✅ Provide valid/invalid examples
- ✅ Cannot delete last pattern
- ✅ Cannot delete pattern in use by repositories

**Fields:**
- Pattern Name (unique identifier)
- Description (human-readable)
- Link Pattern (regex for link files)
- File Pattern (regex for regular files)
- Max Stem Length (character limit)
- Valid Examples (comma-separated)
- Invalid Examples (comma-separated)

**Example Pattern:**
```
Name: Extended Pattern 2025
Description: 7 digits + 2 letters + unlimited numbers
Link Pattern: ^\d{7}_[A-Z]{2}\d+$
File Pattern: ^\d{7}_[A-Z]{2}\d+$
Max Length: 20
Valid Examples: 1234567_AB123, 1234567_XY999
Invalid Examples: 123456, 1234567_ABC
```

### 2. Repositories Tab 💾

**Purpose:** Configure multiple repositories with different settings

**Features:**
- ✅ Add/Edit/Delete repositories
- ✅ Set GitLab URL and Project ID per repository
- ✅ Assign different file types per repository
- ✅ Assign different filename patterns per repository
- ✅ Set branch per repository
- ✅ Cannot delete last repository
- ✅ Cannot delete if users have it as default

**Fields:**
- Repository ID (unique, lowercase, no spaces)
- Display Name (user-facing name)
- GitLab URL (full URL to GitLab instance)
- Project ID (GitLab project ID)
- Branch (git branch, default: main)
- Allowed File Types (checkboxes: .mcam, .vnc, .emcam, .link)
- Filename Pattern (dropdown of available patterns)
- Description (optional)

**Example Repository:**
```
ID: legacy
Name: Legacy Projects
GitLab URL: https://gitlab.company.com/group/legacy
Project ID: 12345678
Branch: main
File Types: .mcam, .vnc, .link
Pattern: Standard Pattern
Description: Pre-2020 projects with legacy naming
```

### 3. Access Tab 🔐

**Purpose:** Control which users can access which repositories

**Features:**
- ✅ Add/Edit/Delete user access rules
- ✅ Assign multiple repositories per user
- ✅ Set default repository per user
- ✅ No entry = access to all repositories

**Fields:**
- Username (from existing users)
- Accessible Repositories (checkboxes)
- Default Repository (dropdown)

**Example Access Rule:**
```
Username: john_doe
Accessible Repositories: main, projects2025
Default Repository: main
```

**Behavior:**
- Users **without** an access rule: Can access ALL repositories
- Users **with** an access rule: Can ONLY access specified repositories
- Default repository: Opens automatically on login

### 4. Maintenance Tab 🔧

**Purpose:** Repository maintenance and dangerous operations

**Sections:**

#### **Maintenance Tools**
- **Create Manual Backup**
  - Creates timestamped backup in `~/MastercamBackups/`
  - Copies entire repository
  - Endpoint: `POST /admin/create_backup`

- **Cleanup Old Files**
  - Runs `git lfs prune` to remove unreferenced LFS objects
  - Frees disk space
  - Endpoint: `POST /admin/cleanup_lfs`

- **Export Repository as Zip**
  - Downloads entire repository (excluding `.git`)
  - Creates timestamped ZIP file
  - Endpoint: `POST /admin/export_repository`

- **Reload Config from GitLab**
  - Reloads `.pdm-config.json` from GitLab
  - Syncs configuration changes
  - Useful if another admin made changes

#### **Configuration Info**
- Config Version (e.g., 1.0.0)
- Last Updated By (username)
- Last Updated (timestamp)
- Polling Interval (seconds)

#### **Danger Zone** ⚠️
- **Reset Repository to GitLab**
  - **DESTRUCTIVE:** Deletes local repository
  - Clones fresh copy from GitLab
  - Requires typing "RESET" to confirm
  - Reloads page after completion
  - Endpoint: `POST /admin/reset_repository`

---

## Users Tab - User Account Management

**Purpose:** Manage user accounts and passwords

**Features:**
- ✅ Create new users
- ✅ Reset user passwords
- ✅ Delete users
- ✅ View all users with creation dates
- ✅ Admin users shown with badge
- ✅ Cannot delete your own account

### Create User

**Fields:**
- Username (unique)
- Password (minimum 8 characters)
- Grant admin privileges (checkbox)

**Endpoint:** `POST /admin/users/create`

### Reset Password

- Click "Reset Password" button on any user
- Enter new password (minimum 8 characters)
- Password updated immediately

**Endpoint:** `POST /admin/users/{username}/reset-password`

### Delete User

- Click trash icon on any non-admin user
- Confirms before deletion
- Cannot delete yourself
- Cannot delete other admin users

**Endpoint:** `DELETE /admin/users/{username}`

---

## Complete API Reference

### Admin Configuration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/config` | GET | Get complete configuration |
| `/admin/config/patterns` | POST | Add filename pattern |
| `/admin/config/patterns/{name}` | DELETE | Delete pattern |
| `/admin/config/repositories` | POST | Add repository |
| `/admin/config/repositories/{id}` | DELETE | Delete repository |
| `/admin/config/user-access` | POST | Add/update user access |
| `/admin/config/user-access/{username}` | DELETE | Delete user access |
| `/admin/config/my-repositories` | GET | Get user's accessible repos |

### User Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/users` | GET | List all users |
| `/admin/users/create` | POST | Create new user |
| `/admin/users/{username}/reset-password` | POST | Reset password |
| `/admin/users/{username}` | DELETE | Delete user |

### Maintenance Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/create_backup` | POST | Create repository backup |
| `/admin/cleanup_lfs` | POST | Clean up old LFS files |
| `/admin/export_repository` | POST | Export as ZIP |
| `/admin/reset_repository` | POST | Reset to GitLab |

### File Override Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/files/{filename}/override` | POST | Force unlock file |
| `/admin/files/{filename}/delete` | DELETE | Permanently delete file |

---

## Files Modified

| File | Purpose | Status |
|------|---------|--------|
| [adminPanel.js](backend/static/js/components/adminPanel.js) | **NEW** - Complete admin UI | ✅ Created |
| [main.js:7](backend/static/js/main.js#L7) | Import new adminPanel | ✅ Updated |
| [main.js:331](backend/static/js/main.js#L331) | Initialize adminPanel | ✅ Updated |
| [admin.py](backend/app/api/routers/admin.py) | Backend endpoints (unchanged) | ✅ Verified |
| [admin_config.py](backend/app/api/routers/admin_config.py) | Config endpoints (unchanged) | ✅ Verified |

---

## How It Works

### Initialization Flow

```
Page Load
   ↓
DOMContentLoaded
   ↓
initAdminPanel() called
   ↓
Listens for Admin tab click
   ↓
Admin tab opened (first time)
   ↓
attachAdminEventListeners()
   ↓
loadAdminConfig()
   ↓
API: GET /admin/config
   ↓
Render patterns, repos, access
   ↓
All buttons now functional
```

### User Management Flow

```
Users tab clicked
   ↓
loadUsers()
   ↓
API: GET /admin/users
   ↓
Render user list with buttons
   ↓
Actions available:
  - Create User → Modal → POST /admin/users/create
  - Reset Password → Prompt → POST /admin/users/{username}/reset-password
  - Delete User → Confirm → DELETE /admin/users/{username}
```

### Configuration Sync

```
Admin makes change
   ↓
API call (POST/DELETE)
   ↓
Backend updates .pdm-config.json
   ↓
Git commit & push to GitLab
   ↓
Polling (every 30s) pulls changes
   ↓
All users get updated config
```

---

## Configuration Storage

### Location
- **File:** `.pdm-config.json` (in repository root)
- **Storage:** GitLab repository
- **Sync:** Automatic polling every 30 seconds

### Structure
```json
{
  "version": "1.0.0",
  "filename_patterns": [
    {
      "name": "Standard Pattern",
      "description": "7 digits + optional letters/numbers",
      "link_pattern": "^\\d{7}(_[A-Z]{1,3}\\d{1,3})?$",
      "file_pattern": "^\\d{7}(_[A-Z]{1,3}\\d{1,3})?$",
      "max_stem_length": 15,
      "example_valid": ["1234567", "1234567_ABC123"],
      "example_invalid": ["123456", "1234567_ABCD"]
    }
  ],
  "repositories": [
    {
      "id": "main",
      "name": "Main Repository",
      "gitlab_url": "https://gitlab.com/group/project",
      "project_id": "74609002",
      "branch": "main",
      "allowed_file_types": [".mcam", ".vnc", ".emcam", ".link"],
      "filename_pattern_id": "Standard Pattern",
      "description": "Primary production repository"
    }
  ],
  "user_access": [
    {
      "username": "john_doe",
      "repository_ids": ["main", "legacy"],
      "default_repository_id": "main"
    }
  ],
  "revision_settings": {
    "default_range_limit": 50,
    "show_minor_revisions": true
  },
  "polling_interval_seconds": 30,
  "last_updated_by": "admin",
  "last_updated_at": "2025-01-15T10:30:00Z"
}
```

---

## Safety Features

### Validation Rules

**Pattern Deletion:**
1. Cannot delete if it's the last pattern
2. Cannot delete if any repository uses it
3. Must add replacement pattern first

**Repository Deletion:**
1. Cannot delete if it's the last repository
2. Cannot delete if any user has it as default
3. Must reassign users first

**User Deletion:**
1. Cannot delete yourself
2. Cannot delete other admin users (UI prevents this)
3. Confirmation required

### Error Handling

- All API calls wrapped in try/catch
- User-friendly error messages
- Console logging for debugging
- Graceful fallbacks for missing config

---

## Future-Ready Configuration Options

The admin panel is designed to be **extensible**. Here are the configuration options already in place or easy to add:

### Currently Implemented ✅
1. Custom filename regex patterns
2. Multiple repository support
3. Per-repository file types
4. User repository access control
5. Revision-based history settings
6. Polling interval configuration

### Easy to Add in Future 🔮

**File Management:**
- File size limits per repository
- Allowed file extensions (custom)
- Auto-archive after N days
- Require commit messages minimum length

**User Permissions:**
- Read-only vs read-write per repo
- File checkout time limits
- Max concurrent checkouts per user
- User groups/roles

**Notifications:**
- Email on file checkout
- Slack/Teams integration
- Daily/weekly digest emails
- Lock expiration warnings

**Audit & Compliance:**
- Retention policies
- Audit log export
- Compliance templates
- Approval workflows

**Performance:**
- LFS file size thresholds
- Auto-cleanup schedules
- Cache settings
- Background job configuration

**Integration:**
- Multiple GitLab instances
- External authentication (LDAP, SSO)
- CAD software integration hooks
- Custom webhook endpoints

### How to Add New Config Options

1. **Add field to schemas.py**
```python
class PDMAdminConfig(BaseModel):
    # ... existing fields ...
    max_file_size_mb: int = Field(100, description="Max file size in MB")
```

2. **Update admin_config_service.py validation**
```python
def validate_config(self, config: PDMAdminConfig):
    if config.max_file_size_mb < 1 or config.max_file_size_mb > 1000:
        return False, "File size must be between 1-1000 MB"
```

3. **Add UI field in index.html**
```html
<div>
  <label for="maxFileSize">Max File Size (MB)</label>
  <input type="number" id="maxFileSize" value="100" min="1" max="1000" />
</div>
```

4. **Update adminPanel.js to read/save field**
```javascript
// In loadAdminConfig()
updateMaxFileSizeDisplay(config.max_file_size_mb);

// In save function
const data = {
  // ... existing fields ...
  max_file_size_mb: parseInt(form.querySelector('#maxFileSize').value)
};
```

---

## Testing Instructions

### Test 1: Admin Tab Loads
```
1. Login as admin
2. Click Settings (gear icon)
3. Verify you see "Admin" and "Users" tabs
4. Click "Admin" tab
5. Verify you see 4 subtabs: Patterns, Repos, Access, Tools
6. Check browser console for: "[Admin] All event listeners attached successfully"
```

### Test 2: Pattern Management
```
1. Click "Patterns" subtab
2. Click "Add Pattern" button
3. Fill in all fields
4. Click "Save Pattern"
5. Verify pattern appears in list
6. Try to delete it
7. Verify confirmation dialog
```

### Test 3: Repository Management
```
1. Click "Repos" subtab
2. Click "Add Repository"
3. Fill in all fields
4. Select pattern from dropdown
5. Check file type checkboxes
6. Save
7. Verify repository appears in list
```

### Test 4: User Access
```
1. Click "Access" subtab
2. Click "Add User"
3. Enter username
4. Check repositories
5. Set default repository
6. Save
7. Verify access rule appears
```

### Test 5: Maintenance Tools
```
1. Click "Tools" subtab
2. Try "Create Backup"
   - Verify confirmation dialog
   - Check ~/MastercamBackups/ folder
3. Try "Cleanup LFS"
   - Verify confirmation
   - Check success notification
4. Try "Export Repository"
   - Verify ZIP download starts
5. Try "Reload Config"
   - Verify config reloads
```

### Test 6: User Management
```
1. Click "Users" tab
2. Verify user list loads
3. Click "Create User"
4. Fill form and save
5. Verify new user appears
6. Click "Reset Password" on user
7. Verify prompt appears
8. Try to delete user
9. Verify confirmation
```

### Test 7: Validation Rules
```
1. Try to delete the last pattern
   → Should fail with error
2. Try to delete pattern in use
   → Should fail with error
3. Try to delete last repository
   → Should fail with error
4. Try to delete your own user account
   → Should fail (button hidden or error)
```

---

## Troubleshooting

### "Add Pattern" button doesn't work
**Fix:** Open browser console, refresh page, click Admin tab, check for "[Admin] All event listeners attached successfully"

### Patterns list shows "Failed to load"
**Cause:** `.pdm-config.json` doesn't exist yet
**Fix:** Normal for first use, click "Add Pattern" to create first pattern

### Can't delete pattern/repo
**Cause:** Validation rules preventing deletion
**Fix:** Read error message, add replacement first, then delete

### Users tab shows error
**Cause:** Not authenticated as admin
**Fix:** Logout and login as admin user

### Changes don't appear for other users
**Cause:** Polling hasn't synced yet
**Fix:** Wait 30 seconds, or click "Reload Config from GitLab"

---

## Summary

✅ **All original admin features restored**
  - User management (create, reset password, delete)
  - Repository maintenance (backup, cleanup, export, reset)
  - File override (force unlock, delete)

✅ **New configuration system fully functional**
  - Filename patterns (regex-based, extensible)
  - Multi-repository support
  - User access control
  - GitLab-synced storage

✅ **Future-ready architecture**
  - Easy to add new config fields
  - Modular and well-documented
  - Validation rules prevent errors
  - Graceful error handling

✅ **Complete UI with proper event handling**
  - Lazy loading prevents DOM errors
  - All buttons have handlers
  - Modal-based workflows
  - User-friendly messages

---

## Next Steps

1. ✅ **Revision-based history** - DONE! (see REVISION_HISTORY_COMPLETE.md)
2. ⏳ **User messaging system** - Need to implement
3. ⏳ **Group messaging** - Need to implement

**The admin panel is now complete and fully functional!** 🎉

**Refresh your browser and test it out by logging in as an admin user.**
