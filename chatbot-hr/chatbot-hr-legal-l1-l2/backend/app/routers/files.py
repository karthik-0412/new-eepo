from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import List
from ..storage.azure_blob import blob_storage
import logging
from starlette.concurrency import run_in_threadpool
import os

# read container names from environment with sensible defaults
DEFAULT_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER', 'uploads')
DOMAIN_CONTAINER_MAP = {
    'auto': DEFAULT_CONTAINER,
    'hr': os.getenv('AZURE_CONTAINER_HR', 'hrdocs'),
    'legal': os.getenv('AZURE_CONTAINER_LEGAL', 'legaldocs'),
    'l1': os.getenv('AZURE_CONTAINER_L1', 'l1docs'),
    'l2': os.getenv('AZURE_CONTAINER_L2', 'l2docs'),
}

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), domain: str = Form("auto")):
    """
    Upload a file to Azure Blob Storage.
    
    The file will be stored with a timestamp-prefixed name to ensure uniqueness.
    Returns a dict containing the blob name, URL (with SAS token), and metadata.
    """
    try:
        content = await file.read()
        # Determine container based on domain (domain comes from multipart form)
        container = DOMAIN_CONTAINER_MAP.get(domain.lower()) if domain else None
        if not container:
            container = DEFAULT_CONTAINER

        logging.info(f"Uploading file '{file.filename}' to container '{container}' (domain='{domain}')")

        # call sync upload in threadpool (pass container name)
        result = await run_in_threadpool(
            blob_storage.upload_file,
            content,
            file.filename,
            file.content_type,
            container,
        )
        return result
    except Exception as e:
        logging.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_files(max_results: int = 100, domain: str = "auto") -> List[dict]:
    """
    List files in the blob storage container.
    Returns a list of dicts containing file metadata and SAS URLs.
    """
    try:
        container = DOMAIN_CONTAINER_MAP.get(domain.lower()) if domain else None
        if not container:
            container = DEFAULT_CONTAINER

        logging.info(f"Listing files from container '{container}' (domain='{domain}')")

        files = await run_in_threadpool(blob_storage.list_files, max_results, container)
        return files
    except Exception as e:
        logging.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))