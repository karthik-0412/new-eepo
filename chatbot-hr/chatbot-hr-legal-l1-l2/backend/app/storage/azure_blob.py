import os
from typing import Optional, List
from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient,
    BlobClient,
    ContainerClient,
    generate_blob_sas,
    BlobSasPermissions,
    ContentSettings,
)
from azure.core.exceptions import ResourceExistsError
from dotenv import load_dotenv

load_dotenv()

class AzureBlobStorage:
    def __init__(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING not found in environment variables")
        
        self.service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "uploads")
        
        # Create container if it doesn't exist
        try:
            self.service_client.create_container(self.container_name)
        except ResourceExistsError:
            pass  # Container already exists
        # Try to extract account key from connection string for SAS generation
        self.account_name = None
        self.account_key = None
        parts = [p for p in connection_string.split(';') if p]
        for p in parts:
            if p.startswith('AccountName='):
                self.account_name = p.split('=', 1)[1]
            if p.startswith('AccountKey='):
                self.account_key = p.split('=', 1)[1]
        if not self.account_name:
            # fallback to service client
            try:
                self.account_name = self.service_client.account_name
            except Exception:
                self.account_name = None
    
    def upload_file(self, file_content: bytes, filename: str, content_type: Optional[str] = None, container_name: Optional[str] = None) -> dict:
        """
        Upload a file to Azure Blob Storage.
        
        Args:
            file_content: The file content as bytes
            filename: Original filename
            content_type: Optional MIME type
        
        Returns:
            dict with blob_name, url, and other metadata
        """
        # Generate a unique blob name using timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        blob_name = f"{timestamp}-{filename}"
        
        # Determine container to use
        target_container = container_name or self.container_name
        # Ensure container exists
        try:
            self.service_client.create_container(target_container)
        except ResourceExistsError:
            pass

        # Get container client
        container_client = self.service_client.get_container_client(target_container)

        # Upload the file (sync client)
        blob_client = container_client.get_blob_client(blob_name)
        content_settings_obj = ContentSettings(content_type=content_type) if content_type else None
        blob_client.upload_blob(file_content, blob_type="BlockBlob", content_settings=content_settings_obj, overwrite=True)

        # Generate SAS URL that expires in 1 hour (for immediate viewing)
        sas_token = generate_blob_sas(
            account_name=self.account_name or self.service_client.account_name,
            container_name=target_container,
            blob_name=blob_name,
            account_key=self.account_key or getattr(self.service_client.credential, 'account_key', None),
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )

        blob_url = f"{blob_client.url}?{sas_token}"

        return {
            "blob_name": blob_name,
            "url": blob_url,
            "content_type": content_type,
            "size": len(file_content),
            "uploaded_at": timestamp,
        }
    
    def list_files(self, max_results: Optional[int] = None, container_name: Optional[str] = None) -> List[dict]:
        """List all files in the container (synchronous)

        Returns a list of dicts with name, url, content_type, size, last_modified
        """
        target_container = container_name or self.container_name
        # Ensure container exists (no-op if exists)
        try:
            self.service_client.create_container(target_container)
        except ResourceExistsError:
            pass

        container_client = self.service_client.get_container_client(target_container)
        files = []

        for blob in container_client.list_blobs():
            sas_token = generate_blob_sas(
                account_name=self.account_name or self.service_client.account_name,
                container_name=target_container,
                blob_name=blob.name,
                account_key=self.account_key or getattr(self.service_client.credential, 'account_key', None),
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=1)
            )

            blob_url = f"{self.service_client.get_blob_client(target_container, blob.name).url}?{sas_token}"

            files.append({
                "name": blob.name,
                "url": blob_url,
                "content_type": getattr(blob.content_settings, 'content_type', None),
                "size": blob.size,
                "last_modified": blob.last_modified.isoformat() if blob.last_modified is not None else None,
            })

            if max_results and len(files) >= max_results:
                break

        return files

# Singleton instance
blob_storage = AzureBlobStorage()