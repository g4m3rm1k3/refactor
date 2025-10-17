# GitLab Integration - Single Source of Truth

## Architecture Overview

**GitLab = Single Source of Truth**
- Main repository contains `.pdm-config.json`
- All users connect to main repo first
- Users auto-discovered on first connection
- Admin notified of new users
- Config syncs to all connected users

---

## Changes Required

### 1. Auto-Discover Users from GitLab ✅

**When a user connects:**
```
User authenticates → GitLab credentials validated → User info extracted
                                                        ↓
                                             Username recorded in DB
                                                        ↓
                                             Check if new user
                                                        ↓
                                          Notify admin if new user
```

**Backend Changes:**
- Modify authentication to capture GitLab username
- Store user info in local DB (username, first_seen, last_seen)
- Track new vs returning users
- Create notification queue for admins

**Frontend Changes:**
- Remove "Create User" button
- Show "GitLab Users" list instead
- Display first seen / last seen timestamps
- Show "NEW" badge for recently connected users

---

### 2. Repository Update Functionality ✅

**Problem:** POST /repositories fails if repo already exists
**Solution:** Make POST act as upsert (create or update)

**Backend Changes:**
```python
@router.post("/repositories")
async def add_or_update_repository():
    if repository.id exists:
        # Update existing
        update_repository(repository)
    else:
        # Add new
        add_repository(repository)
```

**Frontend Changes:**
- Edit button uses same modal as Add
- Form pre-fills with existing values
- Save button updates instead of creating

---

### 3. Repository Selector for Users ✅

**Show dropdown when user has access to multiple repos**

**Location:** Top navigation bar (next to user name)

**UI:**
```
┌──────────────────────────────────┐
│ [Repo: Main ▼]  g4m3rm1k3  [⚙️] │
└──────────────────────────────────┘
```

**Behavior:**
- Hidden if user has access to only 1 repo
- Shown if user has access to 2+ repos
- Switching repo reloads file list
- Persists selection in localStorage

---

### 4. Custom File Extensions ✅

**Current limitation:** File types hardcoded (.mcam, .vnc, .emcam, .link)

**Solution:** Allow custom extensions in pattern definition

**Schema Changes:**
```python
class FileNamePattern(BaseModel):
    name: str
    description: str
    link_pattern: str
    file_pattern: str
    max_stem_length: int
    allowed_extensions: List[str]  # NEW: [".mcam", ".vnc", ".custom"]
    example_valid: List[str]
    example_invalid: List[str]
```

**Why in Pattern not Repository?**
- Different projects may have different CAM software
- Pattern defines validation rules including what files are allowed
- Repository references a pattern and inherits its rules

**Example Use Case:**
```
Pattern: "Legacy CAM Files"
  - File Pattern: ^\d{7}$
  - Allowed Extensions: [".mcam", ".vnc", ".ops"]

Pattern: "New CAM Files 2025"
  - File Pattern: ^\d{7}_[A-Z]{2}\d+$
  - Allowed Extensions: [".mcam-x", ".vnc-x", ".session"]
```

---

### 5. Admin Notifications ✅

**Notification Types:**
1. New user connected
2. Config changed by another admin
3. File locked for >24 hours
4. LFS storage nearing limit

**Implementation:**
- Backend: Notification queue table
- API: GET /admin/notifications (unread count + list)
- Frontend: Bell icon with badge in top nav
- WebSocket: Real-time notification push

---

## Implementation Order

### Phase 1: Critical Fixes (Do Now)
1. ✅ Fix repository update (make POST upsert)
2. ✅ Add custom file extensions to patterns
3. ✅ Add repository selector dropdown

### Phase 2: GitLab Integration (Next)
4. ✅ Auto-discover users on connection
5. ✅ Track user activity (first_seen, last_seen)
6. ✅ Update Users tab to show GitLab users

### Phase 3: Notifications (After)
7. ✅ Create notification system
8. ✅ Add notification bell icon
9. ✅ WebSocket push for real-time alerts

---

## Database Schema Changes

