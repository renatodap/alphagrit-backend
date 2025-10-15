from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps.auth import get_current_user
from app.services.uploads import signed_urls
from app.api.v1.dto.upload_dto import PostUploadIn, MetricUploadIn

router = APIRouter()


@router.post("/posts")
async def sign_post_upload(payload: PostUploadIn, user=Depends(get_current_user)):
    return await signed_urls.create_post_upload(
        user, payload.program_id, payload.post_id, payload.filename
    )


@router.post("/metrics")
async def sign_metric_upload(payload: MetricUploadIn, user=Depends(get_current_user)):
    return await signed_urls.create_metric_upload(user, payload.metric_id, payload.filename)


@router.get("/download")
async def sign_download(bucket: str, path: str, user=Depends(get_current_user)):
    # auth enforced by dependency; RLS still applies on access when using signed URLs
    return await signed_urls.create_download_url(bucket, path)
