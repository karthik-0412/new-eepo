from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
from ..storage.azure_blob import blob_storage
import logging
from starlette.concurrency import run_in_threadpool

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to Azure Blob Storage.
    
    The file will be stored with a timestamp-prefixed name to ensure uniqueness.
    Returns a dict containing the blob name, URL (with SAS token), and metadata.
    """
    try:
        content = await file.read()
        # call sync upload in threadpool
        result = await run_in_threadpool(
            blob_storage.upload_file,
            content,
            file.filename,
            file.content_type,
        )
        return result
    except Exception as e:
        logging.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_files(max_results: int = 100) -> List[dict]:
    """
    List files in the blob storage container.
    Returns a list of dicts containing file metadata and SAS URLs.
    """
    try:
        files = await run_in_threadpool(blob_storage.list_files, max_results)
        return files
    except Exception as e:
        logging.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))