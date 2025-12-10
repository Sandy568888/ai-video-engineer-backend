"""Wasabi S3 service for video storage"""
import boto3
from botocore.exceptions import ClientError
import logging
import os
logger = logging.getLogger(__name__)

class WasabiService:
    def __init__(self):
        general_mock = os.getenv('MOCK_MODE', 'False').lower() == 'true'
        specific_mock = os.getenv('WASABI_MOCK_MODE', 'False').lower() == 'true'
        self.mock_mode = general_mock or specific_mock
        
        logger.info(f"Wasabi initialized: mock_mode={self.mock_mode}")
        
        if not self.mock_mode:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv('WASABI_ENDPOINT', 'https://s3.wasabisys.com'),
                aws_access_key_id=os.getenv('WASABI_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('WASABI_SECRET_KEY'),
                region_name=os.getenv('WASABI_REGION', 'us-east-1')
            )
            self.bucket_name = os.getenv('WASABI_BUCKET_NAME', 'ai-videos')
        else:
            self.s3_client = None
            self.bucket_name = 'mock-bucket'
    
    def upload_file(self, file_path, object_name):
        """Upload file to Wasabi S3"""
        if self.mock_mode:
            logger.info(f"MOCK: Uploading {file_path} as {object_name}")
            return f"https://mock-wasabi.com/{self.bucket_name}/{object_name}"
        
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name, ExtraArgs={'ACL': 'private'})
            url = self.s3_client.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name, 'Key': object_name}, ExpiresIn=604800)
            logger.info(f"Uploaded {object_name} to Wasabi")
            return url
        except ClientError as e:
            logger.error(f"Wasabi upload error: {e}")
            raise
    
    def delete_file(self, object_name):
        """Delete file from Wasabi S3"""
        if self.mock_mode:
            logger.info(f"MOCK: Deleting {object_name}")
            return True
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"Deleted {object_name}")
            return True
        except ClientError as e:
            logger.error(f"Wasabi delete error: {e}")
            return False
