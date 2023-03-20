import time, grequests, requests, logging, math, os.path


class SteamAchievements:
    def __init__(self, api_key, steam_id):
        self.api_key = api_key
        self.steam_id = steam_id
        self.current_game = ""
        self.games_without_achievements = []
        self._get_games_without_achievements()
        self.games_with_achievements = []
        self.stats = {}

    def get_current_game(self):
        player_summary = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={self.api_key}&steamids={self.steam_id}").json()["response"]["players"][0]
        if "gameid" in player_summary:
            self.current_game = player_summary["gameextrainfo"]

    def _get_games_without_achievements(self):
        if os.path.isfile("games_without_achievements.txt"):
            f = open("games_without_achievements.txt", "r")
            lines = f.readlines()

            for line in lines:
                self.games_without_achievements.append(line.replace("\n", ""))

            f.close()

    def _save_game_without_achievements(self, game_name):
        if game_name not in self.games_without_achievements:
            self.games_without_achievements.append(game_name)
            f = open("games_without_achievements.txt", "a")
            f.write(game_name + "\n")
            f.close()

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
            urls.append(f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={self.api_key}&steamid={self.steam_id}&appid={str(game['appid'])}")

        # request stuff
        rs = (grequests.get(u) for u in urls)
        responses = grequests.map(rs)

        for response in responses:
            game_stats = response.json()["playerstats"]

            if "achievements" in game_stats:
                achieved_achievements = self._get_achieved_achievements(game_stats["achievements"])
                total_achievements = len(game_stats["achievements"])
                game_completion = (achieved_achievements / total_achievements) * 100

                self.stats = [game_stats["gameName"]] = game_completion

            elif "gameName" in game_stats:
                self._save_game_without_achievements(game_stats["gameName"])
        
        logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)
        logging.info(f"Gathered achievement info for {str(len(owned_games))} games in {str(time.time() - start_time)} seconds")

    def get_steam_completion(self, game_achievements):
        # https://steamcommunity.com/sharedfiles/filedetails/?id=650166273
        
        total_percentage = sum(game_completion for game_completion in game_achievements.values() if round(game_completion) != 0)
        started_games = sum(1 for game_completion in game_achievements.values() if round(game_completion) != 0)

        return math.floor((total_percentage/started_games))

    def get_real_completion(self, game_achievements):
        total_percentage = sum(game_completion for game_completion in game_achievements.values())
        total_games = len(game_achievements)

        return round((total_percentage/total_games), 2)

