# Admin Configuration UI - Implementation Complete! 🎉

## Overview

The admin configuration UI has been successfully implemented with full frontend and backend integration. This allows administrators to manage all aspects of the PDM system through an intuitive web interface.

---

## ✅ What's Been Implemented

### **Backend Components**

1. **Admin Configuration API** ([admin_config.py](backend/app/api/routers/admin_config.py))
   - Full CRUD operations for patterns, repositories, and user access
   - Configuration validation
   - GitLab-based storage with automatic syncing

2. **Admin Configuration Service** ([admin_config_service.py](backend/app/services/admin_config_service.py))
   - Loads/saves config to GitLab (`.pdm-config.json`)
   - Automatic polling (every 30 seconds)
   - Default configuration generator
   - Validation and error handling

3. **Enhanced API Endpoints**
   - `/admin/config/` - Get/update full configuration
   - `/admin/config/patterns` - Manage filename patterns
   - `/admin/config/repositories` - Manage repositories
   - `/admin/config/user-access` - Manage user access
   - `/files/{filename}/history/revisions` - Revision-based history

### **Frontend Components**

1. **Admin Configuration UI** ([index.html](backend/static/index.html))
   - 4 tabbed sections: Patterns, Repositories, Access, Tools
   - Modal forms for adding/editing configurations
   - Real-time updates
   - Dark mode support

2. **Admin Config JavaScript Module** ([adminConfig.js](backend/static/js/components/adminConfig.js))
   - Handles all admin UI interactions
   - Modal management
   - Data loading and display
   - Form validation

3. **Enhanced API Service** ([service.js](backend/static/js/api/service.js))
   - All admin config API methods
   - Revision-based history endpoint
   - Proper error handling

---

## 🎨 Admin UI Features

### **1. Filename Patterns Tab**

**Features:**
- View all defined regex patterns
- Add new patterns with validation
- See examples of valid/invalid filenames
- Delete patterns (requires no repositories using it)

**Fields:**
- Pattern Name (unique identifier)
- Description
- Link Pattern (regex)
- File Pattern (regex)
- Max Stem Length
- Valid/Invalid Examples

**Example:**
```
Name: Extended 2025
Description: 7 digits + 2 letters + unlimited numbers
Link Pattern: ^\d{7}_[A-Z]{2}\d+$
File Pattern: ^\d{7}_[A-Z]{2}\d+$
Max Length: 20
Valid: 1234567_AB123, 1234567_XY999
Invalid: 1234567_ABC123, 123456
```

### **2. Repositories Tab**

**Features:**
- Configure multiple GitLab repositories
- Assign filename patterns to repos
- Set allowed file types per repo
- View repository details

**Fields:**
- Repository ID (unique)
- Display Name
- GitLab URL
- Project ID
- Branch
- Allowed File Types (checkboxes)
- Filename Pattern (dropdown)
- Description

**Example:**
```
ID: projects_2025
Name: 2025 New Projects
GitLab: https://gitlab.com/company/projects2025
Project ID: 98765
Branch: main
File Types: .mcam, .emcam
Pattern: Extended 2025
```

### **3. User Access Tab**

**Features:**
- Control user access to repositories
- Set default repository per user
- Visual repository badges
- Remove user access

**Fields:**
- Username
- Accessible Repositories (checkboxes)
- Default Repository (dropdown)

**Example:**
```
Username: john_engineer
Accessible Repos: [main] [projects_2025] [legacy]
Default Repo: projects_2025
```

**Access Rules:**
- No entry for user = access to ALL repositories
- Empty list = NO access
- Default repo must be in user's access list

### **4. Maintenance Tools Tab**

**Features:**
- View configuration info
- Reload config from GitLab
- Create backups
- Export repository
- Clean up LFS files
- Reset repository (danger zone)

**Configuration Info Displayed:**
- Config Version
- Last Updated By
- Last Updated At
- Polling Interval

---

## 🚀 How to Use the Admin UI

### **Step 1: Access the Admin Panel**

1. Start the application: `python run.py`
2. Login as an admin user (`admin` or `g4m3rm1k3`)
3. Click the **Settings gear icon** (⚙️) in the top-right
4. Click the **Admin tab** (shield icon)

