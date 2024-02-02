import os

from google.cloud import storage
from google.oauth2 import service_account

def createBucket(bucketName, storageClass='STANDARD', location='US-CENTRAL1'):
    storage_client = getStorageClient()

    bucket = storage_client.bucket(bucketName)
    bucket.storage_class = storageClass

    bucket = storage_client.create_bucket(bucket, location=location)

    return f'Bucket {bucket.name} created with storage class {bucket.storage_class} in {bucket.location}.'

def uploadToBucket(bucketName, fileName, file):
    storage_client = getStorageClient()

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(fileName)
    blob.upload_from_string(file)

    return f'File {fileName} uploaded to {bucketName}.'

def downloadFromBucket(bucketName, fileName):
    storage_client = getStorageClient()

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(fileName)

    return blob.download_as_string()

def getStorageClient():
    pk = os.environ.get('PRIVATE_KEY').replace('\\n', '\n') # replace the escaped newline character
    creds = {
        "type": "service_account",
        "project_id": os.environ.get('PROJECT_ID'),
        "private_key_id": os.environ.get('PRIVATE_KEY_ID'),
        "private_key": pk,
        "client_email": os.environ.get('CLIENT_EMAIL'),
        "client_id": os.environ.get('CLIENT_ID'),
        "token_uri": os.environ.get('TOKEN_URI'),
    }
    credentials = service_account.Credentials.from_service_account_info(creds)
    storage_client = storage.Client(credentials=credentials)
    return storage_client

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    #print(os.environ.get('PRIVATE_KEY'))
    # TEST: createBucket
    client = getStorageClient()