from nba_api.live.nba.endpoints import scoreboard
import json
from prisma import Prisma


class GameFinalUpdater:

  def __init__(self) -> None:
    self.db = Prisma()

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
    self.db.connect()

    game_final = self.db.gamefinal.find_unique(
      where = {
        "game_id": game["gameId"]
      },
    )
    if game_final:
      game_id = game_final.game_id
      new_final = False
      team_ids = [game_final.away_team_id, game_final.home_team_id]
    else:
      new_game_final = self.db.gamefinal.create({
        "game_id": game["gameId"],
        "game_date": game["gameCode"].split("/")[0],
        "away_team_id": int(game["awayTeam"]["teamId"]),
        "home_team_id": int(game["homeTeam"]["teamId"]),
      })

      game_id = new_game_final.game_id
      new_final = True
      team_ids = [new_game_final.away_team_id, new_game_final.home_team_id]

    self.db.disconnect()

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