### **Step 2: Navigate Admin Tabs**

The admin panel has 4 tabs:

| Icon | Tab | Purpose |
|------|-----|---------|
| 📝 | **Patterns** | Manage filename regex patterns |
| 💾 | **Repos** | Configure GitLab repositories |
| 🔒 | **Access** | Control user repository access |
| 🛠️ | **Tools** | Maintenance and info |

### **Step 3: Add a Filename Pattern**

1. Go to **Patterns** tab
2. Click **"+ Add Pattern"** button
3. Fill in the form:
   ```
   Pattern Name: My Custom Pattern
   Description: 7 digits + 3 letters + 2 numbers
   Link Pattern: ^\d{7}_[A-Z]{3}\d{2}$
   File Pattern: ^\d{7}_[A-Z]{3}\d{2}$
   Max Length: 20
   Valid Examples: 1234567_ABC12, 9876543_XYZ99
   Invalid Examples: 123456, 1234567_AB123
   ```
4. Click **"Save Pattern"**
5. Pattern is immediately saved to GitLab

### **Step 4: Add a Repository**

1. Go to **Repos** tab
2. Click **"+ Add Repository"** button
3. Fill in the form:
   ```
   Repository ID: new_projects
   Display Name: New Projects 2025
   GitLab URL: https://gitlab.com/company/projects
   Project ID: 12345
   Branch: main
   File Types: ☑ .mcam ☑ .vnc ☐ .emcam ☑ .link
   Pattern: My Custom Pattern
   Description: Projects using new naming scheme
   ```
4. Click **"Save Repository"**
5. Repository configuration saved to GitLab

### **Step 5: Configure User Access**

1. Go to **Access** tab
2. Click **"+ Add User"** button
3. Fill in the form:
   ```
   Username: engineer_mike
   Repositories: ☑ main ☑ new_projects ☐ legacy
   Default Repo: new_projects
   ```
4. Click **"Save Access"**
5. User access saved to GitLab

### **Step 6: View Configuration Info**

1. Go to **Tools** tab
2. View current configuration:
   ```
   Config Version: 1.0.0
   Last Updated By: admin
   Last Updated: 2025-10-16 15:30:00
   Polling Interval: 30s
   ```
3. Click **"Reload Config from GitLab"** to force refresh

---

## 🔄 How Configuration Sync Works

### **Automatic Synchronization**

1. **Admin makes change** → Clicks "Save"
2. **Backend validates** → Checks regex, repository refs, etc.
3. **Saves to GitLab** → Commits `.pdm-config.json` to repo
4. **All users poll** → Check for updates every 30 seconds
5. **Config updated** → All users get new settings automatically

### **Polling Mechanism**

```python
# In admin_config_service.py
async def start_polling(self, git_service=None):
    while True:
        await asyncio.sleep(polling_interval)  # Default: 30 seconds

        # Check if GitLab has newer config
        if config_changed_on_gitlab():
            pull_latest_changes()
            reload_config()
```

**Benefits:**
- All users stay in sync
- No manual config distribution
- Version controlled (stored in Git)
- Automatic rollback via Git history

---

## 📊 Configuration File Structure

### **.pdm-config.json** (stored in GitLab repo root)

```json
{
  "version": "1.0.0",
  "filename_patterns": [
    {
      "name": "Standard Pattern",
      "description": "7 digits + optional suffix",
      "link_pattern": "^\\d{7}(_[A-Z]{3}\\d{3})?$",
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
      "description": "Primary PDM repository"
    }
  ],
  "user_access": [
    {
      "username": "engineer_1",
      "repository_ids": ["main", "projects_2025"],
      "default_repository_id": "main"
    }
  ],
  "revision_settings": {
    "display_mode": "range",
    "default_limit": 50,
    "show_minor_revisions": true,
    "group_by_major": false
  },
  "polling_interval_seconds": 30,
  "last_updated_by": "admin",
  "last_updated_at": "2025-10-16T20:30:00.000000+00:00"
}
```

---

## 🎯 UI/UX Features

### **Responsive Design**
- Mobile-friendly layout
- Collapsible sections
- Touch-friendly buttons
- Adaptive forms

### **Dark Mode Support**
- All admin UI components support dark mode
- Proper contrast ratios
- Smooth theme transitions

