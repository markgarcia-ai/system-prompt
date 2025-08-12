# kept for structure; Stripe webhook is in purchases.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
