import time, grequests, requests, logging, math, os.path


class SteamAchievements:
    def __init__(self, api_key, steam_id):
        self.api_key = api_key
        self.steam_id = steam_id
        self.current_game = None
        self.get_current_game()
        self.games_without_achievements = []
        self._get_games_without_achievements()
        self.games_with_achievements = []
        self.stats = {}

    def get_current_game(self):
        player_summary = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={self.api_key}&steamids={self.steam_id}").json()["response"]["players"][0]
        if "gameextrainfo" in player_summary:
            self.current_game = player_summary["gameextrainfo"]

    def _get_games_without_achievements(self):
        if os.path.isfile("games_without_achievements.txt"):
            with open("games_without_achievements.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    self.games_without_achievements.append(line.replace("\n", ""))

    def _save_game_without_achievements(self, game_name):
        if game_name not in self.games_without_achievements:
            self.games_without_achievements.append(game_name)
            with open("games_without_achievements.txt", "a") as f:
                f.write(game_name + "\n")

    def _filter_games_without_achievements(self, games):
        for game in games:
            # check if game has stats
            if "has_community_visible_stats" not in game:
                self._save_game_without_achievements(game["name"])
            else:
                self.games_with_achievements.append(game)

    @staticmethod
    def _get_achieved_achievements(achievements):
        result = 0
        for achievement in achievements:
            result += achievement["achieved"]
        return result

    def get_steam_achievements(self):
        start_time = time.time()
        owned_games = requests.get(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={self.api_key}&steamid={self.steam_id}&include_played_free_games=true&include_appinfo=true").json()["response"]["games"]
        self._filter_games_without_achievements(owned_games)

        # create request urls
        urls = []
        for game in self.games_with_achievements:
            urls.append(f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={self.api_key}&steamid={self.steam_id}&appid={game['appid']}")

        # request stuff
        rs = (grequests.get(u) for u in urls)
        responses = grequests.map(rs)

        for response in responses:
            game_stats = response.json()["playerstats"]

            if "achievements" in game_stats:
                achieved_achievements = self._get_achieved_achievements(game_stats["achievements"])
                total_achievements = len(game_stats["achievements"])

                self.stats[game_stats["gameName"]] = {"completed_achievements": achieved_achievements, "total_achievements": total_achievements}

            elif "gameName" in game_stats:
                self._save_game_without_achievements(game_stats["gameName"])
        
        logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)
        logging.info(f"Gathered achievement info for {str(len(owned_games))} games in {str(time.time() - start_time)} seconds")

    def generate_result(self, template):
        if self.current_game != None:
            template = template.replace("#current_game#", self.current_game)
            template = template.replace("#current_game_completion#", f"{self.stats[self.current_game]['completed_achievements']} / {self.stats[self.current_game]['total_achievements']}")
            with open("achievements.txt", "wb") as f:
                f.write((template).encode('utf8'))

    def get_steam_completion(self, game_achievements):
        # https://steamcommunity.com/sharedfiles/filedetails/?id=650166273
        
        total_percentage = sum(game_completion for game_completion in game_achievements.values() if round(game_completion) != 0)
        started_games = sum(1 for game_completion in game_achievements.values() if round(game_completion) != 0)

        return math.floor((total_percentage/started_games))

    def get_real_completion(self, game_achievements):
        total_percentage = sum(game_completion for game_completion in game_achievements.values())
        total_games = len(game_achievements)

        return round((total_percentage/total_games), 2)