### **Real-Time Updates**
- Auto-reload on config changes
- Loading spinners
- Success/error notifications
- Smooth transitions

### **Form Validation**
- Required field indicators (red *)
- Regex pattern validation
- Duplicate name checking
- User-friendly error messages

### **Visual Indicators**
- Color-coded badges for file types
- Repository access pills
- Status icons
- Hover effects

---

## 🔧 API Endpoints Summary

### **GET /admin/config/**
Returns complete admin configuration

**Response:**
```json
{
  "version": "1.0.0",
  "filename_patterns": [...],
  "repositories": [...],
  "user_access": [...],
  "revision_settings": {...},
  "polling_interval_seconds": 30
}
```

### **POST /admin/config/patterns**
Add a new filename pattern

**Request:**
```json
{
  "name": "My Pattern",
  "description": "Description here",
  "link_pattern": "^\\d{7}...$",
  "file_pattern": "^\\d{7}...$",
  "max_stem_length": 20,
  "example_valid": ["1234567_AB12"],
  "example_invalid": ["123456"]
}
```

### **POST /admin/config/repositories**
Add a new repository

**Request:**
```json
{
  "id": "repo_id",
  "name": "Display Name",
  "gitlab_url": "https://...",
  "project_id": "12345",
  "branch": "main",
  "allowed_file_types": [".mcam"],
  "filename_pattern_id": "My Pattern"
}
```

### **POST /admin/config/user-access**
Update user repository access

**Request:**
```json
{
  "username": "user123",
  "repository_ids": ["main", "projects"],
  "default_repository_id": "main"
}
```

### **DELETE /admin/config/user-access/{username}**
Remove user access configuration

### **GET /files/{filename}/history/revisions**
Get revision-based file history

**Query Parameters:**
- `start_revision` (optional): e.g., "1.0"
- `end_revision` (optional): e.g., "20.5"
- `limit` (optional): default 50

**Response:**
```json
{
  "filename": "1234567_ABC123.mcam",
  "total_revisions": 25,
  "revision_range": "1.0 - 20.5",
  "filtered": true,
  "revisions": [
    {
      "revision": "20.5",
      "commit_hash": "abc123...",
      "author": "engineer_1",
      "timestamp": "2025-10-16T...",
      "message": "Updated toolpaths"
    }
  ]
}
```

---

## 🎨 UI Components

### **Pattern Card**
```html
┌─────────────────────────────────────────────┐
│ Standard Pattern                    [🗑️]    │
│ 7 digits + optional suffix                  │
│                                              │
│ Link Pattern:                                │
│ ^\d{7}(_[A-Z]{3}\d{3})?$                   │
│                                              │
│ File Pattern:                                │
│ ^\d{7}(_[A-Z]{1,3}\d{1,3})?$               │
│                                              │
│ Max Length: 15                               │
│ Valid: 1234567, 1234567_ABC123              │
└─────────────────────────────────────────────┘
```

### **Repository Card**
```html
┌─────────────────────────────────────────────┐
│ Main Repository                     [🗑️]    │
│ main                                         │
│ Primary PDM repository                       │
│                                              │
│ GitLab URL: https://gitlab.com/...           │
│ Project ID: 74609002                         │
│ Branch: main                                 │
│ Pattern: Standard Pattern                    │
│                                              │
│ File Types: [.mcam] [.vnc] [.emcam] [.link] │
└─────────────────────────────────────────────┘
```

### **User Access Card**
```html
┌─────────────────────────────────────────────┐
│ 👤 engineer_1                       [🗑️]    │
│ Default: main                                │
│                                              │
│ Accessible Repositories:                     │
│ [main] [projects_2025] [legacy]             │
└─────────────────────────────────────────────┘
```

---

## 🔒 Security Features

### **Admin-Only Access**
- All `/admin/config/*` endpoints require admin authentication
- JWT token with `is_admin` flag validated
- Username must be in `ADMIN_USERS` list

### **Configuration Validation**
- Regex patterns must compile
- Repository IDs must be unique
- Pattern references must exist
- User access must reference valid repos
- Default repo must be in user's access list

