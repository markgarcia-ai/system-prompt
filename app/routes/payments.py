from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Prompt, Purchase
from ..auth import get_current_user
import stripe
import os
from typing import Optional

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/api/payments", tags=["payments"])

class CreatePaymentIntentRequest(BaseModel):
    prompt_id: int

class CreatePaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str

@router.post("/create-payment-intent")
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a Stripe payment intent for purchasing a prompt"""
    
    # Get the prompt
    prompt = session.get(Prompt, request.prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Check if user already owns this prompt
    existing_purchase = session.exec(
        select(Purchase).where(
            Purchase.user_id == user.id,
            Purchase.prompt_id == request.prompt_id
        )
    ).first()
    
    if existing_purchase:
        raise HTTPException(status_code=400, detail="You already own this prompt")
    
    try:
        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(prompt.price * 100),  # Convert to cents
            currency="usd",
            metadata={
                "user_id": user.id,
                "prompt_id": prompt.id,
                "prompt_title": prompt.title
            }
        )
        
        return CreatePaymentIntentResponse(
            client_secret=payment_intent.client_secret,
            payment_intent_id=payment_intent.id
        )
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm-purchase")
async def confirm_purchase(
    payment_intent_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Confirm a purchase after successful payment"""
    
    try:
        # Retrieve payment intent from Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status != "succeeded":
            raise HTTPException(status_code=400, detail="Payment not completed")
        
        # Extract metadata
        prompt_id = payment_intent.metadata.get("prompt_id")
        if not prompt_id:
            raise HTTPException(status_code=400, detail="Invalid payment intent")
        
        prompt_id = int(prompt_id)
        prompt = session.get(Prompt, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Check if already purchased
        existing_purchase = session.exec(
            select(Purchase).where(
                Purchase.user_id == user.id,
                Purchase.prompt_id == prompt_id
            )
        ).first()
        
        if existing_purchase:
            return {"message": "Purchase already confirmed"}
        
        # Create purchase record
        purchase = Purchase(
            user_id=user.id,
            prompt_id=prompt_id,
            amount_cents=int(payment_intent.amount),
            stripe_payment_intent_id=payment_intent_id
        )
        session.add(purchase)
        
        # Update seller's balance
        seller = session.get(User, prompt.user_id)
        if seller:
            seller.balance_cents += int(payment_intent.amount * 0.85)  # 85% to seller, 15% platform fee
        
        # Increment prompt downloads
        prompt.downloads += 1
        
        session.commit()
        
        return {"message": "Purchase confirmed successfully"}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-payout")
async def create_payout(
    amount_cents: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a payout to user's PayPal or bank account"""
    
    if amount_cents > user.balance_cents:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    if amount_cents < 1000:  # Minimum $10
        raise HTTPException(status_code=400, detail="Minimum withdrawal amount is $10")
    
    try:
        # Create Stripe transfer (if using Stripe Connect)
        if user.stripe_account_id:
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency="usd",
                destination=user.stripe_account_id,
                metadata={
                    "user_id": user.id,
                    "type": "payout"
                }
            )
        else:
            # For PayPal or bank transfers, you'd integrate with those services
            # For now, we'll just deduct from balance
            pass
        
        # Deduct from user's balance
        user.balance_cents -= amount_cents
        session.commit()
        
        return {"message": "Payout initiated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/balance")
async def get_balance(user: User = Depends(get_current_user)):
    """Get user's current balance"""
    return {
        "balance_cents": user.balance_cents,
        "balance_formatted": f"${user.balance_cents / 100:.2f}"
    }

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        # Handle successful payment
        await handle_payment_success(payment_intent)
    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        # Handle failed payment
        await handle_payment_failure(payment_intent)
    
    return {"status": "success"}

async def handle_payment_success(payment_intent):
    """Handle successful payment"""
    # This would typically update the database
    # For now, we'll rely on the confirm-purchase endpoint
    pass

async def handle_payment_failure(payment_intent):
    """Handle failed payment"""
    # This would typically notify the user
    pass 