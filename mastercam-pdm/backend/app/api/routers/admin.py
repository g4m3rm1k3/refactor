from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import JSONResponse, FileResponse

# Import our schemas, dependencies, and services
from app.models import schemas
from app.api.dependencies import (
    get_git_repo,
    get_lock_manager,
    get_current_admin_user,
    get_user_auth,
    get_config_manager
)
from app.services.git_service import GitRepository
from app.services.lock_service import MetadataManager
from app.core.security import UserAuth
from app.core.config import ConfigManager
import logging
import shutil
import stat
import psutil
from pathlib import Path
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",  # All routes here will start with /admin
    tags=["Administration"],
    # IMPORTANT: This protects ALL routes in this file
    dependencies=[Depends(get_current_admin_user)]
)


@router.post("/files/{filename}/override", response_model=schemas.StandardResponse)
async def admin_override_lock(
    filename: str,
    request: schemas.AdminOverrideRequest,
    # We can still get the user info if needed
    admin_user: dict = Depends(get_current_admin_user),
    git_repo: GitRepository = Depends(get_git_repo),
    lock_manager: MetadataManager = Depends(get_lock_manager)
):
    """(Admin) Forcibly removes a lock from a file."""
    if request.admin_user != admin_user.get('sub'):
        raise HTTPException(status_code=403, detail="Admin username mismatch.")

    file_path = git_repo.find_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found.")

    lock_info = lock_manager.get_lock_info(file_path)
    if not lock_info:
        return {"status": "success", "message": "File was already unlocked."}

    lock_file_path = lock_manager._get_lock_file_path(file_path)
    relative_lock_path = str(lock_file_path.relative_to(git_repo.repo_path))

    lock_manager.release_lock(file_path)

    success = git_repo.commit_and_push(
        file_paths=[relative_lock_path],
        message=f"ADMIN OVERRIDE: Unlock {filename} by {request.admin_user}",
        author_name=request.admin_user
    )

    if not success:
        # Best effort to restore the lock if push fails
        lock_manager.create_lock(file_path, lock_info['user'], force=True)
        raise HTTPException(
            status_code=500, detail="Failed to commit lock override.")

    return {"status": "success", "message": f"Lock on '{filename}' has been overridden."}


