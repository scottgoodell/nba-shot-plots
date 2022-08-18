import importlib

    
PLAYER_CATEGORIES = ["rookies"]    

def available_chart_players(team_id):
  chart_players = []
  for category in PLAYER_CATEGORIES:
    players_module = importlib.import_module(f"static.{category}")
    players = getattr(players_module, category)
    
    for player in players:
      if player["team_id"] == team_id:
        data = {
          "player_id": player["id"],
          "team_id": player["team_id"],
          "category": category
        }
        
        chart_players.append(data)

  return chart_players