from gcloud.aio.storage import Storage
import aiohttp

from google.cloud import storage

async def asyncUploadToBucket(bucketName, folderName, fileName, file):
    async with aiohttp.ClientSession() as session:
        storage = Storage(service_file='/code/common/creds.json', session=session)
        status = await storage.upload(bucketName, folderName+"/"+fileName, file)
        return status['selfLink']
    
def createBucket(bucketName, storageClass='STANDARD', location='US-CENTRAL1'):
    storage_client = storage.Client.from_service_account_json('/code/common/creds.json')

    bucket = storage_client.bucket(bucketName)
    bucket.storage_class = storageClass

    bucket = storage_client.create_bucket(bucket, location=location)

    return f'Bucket {bucket.name} created with storage class {bucket.storage_class} in {bucket.location}.'

def uploadToBucket(bucketName, folderName, fileName, file):
    storage_client = storage.Client.from_service_account_json('/code/common/creds.json')

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(folderName+"/"+fileName)
    blob.upload_from_string(file)

    return f'File {fileName} uploaded to {bucketName}.'

def downloadFromBucket(bucketName, folderName, fileName):
    storage_client = storage.Client.from_service_account_json('/code/common/creds.json')

    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(folderName+"/"+fileName)

    return blob.download_as_string()