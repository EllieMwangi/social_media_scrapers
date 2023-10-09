import os
import logging
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:S')
logger = logging.getLogger()

class AzureBlobStorage:
    def __init__(self):
        self.connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

    def get_latest_file(self):

        logger.info(f"Connect to smart data storage account")
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connect_str)

        logger.info("Connect to scraping container")
        self.container_client = self.blob_service_client.get_container_client(container = 'linkedin-inputs')

        logger.info('List container blobs:')
        blob_list = self.container_client.list_blobs()
        self.latest_file = list(blob_list)[0].name

    def download_latest_file(self):

        logger.info(f'Create download file path')
        download_file_path = os.path.join('data', f'{self.latest_file}')

        logger.info(f"Downloading blob to: {download_file_path}")
        with open(download_file_path, "wb") as download_file:
            download_file.write(self.container_client.download_blob(self.latest_file).readall())

    def upload_file(self, filename):
        
        blob_client = self.blob_service_client.get_blob_client(container='linkedin-outputs', blob=filename.split('/')[1])

        logger.info(f"Uploading to Azure Storage as blob:{filename.split('/')[1]}")

        # Upload the created file
        with open(filename, "rb") as data:
            blob_client.upload_blob(data)