### New Table: `gitlab_users`
```sql
CREATE TABLE gitlab_users (
    username VARCHAR(255) PRIMARY KEY,
    gitlab_id INTEGER,
    email VARCHAR(255),
    display_name VARCHAR(255),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### New Table: `admin_notifications`
```sql
CREATE TABLE admin_notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50),  -- 'new_user', 'config_change', etc.
    message TEXT,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    admin_username VARCHAR(255)
);
```

---

## API Endpoints to Add/Modify

### User Management
- `GET /gitlab/users` - Get all GitLab users (discovered)
- `POST /gitlab/users/sync` - Manually sync users from GitLab
- `PATCH /admin/users/{username}/repositories` - Assign repos to user

### Repository Management
- `PUT /admin/config/repositories/{repo_id}` - Update repository (NEW)
- `GET /repositories` - Get user's accessible repos (user-facing)

### Notifications
- `GET /admin/notifications` - Get unread notifications
- `PATCH /admin/notifications/{id}/read` - Mark as read
- `DELETE /admin/notifications/{id}` - Dismiss notification

---

## Frontend Changes

### Top Navigation
```html
<!-- Show repo selector if user has 2+ repos -->
<select id="repoSelector" class="...">
  <option value="main">Main Repository</option>
  <option value="legacy">Legacy Projects</option>
</select>

<!-- Show notification bell for admins -->
<button id="notificationBell">
  <i class="fa-solid fa-bell"></i>
  <span class="badge">3</span> <!-- Unread count -->
</button>
```

### Users Tab (Admin)
```
Before (Manual Creation):
  [Create User] button
  List of manually created users

After (GitLab Auto-Discovery):
  [Sync GitLab Users] button
  List of all users who have connected:
    - Username (from GitLab)
    - First Seen: 2025-01-15
    - Last Seen: 2025-01-17 (2 hours ago)
    - Status: Active/Inactive
    - [Assign Repositories] button
```

### Pattern Configuration
```
Add new field:
  Allowed Extensions: [.mcam] [.vnc] [.emcam] [+ Add]

  Each extension:
    - Text input
    - Remove button
    - Must start with "."
```

---

## CAM File Validation Integration

**Your Question:** "how we put our cam validation into the PDM"

**Solution:** Custom validators per pattern

### Option 1: File Extension-Based Validation
```python
class FileNamePattern(BaseModel):
    # ... existing fields ...
    allowed_extensions: List[str]
    extension_validators: Dict[str, str]  # NEW

    # Example:
    # {
    #   ".mcam": "validate_mastercam_file",
    #   ".vnc": "validate_vericut_file"
    # }
```

### Option 2: Content Validation Hooks
```python
# In validators.py
def validate_cam_file(file_path: str, extension: str) -> Tuple[bool, str]:
    """
    Validate CAM file contents based on extension
    """
    if extension == ".mcam":
        return validate_mastercam_file(file_path)
    elif extension == ".vnc":
        return validate_vericut_file(file_path)
    # ... more validators

def validate_mastercam_file(file_path: str) -> Tuple[bool, str]:
    """
    Check if .mcam file has valid structure
    - Check file header
    - Validate version
    - Check for required sections
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(100)
            # Your validation logic here
            if not header.startswith(b'MCAM'):
                return False, "Invalid Mastercam file header"
        return True, ""
    except Exception as e:
        return False, str(e)
```

### Option 3: Plugin-Based Validators
```python
# Create validators as plugins
# backend/app/validators/cam_validators/

# mastercam_validator.py
class MastercamValidator:
    def validate(self, file_path: str) -> ValidationResult:
        # Your Mastercam-specific validation
        pass

# vericut_validator.py
class VericutValidator:
    def validate(self, file_path: str) -> ValidationResult:
        # Your Vericut-specific validation
        pass
```

**Configure in pattern:**
```json
{
  "name": "Mastercam Files",
  "allowed_extensions": [".mcam"],
  "validators": {
    ".mcam": {
      "type": "plugin",
      "plugin": "mastercam_validator",
      "options": {
        "min_version": "2024",
        "require_toolpath": true
      }
    }
  }
}
```

---

## Questions for You

1. **GitLab API Access:**
   - Do you have a GitLab API token configured?
   - Should we query GitLab API to get user details, or just capture from authentication?

2. **User Discovery:**
   - Should we import all GitLab project members immediately?
   - Or only add users as they connect for the first time?

3. **CAM Validation:**
   - What specific validation do you need? (file structure, version, content checks?)
   - Should validation happen on upload, or also on checkout?
   - Should invalid files be rejected or just warned?

4. **File Extensions:**
   - What custom extensions do you need beyond .mcam, .vnc, .emcam, .link?
   - Should extensions be validated (e.g., must match a pattern)?

---

## Let's Start Implementation

I'll begin with:
1. **Repository Update (PUT endpoint)**
2. **Custom file extensions in patterns**
3. **Repository selector dropdown**

Then we'll move to GitLab user auto-discovery.

Ready to proceed?
