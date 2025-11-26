# Steam Wrapped

## Description

Steam Wrapped is a web application that delivers a personalized "Wrapped" experience for Steam users, similar to Spotify Wrapped but focused on gaming data. It analyzes user profiles, game libraries, playtime, and achievements to provide immersive analytics and storytelling through an interactive dashboard and slide-based presentation. Key features include Steam OpenID login, dense analytics views with a Bento grid layout, caching for performance, and a modern design with dark mode, neon accents, and GSAP animations.

The project is built using Flask for the backend, with Jinja2 templates for rendering, and integrates with the Steam Web API and Google AI for enhanced features.

## Installation Instructions

### Prerequisites

- Python 3.13 or higher
- A Steam Web API key (obtain from [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey))
- A Google AI API key (obtain from [https://aistudio.google.com/app/api-keys](https://makersuite.google.com/app/apikey))

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/SpreadSheets600/Steam-Wrapped.git
   cd Steam-Wrapped
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following:
   ```env
   STEAM_API_KEY=your_steam_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   FLASK_ENV=development
   SECRET_KEY=your_random_secret_key_here
   ```

5. Run the application:
   ```bash
   python run.py
   ```

6. Open your browser and navigate to `http://localhost:5000`.

## Usage Instructions

After installation and setup:

- Visit the application in your browser at `http://localhost:5000`.
- Log in using your Steam account via OpenID.
- Explore the Dashboard for detailed analytics on your gaming habits.
- Experience the Wrapped section for an interactive storytelling presentation of your year in gaming.
- The app caches API responses to ensure smooth performance on subsequent visits.

For deployment, follow the instructions below.

## Deployment to Render

1. Connect your GitHub repository to Render.
2. Create a new Web Service from your repo.
3. Configure the service:
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:application`
4. Set Environment Variables:
   - `STEAM_API_KEY`: Your Steam Web API key
   - `GOOGLE_API_KEY`: Your Google AI API key
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: Generate a random secret key
5. Deploy! Your app will be live at `https://your-app-name.onrender.com`.

## Contribution Guidelines

We welcome contributions to Steam Wrapped! To contribute:

1. Fork the repository on GitHub.
2. Create a new branch for your feature or bug fix: `git checkout -b feature/your-feature-name`.
3. Make your changes, ensuring they follow the project's coding standards (PEP 8 for Python, consistent naming, etc.).
4. Write or update tests as necessary.
5. Commit your changes with clear, descriptive messages.
6. Push to your fork and submit a pull request to the main branch.
7. Provide a detailed description of your changes and why they are needed.

Please ensure all tests pass before submitting. For major changes, open an issue first to discuss the proposal.

## License Information

This project is licensed under the MIT License. See the LICENSE file for more details. The MIT License allows for free use, modification, and distribution of the software, provided that the original copyright notice and disclaimer are included.

## Contact Information

For questions, issues, or suggestions, please use the GitHub Issues page at [https://github.com/SpreadSheets600/Steam-Wrapped/issues](https://github.com/SpreadSheets600/Steam-Wrapped/issues).

You can also reach out via email if needed (check the repository owner's profile for contact details).
