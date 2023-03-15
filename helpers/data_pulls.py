import json
from nba_api.stats.endpoints import boxscoresummaryv2
from nba_api.stats.endpoints import boxscoretraditionalv2
from nba_api.stats.endpoints import shotchartdetail

from helpers.utils import delay_between_1_and_2_secs

def player_game_shot_data(
  team_id,
  player_id,
  game_id,
  shot_type,
  season,
  season_part
):
  delay_between_1_and_2_secs()
  try:
    shot_json = shotchartdetail.ShotChartDetail(
      team_id = team_id,
      player_id = player_id,
      game_id_nullable = game_id,
      context_measure_simple = shot_type,
      season_nullable = season,
      season_type_all_star = season_part
    )
    shot_data = json.loads(shot_json.get_json())
    shot_values = shot_data["resultSets"][0]["rowSet"]

    return shot_values
  except Exception as e:
    print(f"Game shot data failed: {e}")
    return []

def get_game_boxscore(game_id):
  delay_between_1_and_2_secs()
  try:
    data = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id = game_id)

    return data.get_dict()["resultSets"]
  except Exception as e:
    print(f"Game boxscore failed: {e}")
    return

def get_game_summary(game_id):
  delay_between_1_and_2_secs()
  try:
    data = boxscoresummaryv2.BoxScoreSummaryV2(game_id = game_id)

    return data.get_dict()["resultSets"]
  except Exception as e:
    print(f"Game summary failed: {e}")
    return
