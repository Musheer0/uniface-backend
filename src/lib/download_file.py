from src.lib.s3 import bucket, s3

def download_file(file_path:str, file_key:str):
    s3.download_file(
        bucket,
        file_key,
        file_path,
    )
    return file_path