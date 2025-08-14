from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .db import init_db
from .routes import auth as auth_routes, prompts as prompt_routes, purchases as purchase_routes, dashboard as dashboard_routes, tags as tags_routes, outputs as outputs_routes, search as search_routes, analytics as analytics_routes, bundles as bundles_routes, uploads as uploads_routes, webhooks as webhooks_routes, payments as payments_routes
import jwt
from .auth import SECRET_KEY, ALGORITHM

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def start():
    init_db()
    # Seed database with mock data if empty
    from .seed import seed_database
    seed_database()

app.include_router(auth_routes.router)
app.include_router(prompt_routes.router)
app.include_router(purchase_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(tags_routes.router)
app.include_router(outputs_routes.router)
app.include_router(search_routes.router)
app.include_router(analytics_routes.router)
app.include_router(bundles_routes.router)
app.include_router(uploads_routes.router)
app.include_router(webhooks_routes.router)
app.include_router(payments_routes.router)

@app.get("/")
def landing_page(request: Request):
    """Landing page - redirect logged-in users to dashboard"""
    # Check if user is logged in
    token = request.cookies.get("token")
    if token:
        try:
            # Verify token and redirect to dashboard if valid
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return RedirectResponse(url="/dashboard")
        except:
            pass  # Invalid token, continue to landing page
    
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
def market_page(request: Request):
    """Market page for browsing prompts"""
    from .models import Prompt, User
    from .db import get_session
    from sqlmodel import select
    
    # Get all prompts
    session = next(get_session())
    try:
        prompts = session.exec(select(Prompt)).all()
    finally:
        session.close()
    
    return templates.TemplateResponse("market.html", {"request": request, "prompts": prompts})

@app.get("/prompts/{pid}", response_class=HTMLResponse)
def prompt_detail(pid: int, request: Request):
    return templates.TemplateResponse("prompt_detail.html", {"request": request, "pid": pid})

@app.get("/success", response_class=HTMLResponse)
def success(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard")
def dashboard_page(request: Request):
    """Dashboard page for logged-in users"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/profile")
def profile_page(request: Request):
    """Profile management page"""
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/add-prompt", response_class=HTMLResponse)
def add_prompt_page(request: Request):
    """Page for adding new prompts"""
    return templates.TemplateResponse("add_prompt.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
def analytics_dashboard(request: Request):
    """Analytics dashboard for sellers"""
    return templates.TemplateResponse("analytics_dashboard.html", {"request": request})
