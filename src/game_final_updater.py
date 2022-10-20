from helpers.data_pulls import get_game_boxscore, get_game_summary, player_game_shot_data
from nba_api.live.nba.endpoints import scoreboard
import csv
import json
import os
import pandas

from helpers.delay import delay_between_1_and_2_secs
from services.google_storage_handler import GoogleStorageHandler
from static.defaults import Defaults


class GameFinalUpdater:

  def __init__(self) -> None:
    self.csv_path = "./game_finals.csv"
    self.season = Defaults.SEASON
    self.season_part = Defaults.SEASON_PART
    self.shot_type = Defaults.SHOT_TYPE

    self._init_game_finals_csv()

  def update_game_finals(self):
    new_game_finals = []
    storage_client = GoogleStorageHandler()
    games = self._get_scoreboard()

    for game in games:
      print(f"Evaluating game {game['gameId']}..")
      if "final" in game["gameStatusText"].lower():
        away_score = game["awayTeam"]["score"]
        home_score = game["homeTeam"]["score"]

        if away_score != home_score:
          game_update_context = self._update_game_final(game)

          if game_update_context["new_final"]:
            new_game_finals.append(game_update_context)

    if len(new_game_finals) > 0:
      storage_client.upload_object("nba-shot-plot-game-final-backup", "game_finals.csv")

    return new_game_finals

  def _update_game_final(self, game):
    game_id = game["gameId"]
    away_team_id = game["awayTeam"]["teamId"]
    home_team_id = game["homeTeam"]["teamId"]
    team_ids = [away_team_id, home_team_id]
    away_shot_data_available = False
    home_shot_data_available = False

    game_finals_df = pandas.read_csv(self.csv_path, dtype="str")
    unique_game_final_df = game_finals_df[game_finals_df["game_id"] == game_id]

    if unique_game_final_df.shape[0] == 0:
      away_shot_data_available = self._is_shot_data_available(game_id, away_team_id)
      home_shot_data_available = self._is_shot_data_available(game_id, home_team_id)

    if away_shot_data_available == False or home_shot_data_available == False:
      new_final = False
    else:
      new_final = True

      row = {
        "game_id": game_id,
        "game_date": game["gameCode"].split("/")[0],
        "away_team_id": away_team_id,
        "home_team_id": home_team_id,
      }

      df_new_row = pandas.concat([game_finals_df, pandas.DataFrame(row, index=[0])])
      df_new_row.to_csv(self.csv_path, index = False)
      print(f"Added new game with id: {game_id} to csv..")

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
    delay_between_1_and_2_secs()
    data = scoreboard.ScoreBoard().get_dict()
    return data.get("scoreboard", {}).get("games", [])

  def _is_shot_data_available(self, game_id, team_id) -> bool:
    game_summary = get_game_summary(game_id)

    if game_summary is None or len(game_summary[0]["rowSet"]) == 0:
      return False

    if "final" not in game_summary[0]["rowSet"][0][4].lower():
      return False

    boxscore_data = get_game_boxscore(game_id)

    if len(boxscore_data[0]["rowSet"]) == 0:
      return False

    player_boxscore_data = [stat_set for stat_set in boxscore_data if stat_set["name"] == "PlayerStats"][0]
    team_player_boxscore_data = [stat_line for stat_line in player_boxscore_data["rowSet"] if stat_line[1] == team_id]

    player_id = 0
    shots_attempted = 0
    for player in team_player_boxscore_data:
      field_goals_attempted = player[11]

      if field_goals_attempted is None:
        continue

      if field_goals_attempted > shots_attempted:
        shots_attempted = field_goals_attempted
        player_id = player[4]

    if player_id == 0:
      return False

    shot_values = player_game_shot_data(
      team_id = team_id,
      player_id = player_id,
      game_id = game_id,
      shot_type = self.shot_type,
      season = self.season,
      season_part = self.season_part
    )

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
