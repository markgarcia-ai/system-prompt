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
    is_featured: bool = False
    license_type: str = "personal"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    views: int = 0
    downloads: int = 0

class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    prompt_id: int = Field(foreign_key="prompt.id")
    payment_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

class PromptTag(SQLModel, table=True):
    prompt_id: int = Field(foreign_key="prompt.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)

class PromptWatermark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_id: int = Field(foreign_key="prompt.id")
    user_id: int = Field(foreign_key="user.id")
    watermarked_content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Analytics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_id: int = Field(foreign_key="prompt.id")
    user_id: int = Field(foreign_key="user.id")
    event_type: str  # 'view', 'purchase', 'download'
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Bundle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    price_cents: int
    owner_id: int = Field(foreign_key="user.id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BundlePrompt(SQLModel, table=True):
    bundle_id: int = Field(foreign_key="bundle.id", primary_key=True)
    prompt_id: int = Field(foreign_key="prompt.id", primary_key=True)

class PromptOutput(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_id: int = Field(foreign_key="prompt.id")
    user_id: int = Field(foreign_key="user.id")
    output_type: str  # 'text' or 'image'
    content: str
    rating: Optional[int] = None  # 1-5 rating
    feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
