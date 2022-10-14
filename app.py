from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask, render_template, request
import os

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
    print("At least one new game has recently finished!")
    print("Checking to see if charts should be generated..")

    for game in new_game_finals:
      for team_id in game["team_ids"]:
        players_for_charts = available_chart_players(team_id)

        if len(players_for_charts) > 0:
          print(f"Found {len(players_for_charts)} players to chart for game: {game['game_id']}..")
          
          for player in players_for_charts:
            print(f"Starting to generate chart for player: {player['player_id']} team: {player['team_id']} game: {game['game_id']}..")

            img_link, tweet_txt = build_chart(
              team_id = player["team_id"],
              player_id = player["player_id"],
              game_id = game["game_id"],
              category = player["category"]
            )

            if img_link:
              print(f"Finished generating chart with link: {img_link}")
              print(f"Sending tweet with newly created img: {img_link}")

              send_tweet(media_link = img_link, tweet_text = tweet_txt, account_type = player["category"])

              try:
                os.remove(img_link)
              except:
                print(f"Couldn't remove link for {img_link}..")
                pass
            else:
              print(f"Skipping chart for player: {player['player_id']} team: {player['team_id']} game: {game['game_id']}..")
        else:
          print(f"No players found to chart for team: {team_id} within game: {game['game_id']}..")
  else:
    print("No new games recently finished\n--")

def build_chart(team_id, player_id, game_id, category):
  chart = GameShotPlot(team_id = team_id, player_id = player_id, game_id = game_id, category = category)
  chart.build()

  return [chart.image_link, chart.tweet_text]

# use dictionary to get account based on category
def send_tweet(media_link, account_type, tweet_text):
  tweeter = Tweeter(account_type)
  tweeter.send_tweet(tweet_text = tweet_text, media_link = media_link)

def handle_tweet_form(form_response: dict):
  game_id = form_response.get("game_id")
  player_id = int(form_response.get("player_id"))
  team_id = int(form_response.get("team_id"))
  category = form_response.get("category").lower()
  tweet_context = form_response.get("tweet_text")

  img_link, tweet_txt = build_chart(
    team_id = team_id,
    player_id = player_id,
    game_id = game_id,
    category = category
  )

  full_tweet_text = f"{tweet_txt}\n{tweet_context}"
  send_tweet(media_link = img_link, tweet_text = full_tweet_text, account_type = category)

@app.route("/ping")
def ping():
  return {
    "status": 200,
    "message": "pong"
  }

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/create", methods=["GET", "POST"])
def create():
  if request.method == "POST":
    print("Creating ad-hoc tweet from /create form")
    try:
      handle_tweet_form(request.form)
      return render_template("tweet_success.html")
    except Exception as e:
      return {
        "status": 500,
        "message": f"Error creating tweet: {e}"
      }
  else:
    return render_template("create.html")

@app.route("/poll")
def manual_poll():
  poll_games()

  return {
    "status": 200
  }

def cadence():
  print(f"I'm alive at {datetime.now()}")


scheduler.add_job(cadence, "interval", minutes=10)
scheduler.add_job(poll_games, "interval", minutes=30)
scheduler.start()


if __name__ == "__main__":
  app.run(debug = False, port = 1234)
