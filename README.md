# Steam Wrapped 2025

A futuristic, immersive Steam analytics dashboard and "Wrapped" experience.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:

   ```bash
   python run.py
   ```

3. Open `http://localhost:5000`

## Deployment to Render

1. **Connect your GitHub repository** to Render
2. **Create a new Web Service** from your repo
3. **Configure the service**:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:application`
4. **Set Environment Variables**:
   - `STEAM_API_KEY`: Your Steam Web API key (get from `https://steamcommunity.com/dev/apikey`)
   - `GOOGLE_API_KEY`: Your Google AI API key (get from `https://makersuite.google.com/app/apikey`)
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: Generate a random secret key
5. **Deploy!** Your app will be live at `https://your-app-name.onrender.com`

## Features

- **Steam Login** (OpenID)
- **Dashboard**: Dense analytics view with Bento grid layout.
- **Wrapped**: Interactive storytelling experience with horizontal slides.
- **Caching**: API responses are cached to improve performance.
- **Design**: Dark mode, neon accents, glassmorphism, GSAP animations.

## Structure

- `app/routes`: Flask routes (Auth, Views)
- `app/utils`: Helper functions (Steam API, Analytics)
- `app/templates`: Jinja2 templates
- `app/static`: CSS/JS assets
