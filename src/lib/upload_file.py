import os

from src.lib.s3 import require_bucket, s3


def upload_file(file_path: str, file_key: str) -> str:
    """Upload local ``file_path`` to S3 ``file_key``, then delete the local file."""
    bucket = require_bucket()
    s3.upload_file(file_path, bucket, file_key)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
    return file_key
