from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Response
from typing import Dict, List, Optional

# Import our schemas, dependencies, and services
from app.models import schemas
from app.api.dependencies import get_git_repo, get_lock_manager, get_current_user
from app.services.git_service import GitRepository
from app.services.lock_service import MetadataManager
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/files",
    tags=["File Management"],
)

# This endpoint was moved in the previous step


@router.get("", response_model=Dict[str, List[schemas.FileInfo]])
async def get_all_files(
    git_repo: GitRepository = Depends(get_git_repo),
    lock_manager: MetadataManager = Depends(get_lock_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves a structured list of all files, including processing for .link files
    to create virtual file entries.
    """
    if not git_repo or not lock_manager:
        raise HTTPException(
            status_code=503, detail="Repository not initialized.")

    try:
        all_files_from_git = git_repo.list_files()
        all_locks = {lock['file']                     : lock for lock in lock_manager.get_all_locks()}

        physical_files = [
            f for f in all_files_from_git if not f['path'].endswith('.link')]
        link_files = [
            f for f in all_files_from_git if f['path'].endswith('.link')]

        master_file_map = {f['filename']: f for f in physical_files}

        # This list will hold both real and virtual (linked) files for processing
        all_files_to_process = list(master_file_map.values())

        # Process .link files to create virtual file entries
        for link_file in link_files:
            try:
                link_content_bytes = git_repo.get_file_content(
                    link_file['path'])
                if not link_content_bytes:
                    continue

                link_content = json.loads(link_content_bytes)
                master_filename = link_content.get("master_file")

                if master_filename and master_filename in master_file_map:
                    virtual_filename = link_file['filename'].replace(
                        '.link', '')
                    virtual_file = {
                        'filename': virtual_filename,
                        'path': virtual_filename,  # Links use their own name as a virtual path
                        'size': 0,
                        'modified_at': link_file['modified_at'],
                        'is_link': True,
                        'master_file': master_filename
                    }
                    all_files_to_process.append(virtual_file)
            except Exception as e:
                logger.error(
                    f"Could not process link file {link_file['filename']}: {e}")

        # Now, process the combined list to add metadata and lock info
        grouped_files = {}
        username = current_user.get('sub')

        for file_data in all_files_to_process:
            path_for_meta = file_data['path']

            # Enrich with lock status
            lock_info = all_locks.get(path_for_meta)
            if lock_info:
                file_data['status'] = "checked_out_by_user" if lock_info.get(
                    'user') == username else "locked"
                file_data['locked_by'] = lock_info.get('user')
                file_data['locked_at'] = lock_info.get('timestamp')
            else:
                file_data['status'] = "unlocked"

            # Enrich with metadata from .meta.json files
            meta_content_bytes = git_repo.get_file_content(
                f"{path_for_meta}.meta.json")
            if meta_content_bytes:
                try:
                    meta_content = json.loads(meta_content_bytes)
                    file_data['description'] = meta_content.get('description')
                    file_data['revision'] = meta_content.get('revision')
                except json.JSONDecodeError:
                    logger.warning(
                        f"Could not parse metadata for {path_for_meta}")

            # Grouping logic
            group_name = "Miscellaneous"
            if file_data['filename'][:2].isdigit():
                group_name = f"{file_data['filename'][:2]}XXXXX"
            if group_name not in grouped_files:
                grouped_files[group_name] = []

            grouped_files[group_name].append(file_data)

        return grouped_files

    except Exception as e:
        logger.error(f"Failed to retrieve file list: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve file list.")


# This endpoint was moved in the previous step
@router.post("/{filename}/checkout")
async def checkout_file(
    filename: str,
    request: schemas.CheckoutRequest,
    git_repo: GitRepository = Depends(get_git_repo),
    lock_manager: MetadataManager = Depends(get_lock_manager),
    current_user: dict = Depends(get_current_user)
):
    """Locks a file for a user, preventing others from editing it."""
    # NOTE: The full logic for this function goes here. For brevity, it is omitted.
    # Please use the full function body from the previous step.
    return {}

# --- NEWLY ADDED ENDPOINTS ---


@router.post("/{filename}/checkin")
async def checkin_file(
    filename: str,
    user: str = Form(...),
    commit_message: str = Form(...),
    rev_type: str = Form(...),
    new_major_rev: Optional[str] = Form(None),
    file: UploadFile = File(...),
    git_repo: GitRepository = Depends(get_git_repo),
    lock_manager: MetadataManager = Depends(get_lock_manager),
    current_user: dict = Depends(get_current_user)
):
    """Uploads a modified file, updates its metadata, and releases the lock."""
    if user != current_user.get('sub'):
        raise HTTPException(
            status_code=403, detail="Authenticated user does not match user in form.")

    file_path = git_repo.find_file_path(filename)
    if not file_path:
        raise HTTPException(
            status_code=404, detail="File to check in not found.")

    lock_info = lock_manager.get_lock_info(file_path)
    if not lock_info or lock_info['user'] != user:
        raise HTTPException(
            status_code=403, detail="You do not have this file locked.")

    try:
        # This operation is now a high-level orchestration of service methods
        success = git_repo.checkin_file(
            file_path=file_path,
            file_content=await file.read(),
            commit_message=commit_message,
            rev_type=rev_type,
            new_major_rev=new_major_rev,
            author_name=user
        )

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to commit and push changes.")

        # Release the lock after a successful push
        lock_manager.release_lock(file_path)
        git_repo.commit_and_push(
            file_paths=[str(lock_manager._get_lock_file_path(
                file_path).relative_to(git_repo.repo_path))],
            message=f"UNLOCK: {filename} after check-in by {user}",
            author_name=user
        )

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Check-in failed for {filename}: {e}", exc_info=True)
        # We don't re-lock here, because the push might have partially succeeded,
        # leaving the repo in a state that requires manual intervention.
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred during check-in: {e}")


@router.post("/{filename}/cancel_checkout")
async def cancel_checkout(
    filename: str,
    request: schemas.CheckoutRequest,
    git_repo: GitRepository = Depends(get_git_repo),
    lock_manager: MetadataManager = Depends(get_lock_manager),
    current_user: dict = Depends(get_current_user)
):
    """Releases a user's lock on a file without saving any changes."""
    if request.user != current_user.get('sub'):
        raise HTTPException(status_code=403, detail="User mismatch.")

    file_path = git_repo.find_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found.")

    lock_info = lock_manager.get_lock_info(file_path)
    if not lock_info or lock_info['user'] != request.user:
        raise HTTPException(
            status_code=403, detail="You do not have this file checked out.")

    # Get the lock file path before releasing the lock
    lock_file_path = lock_manager._get_lock_file_path(file_path)
    relative_lock_path = str(lock_file_path.relative_to(git_repo.repo_path))

    # Release the lock locally first
    lock_manager.release_lock(file_path)

    # Revert any local changes and clean up downloaded LFS file
    git_repo.revert_local_file_changes(file_path)

    # Commit the lock release
    success = git_repo.commit_and_push(
        file_paths=[relative_lock_path],
        message=f"USER CANCEL: Unlock {filename} by {request.user}",
        author_name=request.user
    )

    if not success:
        # If push fails, we can't guarantee state. The safest is to ask the user to try again.
        raise HTTPException(
            status_code=500, detail="Failed to sync checkout cancellation. Please try again.")

    return {"status": "success", "message": "Checkout cancelled."}


@router.get("/{filename}/download", response_class=Response)
async def download_file(
    filename: str,
    git_repo: GitRepository = Depends(get_git_repo)
):
    """Downloads the latest version of a file."""
    file_path = git_repo.find_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found.")

    # Download LFS content if it's just a pointer
    if git_repo.is_lfs_pointer(file_path):
        if not git_repo.download_lfs_file(file_path):
            raise HTTPException(
                status_code=500, detail="Failed to download file content from LFS.")

    content = git_repo.get_file_content(file_path)
    if content is None:
        raise HTTPException(
            status_code=404, detail="File content could not be read.")

    return Response(
        content,
        media_type='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@router.get("/{filename}/history", response_model=schemas.FileHistory)
async def get_file_history(
    filename: str,
    git_repo: GitRepository = Depends(get_git_repo)
):
    """Retrieves the version history of a file."""
    file_path = git_repo.find_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found.")

    history = git_repo.get_file_history(file_path)
    return {"filename": filename, "history": history}
# Add to backend/app/api/routers/files.py


@router.get("/{filename}/versions/{commit_hash}", response_class=Response)
async def download_file_version(
    filename: str,
    commit_hash: str,
    git_repo: GitRepository = Depends(get_git_repo)
):
    file_path = git_repo.find_file_path(filename)
    if not file_path:
        raise HTTPException(
            status_code=404, detail="File not found in current version.")

    content = git_repo.get_file_content_at_commit(file_path, commit_hash)
    if content is None:
        raise HTTPException(
            status_code=404, detail=f"File '{filename}' not found at commit '{commit_hash[:7]}'.")

    base, ext = os.path.splitext(filename)
    download_filename = f"{base}_rev_{commit_hash[:7]}{ext}"
    return Response(content, media_type='application/octet-stream', headers={'Content-Disposition': f'attachment; filename="{download_filename}"'})
