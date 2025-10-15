from fastapi import APIRouter, Depends

from app.api.v1.deps.auth import get_current_user
from app.services.metrics import metrics_service
from app.api.v1.dto.metric_dto import MetricCreateIn

router = APIRouter()


@router.get("/metrics")
async def list_metrics(user=Depends(get_current_user)):
    return await metrics_service.list_metrics(user)


@router.post("/metrics")
async def create_metric(payload: MetricCreateIn, user=Depends(get_current_user)):
    return await metrics_service.create_metric(user, payload.model_dump())


@router.delete("/metrics/{metric_id}")
async def delete_metric(metric_id: int, user=Depends(get_current_user)):
    return await metrics_service.delete_metric(user, metric_id)
