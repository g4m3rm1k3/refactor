from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Note: We are only moving the Pydantic models here.
# The validation functions will be moved to a different 'utils' file later.


class FileInfo(BaseModel):
    filename: str = Field(..., description="The name of the file")
    path: str = Field(...,
                      description="The relative path of the file in the repository")
    status: str = Field(
        ..., description="File status: 'locked', 'unlocked', or 'checked_out_by_user'")
    locked_by: Optional[str] = Field(
        None, description="Username of the user who has the file locked")
    locked_at: Optional[str] = Field(
        None, description="ISO timestamp when the file was locked")
    checkout_message: Optional[str] = Field(
        "", description="Message explaining why the file is checked out")
    size: Optional[int] = Field(None, description="File size in bytes")
    modified_at: Optional[str] = Field(
        None, description="ISO timestamp of last modification")
    description: Optional[str] = Field(
        None, description="File description from metadata")
    revision: Optional[str] = Field(
        None, description="Current revision number (e.g., '1.5')")
    is_link: bool = Field(
        False, description="True if this is a linked/virtual file")
    master_file: Optional[str] = Field(
        None, description="The master file this link points to")
    group: Optional[str] = Field(
        None, description="Main group identifier (first 2 digits, e.g., '12XXXXX')")
    subgroup: Optional[str] = Field(
        None, description="Subgroup identifier (first 7 digits, e.g., '1234567')")


class CheckoutInfo(BaseModel):
    filename: str = Field(..., description="Name of the checked out file")
    path: str = Field(..., description="Repository path of the file")
    locked_by: str = Field(...,
                           description="User who has the file checked out")
    locked_at: str = Field(...,
                           description="ISO timestamp when checkout occurred")
    duration_seconds: float = Field(
        ..., description="How long the file has been checked out in seconds")


class DashboardStats(BaseModel):
    active_checkouts: List[CheckoutInfo] = Field(
        ..., description="List of currently checked out files")


class CheckoutRequest(BaseModel):
    user: str = Field(..., description="Username requesting the checkout")
    message: Optional[str] = Field("", description="Optional message describing why checking out (e.g., 'Updating dimensions')")


class AdminOverrideRequest(BaseModel):
    admin_user: str = Field(...,
                            description="Admin username performing the override")


class AdminDeleteRequest(BaseModel):
    admin_user: str = Field(...,
                            description="Admin username performing the deletion")


class SendMessageRequest(BaseModel):
    recipient: str = Field(...,
                           description="Username of the message recipient")
    message: str = Field(..., description="Message content to send")
    sender: str = Field(..., description="Username of the message sender")


class AckMessageRequest(BaseModel):
    message_id: str = Field(...,
                            description="Unique identifier of the message to acknowledge")
    user: str = Field(..., description="Username acknowledging the message")


class ConfigUpdateRequest(BaseModel):
    base_url: str = Field(
        alias="gitlab_url", description="GitLab instance URL (e.g., https://gitlab.example.com)")
    project_id: str = Field(..., description="GitLab project ID")
    username: str = Field(..., description="GitLab username")
    token: str = Field(..., description="GitLab personal access token")
    allow_insecure_ssl: bool = Field(
        False, description="Whether to allow insecure SSL connections")


class AdminRevertRequest(BaseModel):
    admin_user: str = Field(...,
                            description="Admin username performing the revert")
    commit_hash: str = Field(..., description="Git commit hash to revert")


class ActivityItem(BaseModel):
    event_type: str = Field(..., description="Type of activity")
    filename: str = Field(..., description="Name of the file involved")
    user: str = Field(..., description="Username who performed the action")
    timestamp: str = Field(..., description="ISO timestamp of the activity")
    commit_hash: str = Field(...,
                             description="Git commit hash associated with the activity")
    message: str = Field(...,
                         description="Commit message or activity description")
    revision: Optional[str] = Field(
        None, description="File revision if applicable")


class ActivityFeed(BaseModel):
    activities: List[ActivityItem] = Field(...,
                                           description="List of recent activities")


class StandardResponse(BaseModel):
    status: str = Field(...,
                        description="Response status: 'success' or 'error'")
    message: Optional[str] = Field(None, description="Human-readable message")


class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=8)
    gitlab_token: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    is_admin: bool


class ConfigSummary(BaseModel):
    gitlab_url: Optional[str] = Field(
        None, description="Configured GitLab URL")
    project_id: Optional[str] = Field(
        None, description="Configured GitLab project ID")
    username: Optional[str] = Field(
        None, description="Configured GitLab username")
    has_token: bool = Field(...,
                            description="Whether a GitLab token is configured")
    repo_path: Optional[str] = Field(None, description="Local repository path")
    is_admin: bool = Field(...,
                           description="Whether the current user has admin privileges")


class AdminRequest(BaseModel):
    admin_user: str


class UserList(BaseModel):
    users: List[str] = Field(...,
                             description="List of usernames from Git history")