@router.delete("/files/{filename}/delete", response_model=schemas.StandardResponse)
async def admin_delete_file(
    filename: str,
    admin_user: dict = Depends(get_current_admin_user),
    git_repo: GitRepository = Depends(get_git_repo),
    lock_manager: MetadataManager = Depends(get_lock_manager)
):
    """(Admin) Permanently deletes a file and its metadata."""
    file_path = git_repo.find_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found.")

    if lock_manager.get_lock_info(file_path):
        raise HTTPException(
            status_code=409, detail="Cannot delete a file that is currently checked out.")

    files_to_remove = git_repo.delete_file_and_metadata(file_path)

    success = git_repo.commit_and_push(
        file_paths=files_to_remove,
        message=f"ADMIN DELETE: Remove {filename} by {admin_user.get('sub')}",
        author_name=admin_user.get('sub')
    )

    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to commit file deletion.")

    return {"status": "success", "message": f"File '{filename}' permanently deleted."}


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users")
async def list_users(
    admin_user: dict = Depends(get_current_admin_user),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    (Admin) List all users in the system.

    Returns:
        Dictionary of users with their info (no password hashes)
    """
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )

    users = auth_service.list_users()
    logger.info(f"Admin {admin_user.get('sub')} listed users")
    return {"status": "success", "users": list(users.values())}


@router.post("/users/create", response_model=schemas.StandardResponse)
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    admin_user: dict = Depends(get_current_admin_user),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    (Admin) Create a new user account.

    Args:
        username: New username
        password: Initial password for the user
        is_admin: Whether the user should have admin privileges
        admin_user: Current admin user (from dependency)
        auth_service: Authentication service (from dependency)

    Returns:
        Success message
    """
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )

    # Check if user already exists
    existing_users = auth_service._load_users()
    if username in existing_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{username}' already exists"
        )

    # Create the user
    success = auth_service.create_user_password(username, password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    logger.info(f"Admin {admin_user.get('sub')} created user: {username}")
    return {
        "status": "success",
        "message": f"User '{username}' created successfully"
    }


@router.post("/users/{username}/reset-password", response_model=schemas.StandardResponse)
async def admin_reset_user_password(
    username: str,
    new_password: str = Form(...),
    admin_user: dict = Depends(get_current_admin_user),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    (Admin) Reset a user's password without requiring reset token.

    Args:
        username: User whose password to reset
        new_password: New password to set
        admin_user: Current admin user
        auth_service: Authentication service

    Returns:
        Success message
    """
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )

    # Check if user exists
    existing_users = auth_service._load_users()
    if username not in existing_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    # Update the password
    success = auth_service.create_user_password(username, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

    logger.info(f"Admin {admin_user.get('sub')} reset password for user: {username}")
    return {
        "status": "success",
        "message": f"Password reset successfully for '{username}'"
    }


@router.delete("/users/{username}", response_model=schemas.StandardResponse)
async def delete_user(
    username: str,
    admin_user: dict = Depends(get_current_admin_user),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    (Admin) Delete a user from the system.

    Args:
        username: User to delete
        admin_user: Current admin user
        auth_service: Authentication service

    Returns:
        Success message

    Raises:
        400: If trying to delete yourself or user doesn't exist
    """
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )

    # Prevent admin from deleting themselves
    if username == admin_user.get('sub'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    # Delete the user
    success = auth_service.delete_user(username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    logger.info(f"Admin {admin_user.get('sub')} deleted user: {username}")
    return {
        "status": "success",
        "message": f"User '{username}' deleted successfully"
    }


# ============================================================================
# REPOSITORY MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/reset_repository", response_model=schemas.StandardResponse)
async def reset_repository(
    request: Request,
    admin_user: dict = Depends(get_current_admin_user),
    git_repo: GitRepository = Depends(get_git_repo),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    (Admin) Reset the local repository to match GitLab exactly.

    This is a destructive operation that:
    1. Terminates all Git processes
    2. Deletes the local repository directory
    3. Reinitializes and clones from GitLab

    WARNING: All local changes will be lost!

    Returns:
        Success message
    """
    if not git_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not initialized"
        )

    repo_path = git_repo.repo_path
    logger.info(f"Admin {admin_user.get('sub')} resetting repository at {repo_path}")

    try:
        # Step 1: Terminate any Git processes that might have file handles open
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in ['git.exe', 'git-lfs.exe', 'git', 'git-lfs']:
                    proc.terminate()
                    proc.wait(timeout=3)
                    logger.info(f"Terminated process {proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                pass

        # Step 2: Delete the repository directory
        def handle_remove_readonly(func, path, exc_info):
            """Handle read-only files during deletion"""
            try:
                Path(path).chmod(stat.S_IWRITE)
                func(path)
            except Exception as chmod_error:
                logger.error(f"Failed to handle readonly file {path}: {chmod_error}")

        # Try multiple times in case of file locks
        last_error = None
        for attempt in range(3):
            try:
                if repo_path.exists():
                    shutil.rmtree(repo_path, onerror=handle_remove_readonly)
                    logger.info(f"Deleted repository directory: {repo_path}")
                break
            except Exception as delete_error:
                last_error = delete_error
                logger.warning(f"Retry {attempt+1}/3 deleting repo: {delete_error}")
                import time
                time.sleep(1)
        else:
            raise Exception(f"Could not delete repository after 3 attempts: {last_error}")

        # Step 3: Reinitialize the repository
        # The GitRepository class will clone from GitLab again
        git_repo._init_repo()
        logger.info("Repository reset and reinitialized successfully")

        # Update the app state to reflect the reset
        request.app.state.git_repo = git_repo

        return {
            "status": "success",
            "message": "Repository has been reset and synchronized with GitLab"
        }

    except Exception as e:
        logger.error(f"Repository reset failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository reset failed: {str(e)}"
        )


@router.post("/create_backup", response_model=schemas.StandardResponse)
async def create_backup(
    admin_user: dict = Depends(get_current_admin_user),
    git_repo: GitRepository = Depends(get_git_repo)
):
    """
    (Admin) Create a manual backup of the entire repository.

    Creates a timestamped copy of the repository in ~/MastercamBackups/

    Returns:
        Success message with backup path
    """
    if not git_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not initialized"
        )

    try:
        # Create backup directory in user's home
        backup_dir = Path.home() / 'MastercamBackups'
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'mastercam_backup_{timestamp}'
        backup_path = backup_dir / backup_name

        # Copy the entire repository
        logger.info(f"Creating backup at {backup_path}")
        shutil.copytree(git_repo.repo_path, backup_path)

        logger.info(f"Backup created successfully by {admin_user.get('sub')}")
        return {
            "status": "success",
            "message": f"Backup created successfully",
            "backup_path": str(backup_path)
        }

    except Exception as e:
        logger.error(f"Backup creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(e)}"
        )


@router.post("/cleanup_lfs", response_model=schemas.StandardResponse)
async def cleanup_lfs(
    admin_user: dict = Depends(get_current_admin_user),
    git_repo: GitRepository = Depends(get_git_repo)
):
    """
    (Admin) Clean up old Git LFS files to free disk space.

    This runs `git lfs prune` to remove unreferenced LFS objects.

    Returns:
        Success message with cleanup details
    """
    if not git_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not initialized"
        )

    try:
        logger.info(f"Admin {admin_user.get('sub')} initiating LFS cleanup")

        # Run git lfs prune command
        result = subprocess.run(
            ['git', 'lfs', 'prune'],
            cwd=git_repo.repo_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise Exception(f"LFS prune failed: {result.stderr}")

        logger.info("LFS cleanup completed successfully")
        return {
            "status": "success",
            "message": "LFS cleanup completed successfully",
            "output": result.stdout
        }

    except subprocess.TimeoutExpired:
        logger.error("LFS cleanup timed out after 5 minutes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LFS cleanup timed out"
        )
    except Exception as e:
        logger.error(f"LFS cleanup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LFS cleanup failed: {str(e)}"
        )


@router.post("/export_repository")
async def export_repository(
    admin_user: dict = Depends(get_current_admin_user),
    git_repo: GitRepository = Depends(get_git_repo)
):
    """
    (Admin) Export the repository as a ZIP file.

    Creates a ZIP archive of the repository (excluding .git folder)
    and returns it as a downloadable file.

    Returns:
        ZIP file download
    """
    if not git_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Repository not initialized"
        )

    try:
        import tempfile
        import zipfile

        logger.info(f"Admin {admin_user.get('sub')} exporting repository")

        # Create temporary ZIP file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"mastercam_export_{timestamp}.zip"
        temp_zip_path = Path(tempfile.gettempdir()) / zip_filename

        # Create ZIP archive
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in git_repo.repo_path.rglob('*'):
                # Skip .git directory
                if '.git' in file_path.parts:
                    continue

                if file_path.is_file():
                    arcname = file_path.relative_to(git_repo.repo_path)
                    zipf.write(file_path, arcname)

        logger.info(f"Repository exported to {temp_zip_path}")

        # Return the ZIP file as a download
        return FileResponse(
            path=temp_zip_path,
            filename=zip_filename,
            media_type='application/zip'
        )

    except Exception as e:
        logger.error(f"Repository export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository export failed: {str(e)}"
        )
