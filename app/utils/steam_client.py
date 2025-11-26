import requests
from bs4 import BeautifulSoup
from steam_web_api import Steam

from app import cache
from flask import current_app


steam_client = None


def get_steam_client():
    global steam_client
    if not steam_client:
        api_key = current_app.config["STEAM_API_KEY"]
        if api_key:
            steam_client = Steam(api_key)
    return steam_client


def safe_get_json(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        return r.json()

    except Exception as e:
        print(f"Failed to get JSON from {url}: {e}")
        return None


@cache.memoize(timeout=86400)
def get_badge_info(badgeid, steamid):
    badge_page = f"https://steamcommunity.com/profiles/{steamid}/badges/{badgeid}"

    try:
        html = requests.get(badge_page).text
        soup = BeautifulSoup(html, "html.parser")
        name_tag = soup.find("div", class_="badge_info_title")
        badge_name = name_tag.text.strip() if name_tag else f"Badge {badgeid}"
        img_tag = soup.find("img", class_="badge_icon")
        badge_img = img_tag["src"] if img_tag else None

        return {"name": badge_name, "image": badge_img}

    except Exception:
        return {"name": f"Badge {badgeid}", "image": None}


@cache.memoize(timeout=3600)
def get_user_summary(steam_id):
    client = get_steam_client()

    if not client:
        return None

    try:
        user = client.users.get_user_details(steam_id)
        return user.get("player")

    except Exception as e:
        print(f"Error getting user summary: {e}")
        return None


@cache.memoize(timeout=3600)
def get_friends_list(steam_id):
    client = get_steam_client()

    if not client:
        return None

    try:
        friends = client.users.get_user_friends_list(steam_id)
        return {
            "friend_count": len(friends.get("friends", [])),
            "friends": friends.get("friends", []),
        }

    except Exception as e:
        print(f"Error getting friends list: {e}")
        return None


@cache.memoize(timeout=3600)
def get_owned_games(steam_id):
    client = get_steam_client()
    if not client:
        return None

    try:
        games = client.users.get_owned_games(steam_id, include_appinfo=True)
        return games

    except Exception as e:
        print(f"Error getting owned games: {e}")
        return None


@cache.memoize(timeout=3600)
def get_recent_games(steam_id):
    client = get_steam_client()

    if not client:
        return None

    try:
        recent = client.users.get_user_recently_played_games(steam_id)
        return recent

    except Exception as e:
        print(f"Error getting recent games: {e}")
        return None


@cache.memoize(timeout=86400)
def get_badges(steam_id):
    client = get_steam_client()

    if not client:
        return None

    try:
        badges_resp = client.users.get_user_badges(steam_id)
        badges = badges_resp.get("badges", [])

        processed_badges = []

        for badge in badges[:10]:
            badge_id = badge.get("badgeid")
            badge_info = get_badge_info(badge_id, steam_id)
            badge["name"] = badge_info.get("name")
            badge["image"] = badge_info.get("image")
            processed_badges.append(badge)

        return processed_badges

    except Exception as e:
        print(f"Error getting badges: {e}")
        return None


@cache.memoize(timeout=3600)
def get_steam_level(steam_id):
    client = get_steam_client()

    if not client:
        return None

    try:
        level = client.users.get_user_steam_level(steam_id)
        return level

    except Exception as e:
        print(f"Error getting Steam level: {e}")
        return None


@cache.memoize(timeout=86400 * 7)  # Cache for a week
def get_game_details(appid):
    details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=en"
    spy_data_url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"

    try:
        details_response = requests.get(details_url).json()

        try:
            spy_data_response = requests.get(spy_data_url, timeout=5).json()
            genre = spy_data_response.get("genre", "")
            owners = spy_data_response.get("owners")
            tags = spy_data_response.get("tags", {})

        except Exception:
            genre = ""
            owners = ""
            tags = {}

        data = details_response.get(str(appid), {}).get("data")
        if data is None:
            return None

        data["genre"] = genre
        data["tags"] = tags
        if owners:
            data["owners"] = owners

        return data
    except Exception as e:
        print(f"Error fetching store info for {appid}: {e}")
        return None


@cache.memoize(timeout=86400)
def get_game_achievements(steam_id, appid):
    api_key = current_app.config["STEAM_API_KEY"]
    url_player = (
        f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"
        f"?appid={appid}&key={api_key}&steamid={steam_id}"
    )

    player_raw = safe_get_json(url_player)

    if not player_raw or "playerstats" not in player_raw:
        return []

    if not player_raw["playerstats"].get("success", True):
        return []

    player_achs = player_raw["playerstats"].get("achievements", [])
    player_map = {a["apiname"]: a for a in player_achs}

    url_schema = (
        f"https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/"
        f"?key={api_key}&appid={appid}"
    )

    schema_raw = safe_get_json(url_schema)
    schema_achs = (
        schema_raw.get("game", {}).get("availableGameStats", {}).get("achievements", [])
        if schema_raw
        else []
    )

    url_rarity = (
        f"https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
        f"?gameid={appid}"
    )

    rarity_raw = safe_get_json(url_rarity)
    global_rarity = (
        {
            a["name"]: a["percent"]
            for a in rarity_raw.get("achievementpercentages", {}).get(
                "achievements", []
            )
        }
        if rarity_raw
        else {}
    )

    final = []
    for ach in schema_achs:
        apiname = ach["name"]
        final.append(
            {
                "api_name": apiname,
                "display_name": ach.get("displayName"),
                "description": ach.get("description"),
                "icon": ach.get("icon"),
                "icon_gray": ach.get("icongray"),
                "hidden": ach.get("hidden", 0),
                "achieved": player_map.get(apiname, {}).get("achieved", 0),
                "unlock_time": player_map.get(apiname, {}).get("unlocktime", 0),
                "rarity": global_rarity.get(apiname),
            }
        )

    return final