class FileHistory(BaseModel):
    filename: str = Field(..., description="Name of the file")
    history: List[Dict[str, Any]
                  ] = Field(..., description="List of historical commits for this file")

# Add this class to backend/app/models/schemas.py


class InitialUserSetup(BaseModel):
    username: str
    gitlab_token: str
    new_password: str = Field(..., min_length=8)


# ===== Admin Configuration Schemas =====

class FileNamePattern(BaseModel):
    """Defines a customizable filename pattern with regex"""
    name: str = Field(..., description="Pattern name (e.g., 'Standard Pattern', 'Legacy Pattern')")
    description: str = Field(..., description="Human-readable description of the pattern")
    link_pattern: str = Field(..., description="Regex pattern for link files (without extension)")
    file_pattern: str = Field(..., description="Regex pattern for regular files (without extension)")
    max_stem_length: int = Field(15, description="Maximum length of filename stem (without extension)")
    allowed_extensions: List[str] = Field(
        default_factory=lambda: [".mcam", ".vnc", ".emcam", ".link"],
        description="Allowed file extensions for this pattern (e.g., ['.mcam', '.custom'])"
    )
    example_valid: List[str] = Field(..., description="Example filenames that match this pattern")
    example_invalid: List[str] = Field(..., description="Example filenames that don't match")


class RepositoryConfig(BaseModel):
    """Configuration for a single repository"""
    id: str = Field(..., description="Unique repository identifier (e.g., 'repo1', 'main')")
    name: str = Field(..., description="Display name for the repository")
    gitlab_url: str = Field(..., description="GitLab base URL")
    project_id: str = Field(..., description="GitLab project ID")
    branch: str = Field("main", description="Git branch to use")
    allowed_file_types: List[str] = Field(..., description="List of allowed file extensions (e.g., ['.mcam', '.vnc'])")
    filename_pattern_id: str = Field(..., description="ID of the filename pattern to use from patterns list")
    local_path: Optional[str] = Field(None, description="Local repository path (auto-generated if not set)")
    description: Optional[str] = Field(None, description="Repository description")


class UserRepositoryAccess(BaseModel):
    """Defines which repositories a user can access"""
    username: str = Field(..., description="Username")
    repository_ids: List[str] = Field(..., description="List of repository IDs the user can access")
    default_repository_id: Optional[str] = Field(None, description="User's default repository on login")


class RevisionHistorySettings(BaseModel):
    """Settings for revision-based history display"""
    display_mode: str = Field("range", description="Display mode: 'range' or 'list'")
    default_limit: int = Field(50, description="Default number of revisions to show")
    show_minor_revisions: bool = Field(True, description="Whether to show minor revisions in range")
    group_by_major: bool = Field(False, description="Group revisions by major version")


class PDMAdminConfig(BaseModel):
    """Complete PDM admin configuration stored in GitLab"""
    version: str = Field("1.0.0", description="Config schema version")

    # Filename patterns
    filename_patterns: List[FileNamePattern] = Field(..., description="Available filename patterns")

    # Repository configurations
    repositories: List[RepositoryConfig] = Field(..., description="Repository configurations")

    # User access control
    user_access: List[UserRepositoryAccess] = Field(default_factory=list, description="User repository access mappings")

    # Revision history settings
    revision_settings: RevisionHistorySettings = Field(
        default_factory=lambda: RevisionHistorySettings(),
        description="Revision history display settings"
    )

    # Polling settings
    polling_interval_seconds: int = Field(30, description="How often to poll GitLab for config updates (seconds)")

    # Last updated tracking
    last_updated_by: Optional[str] = Field(None, description="Username who last updated the config")
    last_updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")


class AdminConfigUpdateRequest(BaseModel):
    """Request to update admin configuration"""
    config: PDMAdminConfig = Field(..., description="Updated configuration")
    admin_user: str = Field(..., description="Admin username performing the update")


class RevisionRangeFilter(BaseModel):
    """Filter for revision-based history queries"""
    start_revision: Optional[str] = Field(None, description="Starting revision (e.g., '1.0')")
    end_revision: Optional[str] = Field(None, description="Ending revision (e.g., '20.5')")
    limit: int = Field(50, description="Maximum number of revisions to return")


class FileHistoryRevision(BaseModel):
    """Single revision entry in file history"""
    revision: str = Field(..., description="Revision number (e.g., '1.5')")
    commit_hash: str = Field(..., description="Git commit hash")
    author: str = Field(..., description="Author username")
    timestamp: str = Field(..., description="ISO timestamp")
    message: str = Field(..., description="Commit message")


class FileHistoryWithRevisions(BaseModel):
    """File history with revision range support"""
    filename: str = Field(..., description="Name of the file")
    total_revisions: int = Field(..., description="Total number of revisions")
    revision_range: str = Field(..., description="Revision range (e.g., '1.0 - 20.5')")
    revisions: List[FileHistoryRevision] = Field(..., description="List of revisions")
    filtered: bool = Field(False, description="Whether results are filtered by range")
