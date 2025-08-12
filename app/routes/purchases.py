import os, stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from ..db import get_session
from ..models import Prompt, Purchase, Analytics
from ..auth import get_current_user

router = APIRouter(prefix="/api/purchase", tags=["purchase"])

STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")

if STRIPE_SECRET:
    stripe.api_key = STRIPE_SECRET

@router.get("/mine")
def my_purchases(user=Depends(get_current_user), session: Session = Depends(get_session)):
    rows = session.exec(select(Purchase, Prompt).where(Purchase.user_id==user.id).join(Prompt, Prompt.id==Purchase.prompt_id)).all()
    return [{"prompt_id": p.id, "title": p.title, "purchase_id": pu.id, "created_at": pu.created_at} for (pu, p) in rows]

@router.post("/{prompt_id}/checkout")
def create_checkout(prompt_id: int, user=Depends(get_current_user), session: Session = Depends(get_session)):
    p = session.get(Prompt, prompt_id)
    if not p or not p.is_active: raise HTTPException(status_code=404)
    if not STRIPE_SECRET:
        # DEV: instant "purchase"
        purchase = Purchase(user_id=user.id, prompt_id=prompt_id, payment_id="dev_"+str(prompt_id))
        session.add(purchase)
        
        # Track purchase analytics
        analytics = Analytics(
            prompt_id=prompt_id,
            event_type="purchase",
            user_id=user.id
        )
        session.add(analytics)
        
        session.commit(); session.refresh(purchase)
        return {"dev": True, "message": "DEV purchase complete", "redirect_url": f"{APP_URL}/success"}
    session_obj = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {"currency":"usd","product_data":{"name":p.title},"unit_amount":p.price_cents},
            "quantity": 1
        }],
        success_url=f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}&prompt_id={p.id}",
        cancel_url=f"{APP_URL}/prompts/{p.id}",
        metadata={"user_id": str(user.id), "prompt_id": str(p.id)}
    )
    return {"checkout_url": session_obj.url}

@router.post("/webhook")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    if not STRIPE_SECRET:
        return {"ok": True}
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(payload, sig, endpoint_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook")
    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]
        user_id = int(s["metadata"]["user_id"]); prompt_id = int(s["metadata"]["prompt_id"])
        payment_id = s["id"]
        purchase = Purchase(user_id=user_id, prompt_id=prompt_id, payment_id=payment_id)
        session.add(purchase)
        
        # Track purchase analytics
        analytics = Analytics(
            prompt_id=prompt_id,
            event_type="purchase",
            user_id=user_id
        )
        session.add(analytics)
        
        session.commit()
    return {"ok": True}
