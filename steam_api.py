import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from steam_web_api import Steam

load_dotenv()

API_KEY = os.getenv("STEAM_API_KEY", "")
print(API_KEY)

steam_client = Steam(API_KEY) if API_KEY else None


def get_json(url):
    try:
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            return r.json()

    except requests.RequestException:
        return None

    return None


def safe_get_json(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        return r.json()

    except Exception as e:
        print(f"Failed to get JSON from {url}: {e}")
        return None


def get_badge_info(badgeid, steamid):
    badge_page = f"https://steamcommunity.com/profiles/{steamid}/badges/{badgeid}"

    html = requests.get(badge_page).text
    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.find("div", class_="badge_info_title")
    badge_name = name_tag.text.strip() if name_tag else f"Badge {badgeid}"

    img_tag = soup.find("img", class_="badge_icon")
    badge_img = img_tag["src"] if img_tag else None

    return {"name": badge_name, "image": badge_img}


def get_user_summary(steam_id):
    if not steam_client:
        return None

    try:
        user = steam_client.users.get_user_details(steam_id)
        return user.get("player")

    except Exception as e:
        print(f"Error getting user summary: {e}")
        return None


def get_friends_list(steam_id):
    if not steam_client:
        return None

    try:
        friends = steam_client.users.get_user_friends_list(steam_id)
        return {
            "friend_count": len(friends.get("friends", [])),
            "friends": friends.get("friends", []),
        }

    except Exception as e:
        print(f"Error getting friends list: {e}")
        return None


def get_owned_games(steam_id):
    if not steam_client:
        return None

    try:
        games = steam_client.users.get_owned_games(steam_id, include_appinfo=True)
        return games

    except Exception as e:
        print(f"Error getting owned games: {e}")
        return None


def get_recent_games(steam_id):
    if not steam_client:
        return None

    try:
        recent = steam_client.users.get_user_recently_played_games(steam_id)
        return recent

    except Exception as e:
        print(f"Error getting recent games: {e}")
        return None


def get_badges(steam_id):
    if not steam_client:
        return None

    try:
        badges = steam_client.users.get_user_badges(steam_id).get("badges", [])

        for badge in badges:
            badge_id = badge.get("badgeid")

            badge_info = get_badge_info(badge_id, steam_id)

            badge["name"] = badge_info.get("name")
            badge["image"] = badge_info.get("image")

        return badges

    except Exception as e:
        print(f"Error getting badges: {e}")
        return None


def get_steam_level(steam_id):
    if not steam_client:
        return None

    try:
        level = steam_client.users.get_user_steam_level(steam_id)
        return level

    except Exception as e:
        print(f"Error getting Steam level: {e}")
        return None


def get_game_details(appid):
    details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=en"
    spy_data_url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"

    try:
        details_response = requests.get(details_url).json()
        spy_data_response = requests.get(spy_data_url).json()

        genre = spy_data_response.get("genre", "")
        owners = spy_data_response.get("owners")

        data = details_response.get(str(appid), {}).get("data")
        if data is None:
            return None

        data["genre"] = genre
        if owners:
            data["owners"] = owners

        return data

    except Exception as e:
        print(f"Error fetching store info for {appid}: {e}")
        return None


def get_game_achievements(steam_id, appid, api_key=API_KEY):
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


def find_rarest_achievement(games_list, steam_id):
    rarest_ach = None
    rarest_percent = 100.0
    rarest_game_name = ""

    for g in games_list[:5]:
        appid = g.get("appid")
        player_ach_data = get_game_achievements(steam_id, appid)

        if not player_ach_data or not player_ach_data.get("playerstats", {}).get(
            "success"
        ):
            continue

        player_achs = player_ach_data["playerstats"].get("achievements", [])

        unlocked = {
            a["apiname"]: a.get("name", a["apiname"])
            for a in player_achs
            if a["achieved"] == 1
        }

        if not unlocked:
            continue

        global_ach_data = safe_get_json(
            f"https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/?gameid={appid}"
        )

        if not global_ach_data or "achievementpercentages" not in global_ach_data:
            continue

        global_achs = global_ach_data["achievementpercentages"]["achievements"]

        for ga in global_achs:
            if ga["name"] in unlocked:
                if float(ga["percent"]) < rarest_percent:
                    rarest_percent = float(ga["percent"])
                    rarest_ach = unlocked[ga["name"]]
                    rarest_game_name = g.get("name")

    return rarest_game_name, rarest_ach, rarest_percent
