import os

from google.cloud import storage
from google.oauth2 import service_account

path_to_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
def createBucket(bucketName, storageClass='STANDARD', location='US-CENTRAL1'):
    credentials = service_account.Credentials.from_service_account_info(path_to_creds)
    storage_client = storage.Client(credentials=credentials)

    bucket = storage_client.bucket(bucketName)
    bucket.storage_class = storageClass

    bucket = storage_client.create_bucket(bucket, location=location)

    return f'Bucket {bucket.name} created with storage class {bucket.storage_class} in {bucket.location}.'

def uploadToBucket(bucketName, folderName, fileName, file):
    credentials = service_account.Credentials.from_service_account_file(path_to_creds)
    storage_client = storage.Client(credentials=credentials)

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(folderName+"/"+fileName)
    blob.upload_from_string(file)

    return f'File {fileName} uploaded to {bucketName}.'

def downloadFromBucket(bucketName, folderName, fileName):
    credentials = service_account.Credentials.from_service_account_file(path_to_creds)
    storage_client = storage.Client(credentials=credentials)

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(folderName+"/"+fileName)

    return blob.download_as_string()