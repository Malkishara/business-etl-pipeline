import logging
import os
from datetime import date
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()  # reads .env; the keys never appear in code

log = logging.getLogger(__name__)


def upload_file(local_path, prefix):
    """Upload a file to s3://<bucket>/<prefix>/<YYYY-MM-DD>/<filename>."""
    bucket = os.getenv("S3_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-1")
    if not bucket:
        log.warning("S3_BUCKET not set - skipping upload")
        return None

    local_path = Path(local_path)
    key = f"{prefix}/{date.today().isoformat()}/{local_path.name}"
    try:
        # boto3 automatically reads AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
        boto3.client("s3", region_name=region).upload_file(
            str(local_path), bucket, key,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )
        uri = f"s3://{bucket}/{key}"
        log.info("Uploaded %s -> %s", local_path.name, uri)
        return uri
    except (BotoCoreError, ClientError) as exc:
        log.error("S3 upload failed: %s", exc)
        return None