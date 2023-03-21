import obspython as obs
import os.path
from steam_achievements import SteamAchievements


DEFAULT_OUTPUT_TEMPLATE = ("Currently Playing: #current_game#\n"
                           "Game  Completion : #current_game_completion#\n")

api_key = ""
steam_id = ""
update_when_playing = True
time = 10
amount_of_games = 10
width_of_games = 17
output_template = DEFAULT_OUTPUT_TEMPLATE

def clear_cache(props, prop):
    if os.path.isfile("games_without_achievements.txt"):
        os.remove("games_without_achievements.txt")

# Script
def script():
    global api_key, steam_id, update_when_playing, output_template, amount_of_games, width_of_games

    if api_key != "" and steam_id != "":
        steam_achieve = SteamAchievements(api_key, steam_id)
        current_game = steam_achieve.current_game
        if not update_when_playing or (update_when_playing and current_game != None):
            steam_achieve.get_steam_achievements()
            steam_achieve.generate_result(output_template)
        obs.timer_remove(script)
        obs.remove_current_callback()
        obs.timer_add(script, time*60000)
    else:
        obs.timer_remove(script)
        obs.remove_current_callback()

def script_load(settings):
    obs.timer_add(script, time*60000)

# Description displayed in the Scripts dialog window
def script_description():
    return """<center><h2>Steam achievements board</h2></center>
              <p>This script allows you to display your steam achievements and some calculated values in your stream.</p>
              <p>Available tags for output template:</p>
              <p>#current_game#, #current_game_completion#</p>"""

# Called to set default values of data settings
def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "api_key", "")
    obs.obs_data_set_default_string(settings, "steam_id", "")
    obs.obs_data_set_default_bool(settings, "update_when_playing", True)
    obs.obs_data_set_default_int(settings, "time", 10)
    obs.obs_data_set_default_int(settings, "amount_of_games", 10)
    obs.obs_data_set_default_int(settings, "width_of_games", 17)
    obs.obs_data_set_default_string(settings, "output_template", DEFAULT_OUTPUT_TEMPLATE)

# Called to display the properties GUI
def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_button(props, "clear_cache", "Clear Cache", clear_cache)
    obs.obs_properties_add_text(props, "api_key", "API Key", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "steam_id", "Steam ID", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_bool(props, "update_when_playing", "Only update when playing")
    obs.obs_properties_add_int(props, "time", "Time between executes (in minutes)", 1, 60, 1)
    obs.obs_properties_add_int(props, "amount_of_games", "Amount of highest ranked games", 1, 100, 1)
    obs.obs_properties_add_int(props, "width_of_games", "Width of highest ranked games", 1, 100, 1)
    obs.obs_properties_add_text(props, "output_template", "Output Template", obs.OBS_TEXT_MULTILINE)
  
    return props

# Called after change of settings including once after script load
def script_update(settings):
    global api_key, steam_id, update_when_playing, time, amount_of_games, width_of_games, output_template

    obs.timer_remove(script)
    obs.remove_current_callback()

    api_key = obs.obs_data_get_string(settings, "api_key")
    steam_id = obs.obs_data_get_string(settings, "steam_id")
    update_when_playing = obs.obs_data_get_bool(settings, "update_when_playing")
    time = obs.obs_data_get_int(settings, "time")
    amount_of_games = obs.obs_data_get_int(settings, "amount_of_games")
    width_of_games = obs.obs_data_get_int(settings, "width_of_games")
    output_template = obs.obs_data_get_string(settings, "output_template")

    script()
    obs.timer_add(script, time*60000)

# Called before data settings are saved
def script_save(settings):
    obs.obs_save_sources()

def script_unload():
    obs.timer_remove(script)
