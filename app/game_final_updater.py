from nba_api.live.nba.endpoints import scoreboard
import csv
import json
import os
import pandas


class GameFinalUpdater:

  def __init__(self) -> None:
    self.csv_path = "./game_finals.csv"
    
    self._init_game_finals_csv()
    self.df = pandas.read_csv(self.csv_path, dtype="str")

  def update_game_finals(self):
    new_game_finals = []
    games = self._get_scoreboard_json()

    for game in games:
      if game["gameStatusText"] == "Final":
        game_update_context = self._update_game_final(game)

        if game_update_context["new_final"]:
          new_game_finals.append(game_update_context)

    return new_game_finals

  def _update_game_final(self, game):
    game_id = game["gameId"]
    away_team_id = game["awayTeam"]["teamId"]
    home_team_id = game["homeTeam"]["teamId"]
    team_ids = [away_team_id, home_team_id]
    game_final_df = self.df.loc[self.df["game_id"] == game_id]
    
    if game_final_df.shape[0] == 1:
      new_final = False
    else:
      new_final = True
      
      row = {
        "game_id": game_id,
        "game_date": game["gameCode"].split("/")[0],
        "away_team_id": away_team_id,
        "home_team_id": home_team_id,
      }

      df_new_row = self.df.append(row, ignore_index = True)
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
  
  def _init_game_finals_csv(self):
    columns = ["game_id", "game_date", "away_team_id", "home_team_id"]
    
    if not os.path.exists(self.csv_path):
      print("Creating new csv for game finals")
      with open(self.csv_path, 'w', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(columns)
        file.close()
