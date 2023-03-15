from dotenv import load_dotenv
from google.cloud import storage


class GoogleStorageHandler:

  # TODO: Error handling..
  
  def __init__(self) -> None:
    load_dotenv()
    self.client = storage.Client()
    
  def download_object(self, bucket_name, object_name, download_directory = "."):
    bucket = self.client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.download_to_filename(f"{download_directory}/{blob.name}")
  
  def upload_object(self, bucket_name, object_name, file_location = "."):
    bucket = self.client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_filename(f"{file_location}/{object_name}")
