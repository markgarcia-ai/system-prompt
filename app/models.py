from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    is_seller: bool = False
    stripe_account_id: Optional[str] = None

class Prompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    content: str
    price_cents: int = 500
    owner_id: int = Field(foreign_key="user.id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    prompt_id: int = Field(foreign_key="prompt.id")
    payment_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
