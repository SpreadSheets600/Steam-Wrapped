from datetime import datetime
from flask import current_app
import google.generativeai as genai
from collections import Counter, defaultdict

from app.utils.steam_client import get_game_achievements, get_game_details


class Analytics:
    def __init__(
        self, user_summary, owned_games, friends, badges, recent_games, steam_id
    ):
        self.user = user_summary
        self.games = owned_games.get("games", []) if owned_games else []
        self.friends = friends
        self.badges = badges if badges else []
        self.recent = recent_games.get("games", []) if recent_games else []
        self.steam_id = steam_id
        self.total_playtime_minutes = sum(
            g.get("playtime_forever", 0) for g in self.games
        )
        self.total_playtime_hours = self.total_playtime_minutes / 60

        self.top_games = sorted(
            self.games, key=lambda x: x.get("playtime_forever", 0), reverse=True
        )

    def get_playstyle_personality(self):
        api_key = current_app.config.get("GOOGLE_API_KEY")
        if not api_key:
            return {
                "title": "The Unknown Gamer",
                "desc": "A mystery wrapped in an enigma.",
                "emoji": "🎮",
            }

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        top_5_names = [g.get("name") for g in self.top_games[:5]]
        recent_names = [g.get("name") for g in self.recent[:5]]
        total_hours = int(self.total_playtime_hours)

        prompt = f"""
        Analyze this Steam user's gaming profile:
        Top 5 Games: {", ".join(top_5_names)}
        Recently Played: {", ".join(recent_names)}
        Total Hours: {total_hours}
        
        Based on this, assign them a "Personality Style" from these options:
        - Strategic Thinker (many strategy + RPG hours)
        - Chaos Enjoyer (FPS + action games)
        - Builder & Crafter (Terraria, Minecraft-like)
        - Completionist (achievement focused)
        - Explorer (variety of genres)
        - Speed Demon (racing/fast games)
        - Story Seeker (narrative games)
        - Social Butterfly (multiplayer focused)
        
        Provide a short, punchy description (max 15 words) explaining why.
        Also suggest an emoji that fits.
        Format: Title|Description|Emoji
        """

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            parts = text.split("|")
            if len(parts) >= 3:
                return {
                    "title": parts[0].strip(),
                    "desc": parts[1].strip(),
                    "emoji": parts[2].strip(),
                }
            elif len(parts) == 2:
                return {
                    "title": parts[0].strip(),
                    "desc": parts[1].strip(),
                    "emoji": "🎮",
                }
            else:
                return {"title": "The Gamer", "desc": text, "emoji": "🎮"}

        except Exception as e:
            print(f"AI Error: {e}")
            return {
                "title": "The Classic Gamer",
                "desc": "You love games, and that's what matters.",
                "emoji": "🎮",
            }

    def get_playtime_timeline(self):
        timeline = defaultdict(int)

        for game in self.games:
            last_played = game.get("rtime_last_played", 0)

            if last_played > 0:
                dt = datetime.fromtimestamp(last_played)
                key = dt.strftime("%Y-%m")

                timeline[key] += game.get("playtime_forever", 0) / 60

        sorted_timeline = sorted(timeline.items())

        if sorted_timeline:
            max_month = max(sorted_timeline, key=lambda x: x[1])
            min_month = min(sorted_timeline, key=lambda x: x[1])
        else:
            max_month = ("N/A", 0)
            min_month = ("N/A", 0)

        return {
            "data": [{"month": k, "hours": int(v)} for k, v in sorted_timeline[-12:]],
            "most_active": {"month": max_month[0], "hours": int(max_month[1])},
            "least_active": {"month": min_month[0], "hours": int(min_month[1])},
        }

    def get_top_games(self, limit=5):
        return self.top_games[:limit]

    def get_top_developers(self):
        developers = {}

        for game in self.top_games[:10]:
            details = get_game_details(game.get("appid"))
            playtime = game.get("playtime_forever", 0) / 60

            if details and "developers" in details:
                for dev in details["developers"]:
                    if dev not in developers:
                        developers[dev] = 0
                    developers[dev] += playtime

        sorted_devs = sorted(developers.items(), key=lambda x: x[1], reverse=True)[:5]
        return (
            [{"name": d[0], "hours": round(d[1], 1)} for d in sorted_devs]
            if sorted_devs
            else [{"name": "Unknown", "hours": 0}]
        )

    def get_genre_breakdown(self):
        genres = Counter()
        for game in self.top_games[:10]:
            details = get_game_details(game.get("appid"))

            if details and "genres" in details:
                for g in details["genres"]:
                    genres[g["description"]] += game.get("playtime_forever", 0)

            elif details and "genre" in details:
                genres[details["genre"]] += game.get("playtime_forever", 0)

        total = sum(genres.values())
        if total == 0:
            return {}

        result = {}
        for k, v in genres.most_common(5):
            result[k] = {"percent": int((v / total) * 100), "hours": int(v / 60)}
        return result

    def get_gaming_energy_score(self):
        hours_score = self.total_playtime_hours * 2
        games_score = len(self.games) * 10
        badges_score = len(self.badges) * 25

        score = int(hours_score + games_score + badges_score)
        percentile = min(99, max(1, int((score / 10000) * 100)))

        return {"score": score, "percentile": percentile}

    def get_achievement_stats(self):
        if not self.top_games:
            return None

        rarest = None
        top_game_name = self.top_games[0].get("name")
        rare_count = 0
        ultra_rare_count = 0

        for game in self.top_games[:5]:
            achievements = get_game_achievements(self.steam_id, game.get("appid"))

            if achievements:
                unlocked_achs = [a for a in achievements if a["achieved"]]

                for ach in unlocked_achs:
                    rarity = float(ach.get("rarity", 100) or 100)
                    if rarity <= 5:
                        ultra_rare_count += 1
                    elif rarity <= 25:
                        rare_count += 1

                if unlocked_achs:
                    game_rarest = min(
                        unlocked_achs, key=lambda x: float(x.get("rarity", 100) or 100)
                    )

                    if rarest is None or float(
                        game_rarest.get("rarity", 100) or 100
                    ) < float(rarest.get("rarity", 100) or 100):
                        rarest = game_rarest
                        top_game_name = game.get("name")

        top_game = self.top_games[0]
        achievements = get_game_achievements(self.steam_id, top_game.get("appid"))
        total = len(achievements) if achievements else 0
        unlocked = (
            len([a for a in achievements if a["achieved"]]) if achievements else 0
        )
        rate = int((unlocked / total) * 100) if total > 0 else 0

        return {
            "total_unlocked": unlocked,
            "completion_rate": rate,
            "rarest": rarest,
            "top_game_name": top_game_name,
            "top_game_total": total,
            "rare_count": rare_count,
            "ultra_rare_count": ultra_rare_count,
        }

    def get_achievement_score(self):
        total_unlocked = 0
        total_achievements = 0
        perfect_games = 0
        zero_achievement_games = 0
        best_game = {"name": "N/A", "rate": 0}

        for game in self.top_games[:5]:
            achievements = get_game_achievements(self.steam_id, game.get("appid"))
            if achievements:
                game_total = len(achievements)
                game_unlocked = len([a for a in achievements if a["achieved"]])
                total_achievements += game_total
                total_unlocked += game_unlocked

                if game_total > 0:
                    rate = int((game_unlocked / game_total) * 100)
                    if rate == 100:
                        perfect_games += 1
                    if rate > best_game["rate"]:
                        best_game = {"name": game.get("name"), "rate": rate}
                    if game_unlocked == 0:
                        zero_achievement_games += 1

        completion_rate = (
            int((total_unlocked / total_achievements) * 100)
            if total_achievements > 0
            else 0
        )

        return {
            "total_unlocked": total_unlocked,
            "completion_rate": completion_rate,
            "perfect_games": perfect_games,
            "zero_games": zero_achievement_games,
            "best_game": best_game,
            "rank_percentile": max(1, 100 - completion_rate),
        }

    def get_global_comparison(self):
        never_played = len([g for g in self.games if g.get("playtime_forever", 0) == 0])

        return {
            "hours": {
                "you": int(self.total_playtime_hours),
                "avg": 350,
            },
            "games": {"you": len(self.games), "avg": 24},
            "rare_achievements": {
                "you": "0.4%",
                "avg": "2.1%",
            },
            "never_played": {"you": never_played, "avg": 12},
        }

    def get_sleep_destroyer(self):
        days_lost = self.total_playtime_hours / 8
        played_games = len([g for g in self.games if g.get("playtime_forever", 0) > 0])
        unplayed_games = len(
            [g for g in self.games if g.get("playtime_forever", 0) == 0]
        )

        return {
            "days_lost": int(days_lost),
            "movies_watched": int(self.total_playtime_hours / 2.5),
            "anime_episodes": int(self.total_playtime_hours * 3),
            "games_played": played_games,
            "games_unplayed": unplayed_games,
            "skill_level_gained": int(self.total_playtime_hours / 10),
        }

    def get_funny_analogies(self):
        return [
            f"You could have binged {int(self.total_playtime_hours / 1.5)} episodes of your favorite show.",
            f"You could have read {int(self.total_playtime_hours / 8)} books from cover to cover.",
            f"You could have driven {int(self.total_playtime_hours / 4)} hours to visit friends.",
            f"You could have cooked {int(self.total_playtime_hours / 2)} homemade meals.",
        ]

    def get_games_categorized(self):
        played = []
        completed = []
        abandoned = []
        never_touched = []

        for game in self.games:
            playtime = game.get("playtime_forever", 0)
            if playtime == 0:
                never_touched.append(game)
            elif playtime > 600:
                completed.append(game)
            elif playtime > 60:
                played.append(game)
            else:
                abandoned.append(game)

        return {
            "played": len(played),
            "completed": len(completed),
            "abandoned": len(abandoned),
            "never_touched": len(never_touched),
        }

    def get_dashboard_stats(self):
        return {
            "total_playtime_hours": int(self.total_playtime_hours),
            "game_count": len(self.games),
            "pile_of_shame": len(
                [g for g in self.games if g.get("playtime_forever", 0) < 60]
            ),
            "never_played": len(
                [g for g in self.games if g.get("playtime_forever", 0) == 0]
            ),
            "level": 0,
            "xp": 0,
        }
