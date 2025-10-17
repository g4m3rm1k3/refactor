# Mastercam PDM - Admin Configuration Guide

## Overview

The Mastercam PDM system now features a comprehensive admin configuration system that allows administrators to customize:

- **Filename patterns** (regex-based validation)
- **File types** per repository
- **Multiple repositories** with user access control
- **Revision-based file history** with range filtering
- **Configuration stored in GitLab** (synced across all users)

All configuration is stored in GitLab at `.pdm-config.json` in the repository root and is automatically synced to all users via polling.

---

## Table of Contents

1. [Admin Configuration Structure](#admin-configuration-structure)
2. [Filename Patterns](#filename-patterns)
3. [Repository Configuration](#repository-configuration)
4. [User Access Control](#user-access-control)
5. [Revision History Settings](#revision-history-settings)
6. [API Endpoints](#api-endpoints)
7. [Frontend Integration](#frontend-integration)
8. [Configuration Sync](#configuration-sync)
9. [Migration Guide](#migration-guide)

---

## Admin Configuration Structure

### Configuration File Location

- **File**: `.pdm-config.json`
- **Location**: Repository root (stored in GitLab)
- **Format**: JSON
- **Polling**: Automatically synced every 30 seconds (configurable)

### Configuration Schema

```json
{
  "version": "1.0.0",
  "filename_patterns": [
    {
      "name": "Standard Pattern",
      "description": "7 digits, optional underscore + 1-3 letters + 1-3 numbers",
      "link_pattern": "^\\d{7}(_[A-Z]{3}\\d{3})?$",
      "file_pattern": "^\\d{7}(_[A-Z]{1,3}\\d{1,3})?$",
      "max_stem_length": 15,
      "example_valid": ["1234567", "1234567_ABC123", "1234567_A1"],
      "example_invalid": ["123456", "1234567_ABCD123", "1234567_abc123"]
    }
  ],
  "repositories": [
    {
      "id": "main",
      "name": "Main Repository",
      "gitlab_url": "https://gitlab.com/g4m3rm1k3-group/test",
      "project_id": "74609002",
      "branch": "main",
      "allowed_file_types": [".mcam", ".vnc", ".emcam", ".link"],
      "filename_pattern_id": "Standard Pattern",
      "local_path": null,
      "description": "Primary PDM repository"
    }
  ],
  "user_access": [
    {
      "username": "john_doe",
      "repository_ids": ["main", "secondary"],
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

## Filename Patterns

### What are Filename Patterns?

Filename patterns define the regex rules for validating filenames. Admins can create multiple patterns and assign them to different repositories.

### Pattern Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Pattern identifier (must be unique) |
| `description` | string | Human-readable description |
| `link_pattern` | string | Regex for link files (without extension) |
| `file_pattern` | string | Regex for regular files (without extension) |
| `max_stem_length` | integer | Maximum filename length before extension |
| `example_valid` | array | Example valid filenames |
| `example_invalid` | array | Example invalid filenames |

### Default Patterns

#### 1. Standard Pattern (Current System)
- **Link Pattern**: `^\d{7}(_[A-Z]{3}\d{3})?$`
- **File Pattern**: `^\d{7}(_[A-Z]{1,3}\d{1,3})?$`
- **Examples**:
  - Valid: `1234567`, `1234567_ABC123`, `1234567_A1`
  - Invalid: `123456`, `1234567_ABCD123`

#### 2. Extended Pattern (New)
- **Link Pattern**: `^\d{7}(_[A-Z]{2}\d+)?$`
- **File Pattern**: `^\d{7}(_[A-Z]{2}\d+)?$`
- **Examples**:
  - Valid: `1234567`, `1234567_AB123`, `1234567_XY9999`
  - Invalid: `123456`, `1234567_A123`

#### 3. Legacy Pattern (Flexible)
- **Link Pattern**: `^[A-Za-z0-9_-]+$`
- **File Pattern**: `^[A-Za-z0-9_-]+$`
- **Examples**:
  - Valid: `Project-A`, `CAD_File_2025`
  - Invalid: `file with spaces`, `file@special`

### Creating Custom Patterns

**Example: Creating a pattern for 7 digits + 2 letters + any numbers**

```python
# POST /api/admin/config/patterns
{
  "name": "Custom Pattern 2025",
  "description": "7 digits, underscore, 2 letters, unlimited numbers",
  "link_pattern": "^\\d{7}_[A-Z]{2}\\d+$",
  "file_pattern": "^\\d{7}_[A-Z]{2}\\d+$",
  "max_stem_length": 20,
  "example_valid": ["1234567_AB123", "1234567_XY99999"],
  "example_invalid": ["1234567_ABC123", "1234567_A1"]
}
```

---

## Repository Configuration

### Multi-Repository Support

The system now supports multiple repositories, each with its own:
- File types
- Filename pattern
- GitLab project
- User access control

### Repository Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique repository identifier |
| `name` | string | Display name |
| `gitlab_url` | string | GitLab base URL |
| `project_id` | string | GitLab project ID |
| `branch` | string | Git branch (default: "main") |
| `allowed_file_types` | array | List of allowed extensions |
| `filename_pattern_id` | string | Pattern to use (references pattern name) |
| `local_path` | string | Local repo path (auto-generated if null) |
| `description` | string | Repository description |

### Example: Adding a Secondary Repository

```python
# POST /api/admin/config/repositories
{
  "id": "legacy",
  "name": "Legacy Projects",
  "gitlab_url": "https://gitlab.com/company/legacy",
  "project_id": "12345",
  "branch": "main",
  "allowed_file_types": [".mcam", ".vnc"],
  "filename_pattern_id": "Legacy Pattern",
  "description": "Old projects with flexible naming"
}
```

### Per-Repository File Types

Each repository can have different allowed file types:

```json
{
  "repositories": [
    {
      "id": "main",
      "allowed_file_types": [".mcam", ".vnc", ".emcam", ".link"]
    },
    {
      "id": "cnc_only",
      "allowed_file_types": [".vnc"]
    },
    {
      "id": "mastercam_only",
      "allowed_file_types": [".mcam", ".emcam"]
    }
  ]
}
```

---

## User Access Control

### User Repository Access

Admins can control which users have access to which repositories.

### Access Properties

| Property | Type | Description |
|----------|------|-------------|
| `username` | string | Username |
| `repository_ids` | array | List of accessible repository IDs |
| `default_repository_id` | string | Default repo on login |

### Example: Assigning Repository Access

```python
# POST /api/admin/config/user-access
{
  "username": "john_doe",
  "repository_ids": ["main", "legacy"],
  "default_repository_id": "main"
}
```

### Access Rules

1. **No Access Entry**: User has access to ALL repositories (backward compatibility)
2. **Empty List**: User has NO repository access
3. **Default Repository**: Must be in the user's access list

### Checking User Access

```python
# GET /api/admin/config/my-repositories
# Returns: ["main", "legacy", "cnc_only"]
```

---

## Revision History Settings

### Revision-Based History (Not Date-Based!)

The system now displays file history by **revision ranges** instead of dates.

### Settings Properties

| Property | Type | Description |
|----------|------|-------------|
| `display_mode` | string | "range" or "list" |
| `default_limit` | integer | Default number of revisions to show |
| `show_minor_revisions` | boolean | Include minor revisions in range |
| `group_by_major` | boolean | Group by major version |

### Example Revision Display

**Instead of**: "Modified on 2025-01-15"

**Now Shows**: "Revisions 1.0 - 20.5" (user can filter to "5.0 - 15.0")

### Revision Range Filtering

Users can filter file history by revision range:

```http
GET /api/files/1234567_ABC123.mcam/history/revisions?start_revision=5.0&end_revision=15.0&limit=50
```

**Response**:
```json
{
  "filename": "1234567_ABC123.mcam",
  "total_revisions": 25,
  "revision_range": "5.0 - 15.0",
  "filtered": true,
  "revisions": [
    {
      "revision": "15.0",
      "commit_hash": "abc123...",
      "author": "john_doe",
      "timestamp": "2025-10-16T...",
      "message": "REV 15.0: Updated toolpaths"
    },
    ...
  ]
}
```

---

## API Endpoints

### Admin Configuration Endpoints

All endpoints require admin authentication.

#### 1. Get Configuration

```http
GET /api/admin/config/
Authorization: Bearer <admin_token>
```

**Response**: Complete `PDMAdminConfig` object

#### 2. Update Configuration

```http
POST /api/admin/config/
Content-Type: application/json

{
  "config": { ... },
  "admin_user": "admin"
}
```

#### 3. Get Filename Patterns

```http
GET /api/admin/config/patterns
```

**Response**: Array of `FileNamePattern` objects

#### 4. Add Filename Pattern

```http
POST /api/admin/config/patterns
Content-Type: application/json

{
  "name": "New Pattern",
  "description": "...",
  "link_pattern": "...",
  "file_pattern": "...",
  "max_stem_length": 20,
  "example_valid": [...],
  "example_invalid": [...]
}
```

#### 5. Get Repositories

```http
GET /api/admin/config/repositories
```

#### 6. Add Repository

```http
POST /api/admin/config/repositories
Content-Type: application/json

{
  "id": "repo_id",
  "name": "Repository Name",
  ...
}
```

#### 7. Get User Access

```http
GET /api/admin/config/user-access
```

#### 8. Update User Access

```http
POST /api/admin/config/user-access
Content-Type: application/json

{
  "username": "user",
  "repository_ids": ["repo1", "repo2"],
  "default_repository_id": "repo1"
}
```

#### 9. Delete User Access

```http
DELETE /api/admin/config/user-access/{username}
```

#### 10. Get My Repositories

```http
GET /api/admin/config/my-repositories
```

**Response**: `["repo1", "repo2"]`

### File History Endpoints

#### Get Revision-Based History

```http
GET /api/files/{filename}/history/revisions?start_revision=1.0&end_revision=20.0&limit=50
```

**Query Parameters**:
- `start_revision` (optional): Starting revision (e.g., "1.0")
- `end_revision` (optional): Ending revision (e.g., "20.5")
- `limit` (optional): Max revisions to return (default: 50)

---

## Frontend Integration

### Using Dynamic Validators

The validators now accept pattern configuration:

```javascript
// In file upload handler
const adminConfigService = getAdminConfigService();
const patternConfig = getPatternConfigFromService(adminConfigService);

// Validate filename
const [isValid, errorMsg] = validateFilenameFormat(
  filename,
  patternConfig
);
```

### Displaying Revision History

```javascript
// Fetch revision history with range
const response = await fetch(
  `/api/files/${filename}/history/revisions?start_revision=5.0&end_revision=15.0`
);

const history = await response.json();

// Display: "Showing revisions 5.0 - 15.0 (25 total)"
console.log(`Revision range: ${history.revision_range}`);
console.log(`Total revisions: ${history.total_revisions}`);
console.log(`Filtered: ${history.filtered ? 'Yes' : 'No'}`);
```

---

## Configuration Sync

### How Polling Works

1. **Startup**: AdminConfigService loads `.pdm-config.json`
2. **Polling**: Every 30 seconds (configurable), checks GitLab for updates
3. **Detection**: Compares file hash between local and remote
4. **Update**: If changed, pulls latest and reloads config
5. **Propagation**: All users receive updated config automatically

### Polling Configuration

```json
{
  "polling_interval_seconds": 30
}
```

### Manual Configuration Push

When admin saves config:

1. Config written to `.pdm-config.json`
2. File committed to GitLab
3. Pushed to remote
4. All users pull on next poll cycle

### Sync Monitoring

```python
# Check last update
config = admin_config_service.get_config()
print(f"Last updated by: {config.last_updated_by}")
print(f"Last updated at: {config.last_updated_at}")
```

---

## Migration Guide

### Migrating from Old System

The new system is **backward compatible**. If no `.pdm-config.json` exists, default configuration is created:

#### Step 1: Initial Setup

On first run, the system automatically:
1. Creates `.pdm-config.json` with current settings
2. Uses "Standard Pattern" (existing regex)
3. Creates "main" repository with current GitLab config
4. No user access restrictions (everyone has access to all repos)

#### Step 2: Customization

Admins can then:
1. Add new filename patterns
2. Create additional repositories
3. Set up user access control
4. Configure revision history settings

#### Step 3: Gradual Migration

1. **Phase 1**: Keep existing pattern, add new repositories
2. **Phase 2**: Create custom patterns for new projects
3. **Phase 3**: Implement user access control
4. **Phase 4**: Full multi-repo setup

### Default Configuration

If no config file exists, this is created automatically:

```json
{
  "version": "1.0.0",
  "filename_patterns": [
    {
      "name": "Standard Pattern",
      "description": "7 digits, optional underscore + 1-3 letters + 1-3 numbers",
      "link_pattern": "^\\d{7}(_[A-Z]{3}\\d{3})?$",
      "file_pattern": "^\\d{7}(_[A-Z]{1,3}\\d{1,3})?$",
      "max_stem_length": 15,
      "example_valid": ["1234567", "1234567_ABC123"],
      "example_invalid": ["123456", "1234567_ABCD123"]
    }
  ],
  "repositories": [
    {
      "id": "main",
      "name": "Main Repository",
      "gitlab_url": "<from config.json>",
      "project_id": "<from config.json>",
      "branch": "main",
      "allowed_file_types": [".mcam", ".vnc", ".emcam", ".link"],
      "filename_pattern_id": "Standard Pattern"
    }
  ],
  "user_access": [],
  "revision_settings": {
    "display_mode": "range",
    "default_limit": 50,
    "show_minor_revisions": true,
    "group_by_major": false
  },
  "polling_interval_seconds": 30
}
```

---

## Example: Complete Setup

### 1. Create Custom Pattern

```http
POST /api/admin/config/patterns
{
  "name": "Extended 2025",
  "description": "7 digits + 2 letters + unlimited numbers",
  "link_pattern": "^\\d{7}_[A-Z]{2}\\d+$",
  "file_pattern": "^\\d{7}_[A-Z]{2}\\d+$",
  "max_stem_length": 20,
  "example_valid": ["1234567_AB123", "1234567_XY99999"],
  "example_invalid": ["1234567_ABC123"]
}
```

### 2. Create New Repository

```http
POST /api/admin/config/repositories
{
  "id": "new_projects",
  "name": "2025 Projects",
  "gitlab_url": "https://gitlab.com/company/projects2025",
  "project_id": "67890",
  "branch": "main",
  "allowed_file_types": [".mcam", ".emcam"],
  "filename_pattern_id": "Extended 2025",
  "description": "New projects using extended naming"
}
```

### 3. Assign User Access

```http
POST /api/admin/config/user-access
{
  "username": "john_engineer",
  "repository_ids": ["main", "new_projects"],
  "default_repository_id": "new_projects"
}
```

### 4. Verify Configuration

```http
GET /api/admin/config/
```

---

## Troubleshooting

### Issue: Pattern Not Validating

**Problem**: New pattern not being used for validation

**Solution**:
1. Check pattern name matches repository's `filename_pattern_id`
2. Verify regex escaping (use `\\d` not `\d` in JSON)
3. Test regex at regex101.com
4. Check admin config service is initialized

### Issue: User Can't Access Repository

**Problem**: User can't see files from a repository

**Solution**:
1. Check user access configuration
2. Verify repository ID is in user's `repository_ids`
3. Check if user has any access entry (no entry = access to all)
4. Verify repository exists in config

### Issue: Revision History Not Showing Range

**Problem**: History shows dates instead of revisions

**Solution**:
1. Use `/history/revisions` endpoint (not `/history`)
2. Check file has revision metadata
3. Verify `revision_settings.display_mode` is "range"

### Issue: Config Not Syncing

**Problem**: Config changes not appearing on other clients

**Solution**:
1. Check `.pdm-config.json` exists in GitLab
2. Verify polling is running (check logs)
3. Manually pull repository to see changes
4. Check `polling_interval_seconds` setting
5. Restart application

---

## Security Considerations

### Admin-Only Access

All admin config endpoints require:
1. Valid JWT token
2. `is_admin` flag in token payload
3. Username in `ADMIN_USERS` list

### Configuration Validation

Every config update is validated:
1. Regex patterns must compile
2. Repository IDs must be unique
3. Pattern references must exist
4. User access must reference valid repos
5. Default repo must be in user's access list

### GitLab Token Security

- Tokens encrypted in `config.json` using Fernet
- Never stored in `.pdm-config.json`
- Only admin can view/update tokens

---

## Future Enhancements

Potential future features:

1. **Pattern Versioning**: Track pattern changes over time
2. **Conditional Patterns**: Different patterns based on file type
3. **Custom Metadata Fields**: Admin-defined metadata fields
4. **Workflow Rules**: Approval workflows for certain repositories
5. **Audit Logging**: Track all config changes
6. **Pattern Testing UI**: Test filenames against patterns in UI
7. **Bulk User Import**: Import user access from CSV
8. **Repository Templates**: Pre-configured repo templates

---

## Summary

The admin configuration system provides:

✅ **Customizable Filename Patterns** - Regex-based validation
✅ **Multi-Repository Support** - Multiple GitLab projects
✅ **User Access Control** - Per-repository permissions
✅ **Revision-Based History** - Range filtering by revision
✅ **GitLab Sync** - Config stored in Git, synced to all users
✅ **Backward Compatible** - Works with existing deployments
✅ **Admin API** - Full REST API for management
✅ **Dynamic Validation** - Patterns loaded from config

All configuration is centralized, version-controlled, and automatically distributed to all users.

For questions or issues, please refer to the API documentation or contact your system administrator.
