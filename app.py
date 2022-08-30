from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from src.game_final_updater import GameFinalUpdater
from src.available_chart_players import available_chart_players
from src.game_shot_plot import GameShotPlot
from services.tweeter import Tweeter


scheduler = BackgroundScheduler(daemon=True)
app = Flask(__name__)

def poll_games():
  print("Polling scoreboard and updating game finals")
  game_status_updater = GameFinalUpdater()
  new_game_finals = game_status_updater.update_game_finals()
  if len(new_game_finals) > 0:
    print("New game(s) have finished!")
    print("Checking to see if charts should be generated..")
    for game in new_game_finals:
      for team_id in game["team_ids"]:
        players_for_charts = available_chart_players(team_id)
        
        for player in players_for_charts:
          print(f"Generating chart for player: {player['player_id']} team: {player['team_id']}..")
          img_link = build_chart(team_id = player["team_id"], player_id = player["player_id"], game_id = game["game_id"])
          
          # TODO: We should skip sending tweet if the above chart building returns None
          print(f"Finished generating chart with link: {img_link}")
          print(f"Sending tweet with newly created img: {img_link}")
          # send_tweet(media_link = img_link)
          # TODO: img file cleanup here after sending the tweet? At this point we should have backed it up to GCP
  else:
    print("No new games recently finished")

def build_chart(team_id, player_id, game_id):
  chart = GameShotPlot(team_id = team_id, player_id = player_id, game_id = game_id)
  img_link = chart.build()

  return img_link
  
def send_tweet(media_link, account = "foobar"):
  tweeter = Tweeter()
  tweeter.send_tweet(media_link)

@app.route("/")
def hello_hunty():
  return "<p>Hello Hunty</p>"

@app.route("/poll")
def manual_poll():
  poll_games()
  
  return {
    "status": 200
  }

scheduler.add_job(poll_games, 'interval', seconds=10)
scheduler.start()


if __name__ == "__main__":
  app.run(debug = False, port = 1234)
