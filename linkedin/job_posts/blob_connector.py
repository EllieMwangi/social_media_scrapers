import os
import logging
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:S')
logger = logging.getLogger()

class AzureBlobStorage:
    def __init__(self):
        self.connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

    def upload_file(self, filename):
        
        logger.info(f"Connect to smart data storage account")
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connect_str)

        blob_client = self.blob_service_client.get_blob_client(container='linkedin-outputs', blob=filename.split('/')[1])
        logger.info(f"Uploading to Azure Storage as blob:{filename.split('/')[1]}")

        # Upload the created file
        with open(filename, "rb") as data:
            blob_client.upload_blob(data)