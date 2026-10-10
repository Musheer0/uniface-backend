import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

bucket = os.getenv("S3_BUCKET")
endpoint_url = os.getenv("AWS_ENDPOINT_URL_S3")
region_name = os.getenv("AWS_REGION")


def _build_client():
    kwargs: dict = {}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    if region_name:
        kwargs["region_name"] = region_name
    return boto3.client("s3", **kwargs)


s3 = _build_client()


def require_bucket() -> str:
    if not bucket:
        raise RuntimeError(
            "S3_BUCKET is not configured. Set S3_BUCKET (and Modal secret)."
        )
    return bucket


def is_missing_key_error(exc: Exception) -> bool:
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        return code in {"404", "NoSuchKey", "NotFound", "NoSuchBucket"}
    return False


__all__ = ["bucket", "endpoint_url", "region_name", "s3", "require_bucket", "is_missing_key_error"]
