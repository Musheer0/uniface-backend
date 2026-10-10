from botocore.exceptions import BotoCoreError, ClientError

from src.lib.s3 import is_missing_key_error, require_bucket, s3


def download_file(file_key: str, file_path: str) -> str:
    """Download S3 ``file_key`` to local ``file_path``.

    Canonical argument order is (file_key, file_path).
    Raises FileNotFoundError when the key does not exist.
    """
    bucket = require_bucket()
    try:
        s3.download_file(bucket, file_key, file_path)
    except ClientError as exc:
        if is_missing_key_error(exc):
            raise FileNotFoundError(f"S3 key not found: {file_key!r}") from exc
        raise
    except BotoCoreError as exc:
        raise IOError(f"S3 download failed for {file_key!r}: {exc}") from exc
    return file_path
