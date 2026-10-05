from src.lib.s3 import bucket, s3

def upload_file(file_path:str, file_key:str):
    s3.upload_file(
        file_path,
        bucket,
        file_key
    )