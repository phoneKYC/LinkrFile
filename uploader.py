"""
uploader.py — GoFile API client (v2 — 2025 API).
Handles file upload to the global endpoint and direct link generation.

API Docs: https://gofile.io/api

Key changes from old API:
  - No more /servers endpoint
  - Single global upload: POST https://upload.gofile.io/uploadfile
  - Auth header: Bearer token (guest accounts auto-created if no token)
  - Direct links require Premium account
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

from config import cfg

logger = logging.getLogger(__name__)

UPLOAD_URL = "https://upload.gofile.io/uploadfile"
GOFILE_API = "https://api.gofile.io"
UPLOAD_TIMEOUT = 600.0  # 10 minutes for large files

# Reusable guest token across uploads (set after first upload)
_guest_token: Optional[str] = None


@dataclass
class UploadResult:
    success: bool
    link: str = ""
    direct_link: str = ""
    file_id: str = ""
    folder_id: str = ""
    filename: str = ""
    guest_token: str = ""  # returned so caller can persist it
    error: str = ""


def _build_headers() -> dict:
    """Build headers for GoFile API requests."""
    headers = {"Accept": "application/json"}
    token = cfg.gofile_token or _guest_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def upload_file(
    file_path: str,
    filename: str,
    progress_callback=None,
) -> UploadResult:
    """
    Upload a file to GoFile using the global upload endpoint.

    - If GOFILE_TOKEN is set, uses that account.
    - Otherwise uses/reuses a guest token (auto-created on first upload).
    - Without folderId, GoFile creates a new public folder each time.

    Args:
        file_path: Local path to the file.
        filename: Display name for the file.
        progress_callback: Optional callback(bytes_uploaded, total_bytes).

    Returns:
        UploadResult with link info.
    """
    global _guest_token

    headers = _build_headers()
    file_size = 0
    try:
        file_size = os.path.getsize(file_path)
    except OSError:
        pass

    try:
        async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
            if progress_callback and file_size > 0:
                result = await _upload_with_progress(
                    client, file_path, filename, headers,
                    file_size, progress_callback,
                )
            else:
                result = await _upload_simple(
                    client, file_path, filename, headers,
                )
    except httpx.TimeoutException:
        return UploadResult(
            success=False,
            error="Upload timed out. Try a smaller file.",
        )
    except Exception as exc:
        logger.exception("GoFile upload error")
        return UploadResult(success=False, error=str(exc))

    # Save guest token for reuse if returned
    if result.success and result.guest_token and not cfg.gofile_token:
        _guest_token = result.guest_token
        logger.info("Guest token saved for reuse")

    return result


async def _upload_simple(
    client: httpx.AsyncClient,
    file_path: str,
    filename: str,
    headers: dict,
) -> UploadResult:
    """Simple upload without progress tracking."""
    with open(file_path, "rb") as f:
        resp = await client.post(
            UPLOAD_URL,
            files={"file": (filename, f)},
            headers=headers,
        )

    if resp.status_code != 200:
        return UploadResult(
            success=False,
            error=f"GoFile returned HTTP {resp.status_code}",
        )

    return _parse_upload_response(resp.json())


async def _upload_with_progress(
    client: httpx.AsyncClient,
    file_path: str,
    filename: str,
    headers: dict,
    total_size: int,
    progress_callback,
) -> UploadResult:
    """Upload with progress tracking via custom multipart streaming."""
    chunk_size = 1024 * 1024  # 1 MB chunks
    uploaded = 0

    def file_generator():
        nonlocal uploaded
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                uploaded += len(chunk)
                if progress_callback:
                    progress_callback(uploaded, total_size)
                yield chunk

    boundary = "----LinkrBotBoundary" + _rand_str(16)

    async def body_generator():
        yield f"--{boundary}\r\n".encode()
        yield (
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n".encode()
        )
        for chunk in file_generator():
            yield chunk
        yield f"\r\n--{boundary}--\r\n".encode()

    content_type = f"multipart/form-data; boundary={boundary}"

    resp = await client.post(
        UPLOAD_URL,
        content=body_generator(),
        headers={**headers, "Content-Type": content_type},
    )

    if resp.status_code != 200:
        return UploadResult(
            success=False,
            error=f"GoFile returned HTTP {resp.status_code}",
        )

    return _parse_upload_response(resp.json())


def _parse_upload_response(data: dict) -> UploadResult:
    """Parse GoFile upload response (2025 format).

    Expected successful response:
    {
        "status": "ok",
        "data": {
            "fileId": "...",
            "fileName": "...",
            "parentFolder": "...",
            "downloadPage": "https://gofile.io/d/..."
        }
    }

    Or with guest token:
    {
        "status": "ok",
        "data": {
            "guestToken": "...",
            "fileId": "...",
            ...
        }
    }
    """
    if data.get("status") != "ok":
        error_msg = data.get("error", "Unknown GoFile error")
        # Some errors come as a list
        if isinstance(error_msg, list):
            error_msg = " | ".join(error_msg)
        return UploadResult(success=False, error=error_msg)

    file_data = data.get("data", {})

    file_id = file_data.get("fileId", "")
    download_page = file_data.get("downloadPage", "")
    parent_folder = file_data.get("parentFolder", "")
    guest_token = file_data.get("guestToken", "")
    name = file_data.get("fileName", "")

    # Build the best available link
    link = download_page
    if not link and parent_folder:
        link = f"https://gofile.io/d/{parent_folder}"

    if not link:
        return UploadResult(
            success=False,
            error="GoFile returned no download link",
        )

    return UploadResult(
        success=True,
        link=link,
        file_id=file_id,
        folder_id=parent_folder,
        filename=name,
        guest_token=guest_token,
    )


async def get_direct_link(content_id: str) -> Optional[str]:
    """
    Create a direct download link for a file or folder.
    Requires a Premium GoFile account (GOFILE_TOKEN must be set).

    POST /contents/{contentId}/directlinks
    """
    if not cfg.gofile_token:
        logger.debug("No GoFile token — direct links require Premium")
        return None

    url = f"{GOFILE_API}/contents/{content_id}/directlinks"
    headers = {"Authorization": f"Bearer {cfg.gofile_token}"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Failed to create direct link: %s", exc)
        return None

    if data.get("status") != "ok":
        logger.warning("Direct link creation failed: %s", data)
        return None

    # Response: {"data": {"link": "https://..."}}
    # Or with restrictions: {"data": {"directLinkId": "...", "link": "..."}}
    result_data = data.get("data", {})

    if isinstance(result_data, dict) and "link" in result_data:
        return result_data["link"]

    # Nested format
    for key, value in result_data.items():
        if isinstance(value, dict) and "link" in value:
            return value["link"]

    return None


def _rand_str(n: int) -> str:
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))