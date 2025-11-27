from flask import Blueprint, render_template, session, redirect, url_for, request

from app.utils.steam_client import (
    get_user_summary,
    get_friends_list,
    get_owned_games,
    get_recent_games,
    get_badges,
    get_steam_level,
)
from app.utils.analytics import Analytics
from app.db import db
from app.models import User, WrappedShare

views_bp = Blueprint("views", __name__)


def build_wrapped_context(steam_id):
    user = get_user_summary(steam_id)
    friends = get_friends_list(steam_id)
    games = get_owned_games(steam_id)
    recent = get_recent_games(steam_id)
    badges = get_badges(steam_id)

    if not user:
        return None

    analytics = Analytics(user, games, friends, badges, recent, steam_id)

    genre_data = analytics.get_genre_breakdown()
    top_genre = list(genre_data.keys())[0] if genre_data else "Unknown"
    top_genre_hours = (
        genre_data[top_genre]["hours"] if genre_data and top_genre in genre_data else 0
    )

    top_devs = analytics.get_top_developers()
    stats = analytics.get_dashboard_stats()
    energy_data = analytics.get_gaming_energy_score()
    top_games_five = analytics.get_top_games(5)
    top_game = top_games_five[0] if top_games_five else None

    return {
        "user": user,
        "stats": stats,
        "top_game": top_game,
        "top_5_games": top_games_five,
        "top_developers": top_devs,
        "top_genre": top_genre,
        "top_genre_hours": top_genre_hours,
        "energy_score": energy_data.get("score", 0),
        "sleep_destroyer": analytics.get_sleep_destroyer(),
        "analogies": analytics.get_funny_analogies(),
        "genre_breakdown": genre_data,
    }


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

    share_entry = (
        WrappedShare.query.filter_by(steam_id=steam_id)
        .order_by(WrappedShare.created_at.desc())
        .first()
    )
    share_url = (
        url_for("views.view_wrapped_share", slug=share_entry.slug, _external=True)
        if share_entry
        else None
    )

    return render_template("dashboard.html", **context, share_url=share_url)


@views_bp.route("/wrapped")
def wrapped():
    if "steam_id" not in session:
        return redirect(url_for("views.index"))

    steam_id = session["steam_id"]
    context = build_wrapped_context(steam_id)

    if not context:
        return "Unable to generate wrapped summary", 500

    share_entry = (
        WrappedShare.query.filter_by(steam_id=steam_id)
        .order_by(WrappedShare.created_at.desc())
        .first()
    )
    share_url = (
        url_for("views.view_wrapped_share", slug=share_entry.slug, _external=True)
        if share_entry
        else None
    )

    auto_copy = request.args.get("copied") == "1" and bool(share_url)

    return render_template(
        "wrapped.html",
        **context,
        can_share=True,
        share_url=share_url,
        auto_copy=auto_copy,
    )


@views_bp.route("/wrapped/share", methods=["POST"])
def create_wrapped_share():
    if "steam_id" not in session:
        return redirect(url_for("views.index"))

    steam_id = session["steam_id"]
    context = build_wrapped_context(steam_id)

    if not context:
        return "Unable to create shareable Wrapped", 500

    share_entry = (
        WrappedShare.query.filter_by(steam_id=steam_id)
        .order_by(WrappedShare.created_at.desc())
        .first()
    )

    if share_entry:
        share_entry.payload = context
    else:
        user = User.query.filter_by(steam_id=steam_id).first()
        share_entry = WrappedShare(steam_id=steam_id, user=user, payload=context)
        db.session.add(share_entry)

    db.session.commit()

    return redirect(url_for("views.wrapped", copied=1))


@views_bp.route("/wrapped/shared/<slug>")
def view_wrapped_share(slug):
    share_entry = WrappedShare.query.filter_by(slug=slug).first_or_404()
    payload = share_entry.payload or {}

    share_url = url_for("views.view_wrapped_share", slug=slug, _external=True)

    return render_template(
        "share.html",
        **payload,
        can_share=False,
        share_url=share_url,
        shared_at=share_entry.created_at,
    )
