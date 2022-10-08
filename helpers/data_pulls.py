import json
from nba_api.live.nba.endpoints import boxscore
from nba_api.stats.endpoints import shotchartdetail

from helpers.delay import delay_between_1_and_2_secs

def player_game_shot_data(
  team_id,
  player_id,
  game_id,
  shot_type,
  season,
  season_part
):
  delay_between_1_and_2_secs()
  shot_json = shotchartdetail.ShotChartDetail(
    team_id = team_id,
    player_id = player_id,
    game_id_nullable = game_id,
    context_measure_simple = shot_type,
    season_nullable = season,
    season_type_all_star = season_part
  )
  shot_data = json.loads(shot_json.get_json())
  shot_values = shot_data['resultSets'][0]['rowSet']

  return shot_values

def get_game_boxscore(game_id):
  delay_between_1_and_2_secs()
  data = boxscore.BoxScore(game_id)

  return data.game.get_dict()
