from fastapi import APIRouter, Depends, HTTPException, status

# Import our schemas, dependencies, and services
from app.models import schemas
from app.api.dependencies import (
    get_git_repo,
    get_lock_manager,
    get_current_admin_user
)
from app.services.git_service import GitRepository
from app.services.lock_service import MetadataManager
import logging

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

# We will add the other admin endpoints (revert, reset repo, etc.) here later.
