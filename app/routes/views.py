from flask import Blueprint, render_template, session, redirect, url_for

from app.utils.steam_client import (
    get_user_summary,
    get_friends_list,
    get_owned_games,
    get_recent_games,
    get_badges,
    get_steam_level,
)
from app.utils.analytics import Analytics

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    if "steam_id" in session:
        return redirect(url_for("views.dashboard"))
    return render_template("index.html")


@views_bp.route("/generating")
def generating():
    if "steam_id" not in session:
        return redirect(url_for("views.index"))
    return render_template("generating.html")


@views_bp.route("/dashboard")
def dashboard():
    if "steam_id" not in session:
        return redirect(url_for("views.index"))

    steam_id = session["steam_id"]

    user = get_user_summary(steam_id)
    friends = get_friends_list(steam_id)
    games = get_owned_games(steam_id)
    recent = get_recent_games(steam_id)
    badges = get_badges(steam_id)
    level = get_steam_level(steam_id)

    if isinstance(level, dict) and "player_level" in level:
        level = level["player_level"]
    elif level is None:
        level = 0

    if not user:
        return "Error fetching profile", 500

    analytics = Analytics(user, games, friends, badges, recent, steam_id)
    stats = analytics.get_dashboard_stats()
    stats["level"] = level

    timeline_data = analytics.get_playtime_timeline()
    top_devs = analytics.get_top_developers()
    genre_data = analytics.get_genre_breakdown()
    energy_data = analytics.get_gaming_energy_score()

    context = {
        "user": user,
        "friends": friends,
        "stats": stats,
        "recent": recent.get("games", [])[:8] if recent else [],
        "top_games": analytics.get_top_games(5),
        "top_game": analytics.get_top_games(1)[0]
        if analytics.get_top_games(1)
        else None,
        "personality": analytics.get_playstyle_personality(),
        "timeline": timeline_data.get("data", []),
        "timeline_stats": {
            "most_active_month": timeline_data.get("most_active", {}).get(
                "month", "N/A"
            ),
            "least_active_month": timeline_data.get("least_active", {}).get(
                "month", "N/A"
            ),
        },
        "genre_breakdown": genre_data,
        "top_developers": top_devs,
        "achievement_stats": analytics.get_achievement_stats(),
        "achievement_score": analytics.get_achievement_score(),
        "energy_score": energy_data.get("score", 0),
        "energy_percentile": energy_data.get("percentile", 50),
        "global_comparison": analytics.get_global_comparison(),
        "games_categorized": analytics.get_games_categorized(),
        "badges": badges if badges else [],
        "sleep_destroyer": analytics.get_sleep_destroyer(),
    }

    return render_template("dashboard.html", **context)


@views_bp.route("/wrapped")
def wrapped():
    if "steam_id" not in session:
        return redirect(url_for("views.index"))

    steam_id = session["steam_id"]

    user = get_user_summary(steam_id)
    friends = get_friends_list(steam_id)
    games = get_owned_games(steam_id)
    recent = get_recent_games(steam_id)
    badges = get_badges(steam_id)

    analytics = Analytics(user, games, friends, badges, recent, steam_id)

    genre_data = analytics.get_genre_breakdown()
    top_genre = list(genre_data.keys())[0] if genre_data else "Unknown"
    top_genre_hours = (
        genre_data[top_genre]["hours"] if genre_data and top_genre in genre_data else 0
    )

    top_devs = analytics.get_top_developers()
    stats = analytics.get_dashboard_stats()
    energy_data = analytics.get_gaming_energy_score()

    context = {
        "user": user,
        "stats": stats,
        "top_game": analytics.get_top_games(1)[0]
        if analytics.get_top_games(1)
        else None,
        "top_5_games": analytics.get_top_games(5),
        "top_developers": top_devs,
        "top_genre": top_genre,
        "top_genre_hours": top_genre_hours,
        "energy_score": energy_data.get("score", 0),
        "sleep_destroyer": analytics.get_sleep_destroyer(),
        "analogies": analytics.get_funny_analogies(),
        "genre_breakdown": genre_data,
    }

    return render_template("wrapped.html", **context)
