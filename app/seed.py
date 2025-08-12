from sqlmodel import Session, select
from .db import engine, init_db
from .models import User, Prompt, Purchase
from .auth import hash_pw

def upsert_user(session: Session, email: str, password: str, is_seller=False) -> User:
    u = session.exec(select(User).where(User.email == email)).first()
    if u: return u
    u = User(email=email, password_hash=hash_pw(password), is_seller=is_seller)
    session.add(u); session.commit(); session.refresh(u)
    return u

def seed():
    init_db()
    with Session(engine) as session:
        seller = upsert_user(session, "seller@example.com", "seller123", True)
        buyer  = upsert_user(session, "buyer@example.com",  "buyer123",  False)

        if not session.exec(select(Prompt)).first():
            prompts = [
                Prompt(
                    title="YouTube-to-Thread Summarizer",
                    description="Turn long videos into crisp Twitter/X threads.",
                    content="SYSTEM: You are a concise, punchy summarizer...\nPROMPT: Given the transcript, extract 7–10 bullets with hooks...",
                    price_cents=499, owner_id=seller.id),
                Prompt(
                    title="Job Hunt Cover Letter Generator",
                    description="ATS-friendly cover letters tailored to the JD.",
                    content="ROLE: Career coach\nDATA: paste job description\nOUTPUT: 200–250 words, 3 quant metrics...",
                    price_cents=699, owner_id=seller.id),
                Prompt(
                    title="Bug Reproducer (JS/React)",
                    description="Coaxes LLM to write a minimal repro & test.",
                    content="SYSTEM: Senior SDET\nPROMPT: Ask for steps to isolate, then generate Jest test + reproduction...",
                    price_cents=599, owner_id=seller.id),
            ]
            for p in prompts:
                session.add(p)
            session.commit()

        print("Seed complete. Users:")
        print("  seller@example.com / seller123")
        print("  buyer@example.com  / buyer123")

if __name__ == "__main__":
    seed()
