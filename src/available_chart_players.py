import importlib
import json

from nba_api.stats.endpoints import commonteamroster

from helpers.delay import delay_between_1_and_2_secs


PLAYER_CATEGORIES = ["rookies", "sophomores"]

def available_chart_players(team_id):

  def _get_team_roster_player_ids(team_id):
    delay_between_1_and_2_secs()
    team_roster_response = commonteamroster.CommonTeamRoster(season = "2021-22", team_id = team_id)
    team_roster_json = json.loads(team_roster_response.get_json())
    team_roster_data = team_roster_json["resultSets"][0]["rowSet"]

    return [player[-1] for player in team_roster_data]
  
  team_roster_player_ids = _get_team_roster_player_ids(team_id)
  chart_players = []
  for category in PLAYER_CATEGORIES:
    players_module = importlib.import_module(f"static.{category}")
    players = getattr(players_module, category)

    for player in players:
      if player["active"] and player["id"] in team_roster_player_ids:
        data = {
          "player_id": player["id"],
          "team_id": team_id,
          "category": category
        }

        chart_players.append(data)

  return chart_players
