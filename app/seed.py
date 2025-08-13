from sqlmodel import Session, select
from .models import User, Prompt, Tag, PromptTag, Purchase, Analytics
from .db import engine
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def seed_database():
    """Seed the database with mock data"""
    with Session(engine) as session:
        # Check if data already exists
        existing_users = session.exec(select(User)).all()
        if existing_users:
            print("Database already has data. Skipping seed.")
            return
        
        print("Seeding database with mock data...")
        
        # Create users
        users = [
            User(
                email="alice@example.com",
                password_hash=hash_password("password123"),
                is_seller=True
            ),
            User(
                email="bob@example.com", 
                password_hash=hash_password("password123"),
                is_seller=True
            ),
            User(
                email="charlie@example.com",
                password_hash=hash_password("password123"),
                is_seller=False
            )
        ]
        
        for user in users:
            session.add(user)
        session.commit()
        
        # Create tags
        tags = [
            Tag(name="Marketing"),
            Tag(name="Creative Writing"),
            Tag(name="Business"),
            Tag(name="Technology"),
            Tag(name="Education"),
            Tag(name="Entertainment"),
            Tag(name="Health"),
            Tag(name="Finance")
        ]
        
        for tag in tags:
            session.add(tag)
        session.commit()
        
        # Create prompts
        prompts = [
            Prompt(
                title="Epic Fantasy Landscape Generator",
                description="Create breathtaking fantasy landscapes with towering crystal mountains, floating islands, and glowing waterfalls in Studio Ghibli style.",
                content="Create a stunning fantasy landscape featuring: [DESCRIPTION]. Style: Studio Ghibli, epic fantasy, magical atmosphere. Include: crystal mountains, floating islands, glowing waterfalls, ethereal lighting, rich colors, detailed textures. Make it cinematic and awe-inspiring.",
                price_cents=699,
                owner_id=users[0].id,
                is_featured=True,
                license_type="commercial",
                views=234,
                downloads=45
            ),
            Prompt(
                title="Brand Name & Slogan Generator",
                description="Generate unique startup names and catchy slogans for any business. Perfect for entrepreneurs and marketers.",
                content="Generate a brand name and slogan for a [BUSINESS_TYPE] company. Requirements: 1) Brand name should be memorable and unique 2) Slogan should be catchy and convey the value proposition 3) Both should reflect [KEY_VALUES] 4) Make it suitable for [TARGET_AUDIENCE]. Format: Brand Name: [NAME] | Slogan: [SLOGAN] | Tagline: [TAGLINE]",
                price_cents=599,
                owner_id=users[0].id,
                is_featured=True,
                license_type="personal",
                views=187,
                downloads=32
            ),
            Prompt(
                title="Neo-Noir Cinematic Portrait",
                description="Create stunning cinematic portraits with Blade Runner aesthetics. Perfect for photographers and filmmakers.",
                content="Create a neo-noir cinematic portrait of [SUBJECT]. Style: Blade Runner aesthetic, cyberpunk, high contrast, dramatic lighting, moody atmosphere. Include: neon lighting, rain effects, urban background, film noir elements, cinematic composition. Make it look like a movie still.",
                price_cents=799,
                owner_id=users[1].id,
                is_featured=True,
                license_type="commercial",
                views=312,
                downloads=67
            ),
            Prompt(
                title="Video-to-Thread Summarizer",
                description="Turn long videos into crisp Twitter/X threads. Perfect for content creators and social media managers.",
                content="Convert this video transcript into a Twitter/X thread: [TRANSCRIPT]. Requirements: 1) Break into 10-15 tweetable chunks 2) Each tweet should be engaging and informative 3) Use emojis and formatting for visual appeal 4) Include a compelling hook in the first tweet 5) End with a call-to-action. Format as numbered tweets with proper threading.",
                price_cents=499,
                owner_id=users[1].id,
                is_featured=False,
                license_type="personal",
                views=156,
                downloads=23
            ),
            Prompt(
                title="If the Moon Landing Happened in 2025",
                description="Create a hyperrealistic depiction of the Apollo 11 moon landing as if it happened in 2025, with modern EVA suits.",
                content="Create a hyperrealistic image of the Apollo 11 moon landing as if it happened in 2025. Include: modern EVA suits with advanced technology, contemporary space equipment, high-resolution photography style, realistic lighting, detailed lunar surface, Earth in background. Make it look like a real NASA photograph from the future.",
                price_cents=899,
                owner_id=users[0].id,
                is_featured=True,
                license_type="commercial",
                views=445,
                downloads=89
            ),
            Prompt(
                title="ATS-Optimized Resume Generator",
                description="Create professional resumes optimized for ATS keyword matching and tailored to specific job roles.",
                content="Create an ATS-optimized resume for a [JOB_TITLE] position at [COMPANY]. Requirements: 1) Include relevant keywords from the job description 2) Use clear, scannable formatting 3) Quantify achievements with numbers 4) Focus on relevant experience and skills 5) Optimize for applicant tracking systems. Format as a professional resume with proper sections.",
                price_cents=699,
                owner_id=users[1].id,
                is_featured=False,
                license_type="personal",
                views=267,
                downloads=41
            ),
            Prompt(
                title="AI-Powered Blog Post Writer",
                description="Generate engaging blog posts with SEO optimization and compelling storytelling.",
                content="Write a comprehensive blog post about [TOPIC]. Requirements: 1) Engaging introduction that hooks the reader 2) Well-structured content with headings 3) SEO-optimized with relevant keywords 4) Include practical tips and actionable advice 5) Compelling conclusion with call-to-action. Target audience: [AUDIENCE]. Word count: 1500-2000 words.",
                price_cents=599,
                owner_id=users[0].id,
                is_featured=False,
                license_type="commercial",
                views=189,
                downloads=28
            ),
            Prompt(
                title="Product Description Generator",
                description="Create compelling product descriptions that convert browsers into buyers.",
                content="Write a compelling product description for [PRODUCT_NAME]. Requirements: 1) Highlight key benefits and features 2) Use persuasive language and emotional triggers 3) Include social proof elements 4) Optimize for e-commerce platforms 5) Include relevant keywords naturally. Target audience: [AUDIENCE]. Tone: [TONE]",
                price_cents=399,
                owner_id=users[1].id,
                is_featured=False,
                license_type="personal",
                views=134,
                downloads=19
            )
        ]
        
        for prompt in prompts:
            session.add(prompt)
        session.commit()
        
        # Create prompt-tag relationships
        prompt_tags = [
            PromptTag(prompt_id=prompts[0].id, tag_id=tags[1].id),  # Fantasy Landscape - Creative Writing
            PromptTag(prompt_id=prompts[0].id, tag_id=tags[3].id),  # Fantasy Landscape - Technology
            PromptTag(prompt_id=prompts[1].id, tag_id=tags[0].id),  # Brand Generator - Marketing
            PromptTag(prompt_id=prompts[1].id, tag_id=tags[2].id),  # Brand Generator - Business
            PromptTag(prompt_id=prompts[2].id, tag_id=tags[1].id),  # Cinematic Portrait - Creative Writing
            PromptTag(prompt_id=prompts[2].id, tag_id=tags[5].id),  # Cinematic Portrait - Entertainment
            PromptTag(prompt_id=prompts[3].id, tag_id=tags[0].id),  # Video Summarizer - Marketing
            PromptTag(prompt_id=prompts[3].id, tag_id=tags[4].id),  # Video Summarizer - Education
            PromptTag(prompt_id=prompts[4].id, tag_id=tags[3].id),  # Moon Landing - Technology
            PromptTag(prompt_id=prompts[4].id, tag_id=tags[4].id),  # Moon Landing - Education
            PromptTag(prompt_id=prompts[5].id, tag_id=tags[2].id),  # Resume Generator - Business
            PromptTag(prompt_id=prompts[5].id, tag_id=tags[4].id),  # Resume Generator - Education
            PromptTag(prompt_id=prompts[6].id, tag_id=tags[0].id),  # Blog Writer - Marketing
            PromptTag(prompt_id=prompts[6].id, tag_id=tags[1].id),  # Blog Writer - Creative Writing
            PromptTag(prompt_id=prompts[7].id, tag_id=tags[0].id),  # Product Description - Marketing
            PromptTag(prompt_id=prompts[7].id, tag_id=tags[2].id),  # Product Description - Business
        ]
        
        for pt in prompt_tags:
            session.add(pt)
        session.commit()
        
        # Create some purchases
        purchases = [
            Purchase(
                user_id=users[2].id,
                prompt_id=prompts[0].id,
                payment_id="pi_mock_001"
            ),
            Purchase(
                user_id=users[2].id,
                prompt_id=prompts[1].id,
                payment_id="pi_mock_002"
            ),
            Purchase(
                user_id=users[2].id,
                prompt_id=prompts[2].id,
                payment_id="pi_mock_003"
            )
        ]
        
        for purchase in purchases:
            session.add(purchase)
        session.commit()
        
        # Create analytics events (only for logged-in users)
        analytics_events = []
        
        # Add purchase events for purchased prompts
        for purchase in purchases:
            analytics_events.append(Analytics(
                prompt_id=purchase.prompt_id,
                user_id=purchase.user_id,
                event_type="purchase"
            ))
        
        for event in analytics_events:
            session.add(event)
        session.commit()
        
        print(f"✅ Seeded database with:")
        print(f"   - {len(users)} users")
        print(f"   - {len(tags)} tags")
        print(f"   - {len(prompts)} prompts")
        print(f"   - {len(prompt_tags)} prompt-tag relationships")
        print(f"   - {len(purchases)} purchases")
        print(f"   - {len(analytics_events)} analytics events")

if __name__ == "__main__":
    seed_database()