### **Data Encryption**
- GitLab tokens encrypted with Fernet
- JWT tokens signed and validated
- Secure cookie settings

---

## 📝 Usage Examples

### **Example 1: Create Pattern for New Project Type**

**Scenario:** Need pattern for 7 digits + 2 letters + any numbers

**Steps:**
1. Open Admin → Patterns tab
2. Click "+ Add Pattern"
3. Fill in:
   ```
   Name: Project 2025 Pattern
   Description: 7 digits + 2 letters + unlimited numbers
   Link: ^\d{7}_[A-Z]{2}\d+$
   File: ^\d{7}_[A-Z]{2}\d+$
   Max: 25
   Valid: 1234567_AB123, 1234567_XY9999
   Invalid: 1234567_A123, 1234567_ABC123
   ```
4. Save
5. **Result:** Pattern available for all repositories

### **Example 2: Add Secondary Repository**

**Scenario:** Need separate repo for legacy projects

**Steps:**
1. Open Admin → Repos tab
2. Click "+ Add Repository"
3. Fill in:
   ```
   ID: legacy
   Name: Legacy Projects
   URL: https://gitlab.com/company/legacy
   Project: 67890
   Branch: main
   Types: .mcam only
   Pattern: Legacy Pattern
   ```
4. Save
5. **Result:** New repo available, synced to all users

### **Example 3: Restrict User Access**

**Scenario:** New engineer should only access main repo

**Steps:**
1. Open Admin → Access tab
2. Click "+ Add User"
3. Fill in:
   ```
   Username: new_engineer
   Repos: ☑ main ☐ legacy ☐ projects_2025
   Default: main
   ```
4. Save
5. **Result:** User can only see files from main repo

---

## 🐛 Troubleshooting

### **Issue: Admin tab not visible**

**Solution:**
- Ensure logged in as admin user (`admin` or `g4m3rm1k3`)
- Check JWT token has `is_admin: true` flag
- Verify username in `ADMIN_USERS` list

### **Issue: Pattern not saving**

**Solution:**
- Check regex is valid (test at regex101.com)
- Ensure pattern name is unique
- Check browser console for errors
- Verify admin authentication

### **Issue: Repository not appearing**

**Solution:**
- Ensure repository ID is unique
- Verify GitLab URL is correct
- Check filename pattern exists
- Reload page to refresh

### **Issue: Config not syncing to other users**

**Solution:**
- Check polling interval (default 30s)
- Verify `.pdm-config.json` exists in GitLab
- Check backend logs for sync errors
- Click "Reload Config from GitLab" manually

---

## 📚 Additional Resources

- **[ADMIN_CONFIGURATION_GUIDE.md](ADMIN_CONFIGURATION_GUIDE.md)** - Detailed configuration guide
- **API Documentation** - `/docs` endpoint (Swagger UI)
- **Backend Code**:
  - [admin_config_service.py](backend/app/services/admin_config_service.py)
  - [admin_config.py](backend/app/api/routers/admin_config.py)
- **Frontend Code**:
  - [adminConfig.js](backend/static/js/components/adminConfig.js)
  - [service.js](backend/static/js/api/service.js)

---

## ✨ What's Next?

Future enhancements could include:

1. **Pattern Testing Tool** - Test filenames against patterns in UI
2. **Bulk User Import** - CSV upload for user access
3. **Audit Log** - Track all configuration changes
4. **Repository Templates** - Pre-configured repo templates
5. **Conditional Patterns** - Different patterns per file type
6. **Custom Metadata Fields** - Admin-defined metadata
7. **Approval Workflows** - Multi-step file approval process
8. **Pattern Versioning** - Track pattern changes over time

---

## 🎉 Summary

The admin configuration UI is **fully functional** and ready to use!

**Features Completed:**
✅ Customizable filename patterns (regex)
✅ Multi-repository support
✅ User access control
✅ GitLab-based config storage
✅ Automatic config synchronization
✅ Revision-based file history
✅ Full CRUD operations
✅ Dark mode support
✅ Mobile responsive
✅ Form validation
✅ Real-time updates

**How to Access:**
1. Login as admin
2. Click ⚙️ Settings
3. Click 🛡️ Admin tab
4. Configure away!

Enjoy your fully customizable PDM system! 🚀
