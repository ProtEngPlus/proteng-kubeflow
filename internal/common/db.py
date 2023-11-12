import os

from google.cloud import storage
from google.oauth2 import service_account

def createBucket(bucketName, storageClass='STANDARD', location='US-CENTRAL1'):
    storage_client = getStorageClient()

    bucket = storage_client.bucket(bucketName)
    bucket.storage_class = storageClass

    bucket = storage_client.create_bucket(bucket, location=location)

    return f'Bucket {bucket.name} created with storage class {bucket.storage_class} in {bucket.location}.'

def uploadToBucket(bucketName, folderName, fileName, file):
    storage_client = getStorageClient()

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(folderName+"/"+fileName)
    blob.upload_from_string(file)

    return f'File {fileName} uploaded to {bucketName}.'

def downloadFromBucket(bucketName, folderName, fileName):
    storage_client = getStorageClient()

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(folderName+"/"+fileName)

    return blob.download_as_string()

def getStorageClient():
    creds = {
        "type": "service_account",
        "private_key_id": os.environ.get('PRIVATE_KEY_ID'),
        "private_key": os.environ.get('PRIVATE_KEY'),
        "client_email": os.environ.get('CLIENT_EMAIL'),
        "client_id": os.environ.get('CLIENT_ID'),
    }
    credentials = service_account.Credentials.from_service_account_info(creds)
    storage_client = storage.Client(credentials=credentials)
    return storage_client