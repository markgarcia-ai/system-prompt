# Prompt Market - AI Prompt Marketplace

A modern, full-featured marketplace for buying and selling AI prompts. Built with FastAPI, SQLModel, and modern web technologies.

## 🚀 Features

- **AI Prompt Marketplace**: Browse and purchase high-quality prompts from AI professionals
- **Expert-Curated Content**: Every prompt is carefully selected and tested by AI professionals
- **Instant Access**: Download prompts immediately after purchase
- **Community Driven**: Join a growing community of AI enthusiasts
- **Secure Transactions**: Safe payment processing with Stripe integration
- **Premium Experience**: Intuitive interface with responsive design
- **Analytics Dashboard**: Track your sales and performance
- **Watermarking**: Protect your prompts with buyer-specific watermarks
- **Tag System**: Organize prompts with categories and tags
- **Rating System**: Community-driven quality assurance

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLModel, SQLAlchemy
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: JWT with bcrypt
- **Payments**: Stripe integration
- **Frontend**: Jinja2 templates with Tailwind CSS
- **Database Migrations**: Alembic
- **Deployment**: Docker support

## 📋 Prerequisites

- Python 3.8+
- pip
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/markgarcia-ai/system-prompt.git
cd system-prompt
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=sqlite:///./dev.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe (for payments)
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 5. Initialize Database

```bash
# Run database migrations
alembic upgrade head
```

### 6. Run the Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

## 📁 Project Structure

```
prompt-market/
├── alembic/                 # Database migrations
├── app/
│   ├── routes/             # API routes
│   ├── templates/          # HTML templates
│   ├── static/             # Static files (CSS, JS, images)
│   ├── models/             # Database models
│   ├── auth.py             # Authentication logic
│   ├── db.py               # Database configuration
│   └── main.py             # FastAPI application
├── requirements.txt        # Python dependencies
├── alembic.ini            # Alembic configuration
├── docker-compose.yml     # Docker configuration
└── README.md              # This file
```

## 🔧 Configuration

### Database

The application uses SQLite by default for development. For production, update the `DATABASE_URL` in your `.env` file to use PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/prompt_market
```

### Stripe Integration

1. Create a Stripe account at [stripe.com](https://stripe.com)
2. Get your API keys from the Stripe dashboard
3. Add them to your `.env` file
4. Set up webhook endpoints for payment processing

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Docker Build

```bash
# Build the image
docker build -t prompt-market .

# Run the container
docker run -p 8000:8000 prompt-market
```

## 📊 API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## 🔐 Authentication

The application uses JWT tokens for authentication. Users can:

1. Register for a new account
2. Login with email and password
3. Access protected routes with JWT tokens

## 💳 Payment Processing

Payments are processed through Stripe:

- Secure payment processing
- Webhook support for payment confirmations
- Automatic delivery of purchased prompts
- Refund handling

## 🎨 Customization

### Styling

The application uses Tailwind CSS. You can customize the design by modifying:

- `app/static/css/tailwind.css`
- Template files in `app/templates/`

### Adding New Features

1. Create new routes in `app/routes/`
2. Add database models in `app/models/`
3. Update templates as needed
4. Run database migrations for schema changes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/markgarcia-ai/system-prompt/issues) page
2. Create a new issue with detailed information
3. Contact the maintainers

## 🔮 Roadmap

- [ ] Advanced analytics and reporting
- [ ] AI-powered prompt recommendations
- [ ] Mobile app development
- [ ] Multi-language support
- [ ] Advanced watermarking features
- [ ] API rate limiting and caching
- [ ] Integration with more AI platforms

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Payments powered by [Stripe](https://stripe.com/)
- Database migrations with [Alembic](https://alembic.sqlalchemy.org/)
