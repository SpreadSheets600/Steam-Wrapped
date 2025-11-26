import re
import requests
from app.db import db
from flask import (
    Blueprint,
    request,
    session,
    redirect,
    url_for,
)

from app.models import User
from app.utils.steam_client import get_user_summary

auth_bp = Blueprint("auth", __name__)

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"


@auth_bp.route("/login")
def login():
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": url_for("auth.authorize", _external=True),
        "openid.realm": url_for("views.index", _external=True),
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    query_string = requests.compat.urlencode(params)
    auth_url = f"{STEAM_OPENID_URL}?{query_string}"

    return redirect(auth_url)


@auth_bp.route("/authorize")
def authorize():
    params = request.args.copy()
    params["openid.mode"] = "check_authentication"

    response = requests.post(STEAM_OPENID_URL, data=params)

    if "is_valid:true" in response.text:
        steam_id = re.search(
            r"https://steamcommunity.com/openid/id/(\d+)", params["openid.claimed_id"]
        ).group(1)
        session["steam_id"] = steam_id

        try:
            user_summary = get_user_summary(steam_id)

            if user_summary:
                user = User.query.filter_by(steam_id=steam_id).first()

                if not user:
                    user = User(steam_id=steam_id)
                    db.session.add(user)

                user.username = user_summary.get("personaname")
                user.avatar_url = user_summary.get("avatarfull")
                db.session.commit()

        except Exception as e:
            print(f"Error saving user: {e}")

        return redirect(url_for("views.generating"))

    return "Login Failed", 401


@auth_bp.route("/logout")
def logout():
    session.pop("steam_id", None)

    return redirect(url_for("views.index"))
