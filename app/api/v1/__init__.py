from fastapi import APIRouter

from app.api.v1.routers import (
    admin,
    affiliate,
    ebooks,
    metrics,
    programs,
    uploads,
    users,
    waitlist,
    webhooks,
    winter_arc,
)

api_router = APIRouter()

# Public-ish endpoints
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Authenticated endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ebooks.router, prefix="/ebooks", tags=["ebooks"])
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])
api_router.include_router(metrics.router, prefix="/me", tags=["metrics"])  # /me/metrics
api_router.include_router(affiliate.router, prefix="/affiliate", tags=["affiliate"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(waitlist.router, prefix="/waitlist", tags=["waitlist"])  # POST /api/v1/waitlist
api_router.include_router(winter_arc.router, prefix="/winter-arc", tags=["winter-arc"])
