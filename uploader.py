"""
uploader.py — GoFile API client.
Handles server selection, file upload, and direct link generation.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from config import cfg

logger = logging.getLogger(__name__)

GOFILE_API = "https://api.gofile.io"
UPLOAD_TIMEOUT = 600.0  # 10 minutes for large files


@dataclass
class UploadResult:
    success: bool
    link: str = ""
    direct_link: str = ""
    file_id: str = ""
    filename: str = ""
    error: str = ""


def _build_upload_headers() -> dict:
    """Build headers for GoFile upload."""
    headers = {"Accept": "application/json"}
    if cfg.gofile_token:
        headers["Authorization"] = f"Bearer {cfg.gofile_token}"
    return headers


async def get_server() -> str:
    """Get the best available GoFile server for upload."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{GOFILE_API}/servers")
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"GoFile server error: {data}")

    server = data["data"]["server"]
    logger.info("GoFile server selected: %s", server)
    return server


async def upload_file(
    file_path: str,
    filename: str,
    progress_callback=None,
) -> UploadResult:
    """
    Upload a file to GoFile.

    Args:
        file_path: Local path to the file.
        filename: Display name for the file.
        progress_callback: Optional async callback(bytes_uploaded, total_bytes).

    Returns:
        UploadResult with link info.
    """
    try:
        server = await get_server()
    except Exception as exc:
        return UploadResult(
            success=False,
            error=f"Failed to get GoFile server: {exc}",
        )

    upload_url = f"https://{server}.gofile.io/contents/uploadfile"
    headers = _build_upload_headers()

    file_size = 0
    try:
        file_size = _get_file_size(file_path)
    except OSError:
        pass

    try:
        async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
            # Use chunked upload for progress tracking
            if progress_callback and file_size > 0:
                result = await _upload_with_progress(
                    client, upload_url, file_path, filename, headers,
                    file_size, progress_callback,
                )
            else:
                result = await _upload_simple(
                    client, upload_url, file_path, filename, headers,
                )
    except httpx.TimeoutException:
        return UploadResult(
            success=False,
            error="Upload timed out. Try a smaller file.",
        )
    except Exception as exc:
        logger.exception("GoFile upload error")
        return UploadResult(success=False, error=str(exc))

    return result


async def _upload_simple(
    client: httpx.AsyncClient,
    url: str,
    file_path: str,
    filename: str,
    headers: dict,
) -> UploadResult:
    """Simple upload without progress tracking."""
    with open(file_path, "rb") as f:
        resp = await client.post(
            url,
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
    url: str,
    file_path: str,
    filename: str,
    headers: dict,
    total_size: int,
    progress_callback,
) -> UploadResult:
    """Upload with progress tracking via custom streaming."""
    import asyncio

    # Read file in chunks and track progress
    chunk_size = 1024 * 1024  # 1 MB chunks
    uploaded = 0

    async def file_generator():
        nonlocal uploaded
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                uploaded += len(chunk)
                # Schedule progress callback (fire and forget)
                if progress_callback:
                    asyncio.ensure_future(
                        progress_callback(uploaded, total_size)
                    )
                yield chunk

    # Build multipart request manually for streaming
    boundary = "----LinkrBotBoundary" + _rand_str(16)

    async def body_generator():
        yield f"--{boundary}\r\n".encode()
        yield (
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n".encode()
        )
        async for chunk in file_generator():
            yield chunk
        yield f"\r\n--{boundary}--\r\n".encode()

    content_type = f"multipart/form-data; boundary={boundary}"

    resp = await client.post(
        url,
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
    """Parse GoFile upload response."""
    if data.get("status") != "ok":
        return UploadResult(
            success=False,
            error=data.get("error", "Unknown GoFile error"),
        )

    file_data = data.get("data", {})
    file_id = file_data.get("fileId", "")
    download_page = file_data.get("downloadPage", "")
    parent_folder = file_data.get("parentFolder", "")

    # If no direct fileId, try the folder as the link
    link = download_page or f"https://gofile.io/d/{parent_folder}"

    # Extract filename from response if available
    name = ""
    if "files" in file_data and isinstance(file_data["files"], dict):
        for fid, finfo in file_data["files"].items():
            name = finfo.get("name", "")
            break

    return UploadResult(
        success=True,
        link=link,
        file_id=file_id,
        filename=name,
    )


async def get_direct_link(file_id: str) -> Optional[str]:
    """
    Get a direct download link for a file.
    Requires GOFILE_TOKEN to be set.
    """
    if not cfg.gofile_token:
        return None

    url = f"{GOFILE_API}/contents/{file_id}/directlinks"
    headers = {"Authorization": f"Bearer {cfg.gofile_token}"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Failed to get direct link: %s", exc)
        return None

    if data.get("status") != "ok":
        return None

    # Navigate response to find the link
    files_data = data.get("data", {})
    if isinstance(files_data, dict):
        # Usually: {"data": {"link": "https://..."}}
        if "link" in files_data:
            return files_data["link"]
        # Or nested: {"data": {"fileId": {"link": "..."}}}
        for key, value in files_data.items():
            if isinstance(value, dict) and "link" in value:
                return value["link"]

    return None


def _get_file_size(path: str) -> int:
    import os
    return os.path.getsize(path)


def _rand_str(n: int) -> str:
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))