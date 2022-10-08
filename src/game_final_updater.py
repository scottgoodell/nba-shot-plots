from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.endpoints import shotchartdetail
import csv
import json
import os
import pandas

from helpers.delay import delay_between_1_and_2_secs
from services.google_storage_handler import GoogleStorageHandler


class GameFinalUpdater:

  def __init__(self) -> None:
    self.csv_path = "./game_finals.csv"
    self.season = "2022-23"
    self.season_type = "Pre Season"
    self.shot_type = "FGA"

    self._init_game_finals_csv()

  def update_game_finals(self):
    new_game_finals = []
    storage_client = GoogleStorageHandler()
    games = self._get_scoreboard_json()

    for game in games:
      if game["gameStatusText"] == "Final":
        game_update_context = self._update_game_final(game)

        if game_update_context["new_final"]:
          new_game_finals.append(game_update_context)

    storage_client.upload_object("nba-shot-plot-game-final-backup", "game_finals.csv")

    return new_game_finals

  def _update_game_final(self, game):
    game_id = game["gameId"]
    away_team_id = game["awayTeam"]["teamId"]
    home_team_id = game["homeTeam"]["teamId"]
    team_ids = [away_team_id, home_team_id]

    game_finals_df = pandas.read_csv(self.csv_path, dtype="str")
    unique_game_final_df = game_finals_df[game_finals_df["game_id"] == game_id]

    away_shot_data_available = self._is_shot_data_available(game_id, away_team_id)
    home_shot_data_available = self._is_shot_data_available(game_id, home_team_id)

    if unique_game_final_df.shape[0] == 1 or away_shot_data_available == False or home_shot_data_available == False:
      new_final = False
    else:
      new_final = True

      row = {
        "game_id": game_id,
        "game_date": game["gameCode"].split("/")[0],
        "away_team_id": away_team_id,
        "home_team_id": home_team_id,
      }

      df_new_row = game_finals_df.append(row, ignore_index = True)
      df_new_row.to_csv(self.csv_path, index = False)

    return {
      "game_id": game_id,
      "new_final": new_final,
      "team_ids": team_ids
    }

  def _get_scoreboard_json(self):
    f = open(f"./fixtures/scoreboard_final.json")
    data = json.load(f)
    return data.get("scoreboard", {}).get("games", [])

  def _get_scoreboard(self):
    data = scoreboard.ScoreBoard()
    return data.get("scoreboard", {}).get("games", [])

  # get player_ids from team_id to loop through shotchartdetail
  def _get_player_ids_from_team_id(self, team_id):
    delay_between_1_and_2_secs()
    team_roster_response = commonteamroster.CommonTeamRoster(season = "2022-23", team_id = team_id)
    team_roster_json = json.loads(team_roster_response.get_json())
    team_roster_data = team_roster_json["resultSets"][0]["rowSet"]

    return [player[-1] for player in team_roster_data]

  # return true if the players shot datas are available - should just be at least one?
  def _is_shot_data_available(self, game_id, team_id) -> bool:
    player_ids = self._get_player_ids_from_team_id(team_id)
    for player_id in player_ids:
      delay_between_1_and_2_secs()
      shot_json = shotchartdetail.ShotChartDetail(
        team_id = team_id,
        player_id = player_id,
        game_id_nullable = game_id,
        context_measure_simple = self.shot_type,
        season_nullable = self.season,
        season_type_all_star = self.season_part
      )
      shot_data = json.loads(shot_json.get_json())
      shot_values = shot_data['resultSets'][0]['rowSet']
      
      if len(shot_values) > 0:
        return True
      
    return False

  def _init_game_finals_csv(self):
    columns = ["game_id", "game_date", "away_team_id", "home_team_id"]

    if not os.path.exists(self.csv_path):
      print("Creating new csv for game finals")
      with open(self.csv_path, 'w', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(columns)
        file.close()
