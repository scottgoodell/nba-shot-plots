import importlib
from nba_api.live.nba.endpoints import boxscore
from nba_api.stats.endpoints import shotchartdetail
import nba_api.stats.static.players as players

from datetime import datetime
import json
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import re

from helpers.delay import delay_between_1_and_2_secs
from services.google_storage_handler import GoogleStorageHandler
from static.player_categories import player_categories
from static.colors import colors
from static.teams import teams

class GameShotPlot:

  image_link = None
  tweet_text = None

  def __init__(self, game_id, player_id, team_id, category, shot_type = "FGA", season = "2022-23", season_part = "Pre Season") -> None:
    self.game_id            = game_id
    self.player_id          = player_id
    self.team_id            = team_id
    self.category           = category
    self.shot_type          = shot_type
    self.season             = season
    self.season_part        = season_part
    self.local_img_location = "/tmp"

  def build(self):
    court_color = colors["court_color"]
    background_color = colors["chart_background"]
    chart_text_color = colors["chart_text"]
    lines_width = 1.5 # const?
    lines_opacity = 0.85 # const?

    game_boxscore_data = self._get_game_boxscore()
    team_boxscore_data = self._get_team_stats(game_boxscore_data)
    top_stats, bottom_stats = self._get_player_game_stats(team_boxscore_data)

    if top_stats["status"] == "INACTIVE" or top_stats["minutes"] == 0:
      return

    font_dir = ["./static/fonts/Lato", "./static/fonts/McLaren"]
    for font in mpl.font_manager.findSystemFonts(font_dir):
      mpl.font_manager.fontManager.addfont(font)

    plt.switch_backend('Agg')

    storage_client = GoogleStorageHandler()

    team_context = [t for t in teams if t["id"] == self.team_id][0]
    court_color = court_color
    lines_color = team_context["lines_color"] if team_context.get("lines_color") else "black"

    mpl.rcParams['axes.linewidth'] = lines_width
    mpl.rcParams['figure.facecolor'] = background_color
    mpl.rcParams['font.weight'] = "bold"
    mpl.rcParams['font.family'] = "McLaren"

    delay_between_1_and_2_secs()
    shot_json = shotchartdetail.ShotChartDetail(
      team_id = self.team_id,
      player_id = self.player_id,
      context_measure_simple = self.shot_type,
      season_nullable = self.season,
      season_type_all_star = self.season_part
    )
    shot_data = json.loads(shot_json.get_json())
    shot_values = shot_data['resultSets'][0]['rowSet']
    game_shot_values = [[s[1], s[10], s[12], s[17], s[18]] for s in shot_values if s[1] == self.game_id]

    player_context = players.find_player_by_id(self.player_id)
    player_full_name = player_context["full_name"]
    player_slug = self._player_slug(player_full_name)

    storage_client.download_object("nba-shot-plot-player-images", f"{player_slug}.png", self.local_img_location)
    storage_client.download_object("nba-shot-plot-team-images", f"{team_context['abbreviation']}.png", self.local_img_location)
    player_img = plt.imread(f"{self.local_img_location}/{player_slug}.png")
    team_img = plt.imread(f"{self.local_img_location}/{team_context['abbreviation']}.png")

    fig, court_ax = plt.subplots()
    fig.set_figheight(9)
    fig.set_figwidth(5.5)
    court_ax.set_facecolor(court_color)

    SIDES = ["top", "bottom", "right", "left"]
    for side in SIDES:
      court_ax.spines[side].set_color(lines_color)

    # Team logo court
    team_logo_coords = team_context["coordinates"] if team_context.get("coordinates") else [-260, 260, -20, 480]
    team_logo_opacity = team_context["logo_opacity"] if team_context.get("logo_opacity") else 0.1
    court_ax.imshow(team_img, extent=team_logo_coords, alpha=team_logo_opacity)

    # Short corner 3PT lines
    court_ax.plot([-214, -214], [0, 140], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([214, 214], [0, 140], linewidth=lines_width, color=lines_color, alpha=lines_opacity)

    # 3PT Arc
    court_ax.add_artist(mpl.patches.Arc((0, 125), 430, 310, theta1=4, theta2=176, facecolor='none', edgecolor=lines_color, lw=lines_width, snap=True, alpha=lines_opacity))

    # Lane and Key
    court_ax.plot([-80, -80], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([80, 80], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([-60, -60], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([60, 60], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([-80, 80], [190, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.add_artist(mpl.patches.Arc((0, 190), 120, 120, theta1=0, theta2=180, facecolor='none', edgecolor=lines_color, lw=lines_width, snap=True, alpha=lines_opacity))

    starting_angles = [-5, -35, -65, -95, -125, -155]
    for a in starting_angles:
      court_ax.add_artist(mpl.patches.Arc((0, 190), 120, 120, angle=a, theta1=-20, theta2=0, facecolor='none', edgecolor=lines_color, lw=lines_width, snap=True, alpha=lines_opacity))

    # Restricted Area
    court_ax.add_artist(mpl.patches.Arc((0, 40), 80, 80, theta1=0, theta2=180, facecolor='none', lw=lines_width, alpha=0.2))

    # Rim
    court_ax.add_artist(mpl.patches.Circle((0, 40), 10, facecolor='none', edgecolor=colors["rim"], lw=lines_width, alpha=0.6))

    # Backboard
    court_ax.plot([-25, 25], [29, 29], linewidth=lines_width, color=lines_color, alpha=0.2)

    # Halfcourt
    court_ax.add_artist(mpl.patches.Circle((0, 470), 60, facecolor='none', edgecolor=lines_color, lw=lines_width, alpha=lines_opacity))
    court_ax.add_artist(mpl.patches.Circle((0, 470), 20, facecolor='none', edgecolor=lines_color, lw=lines_width, alpha=lines_opacity))

    shot_marker_colors = {
      "3PT Field Goal": {
        "Made Shot": colors["made_shot"],
        "Missed Shot": colors["missed_shot"],
      },
      "2PT Field Goal": {
        "Made Shot": colors["made_shot"],
        "Missed Shot": colors["missed_shot"],
      }
    }

    for shot in game_shot_values:
      mark_color = shot_marker_colors[shot[2]][shot[1]]
      court_ax.plot(shot[3], shot[4]+45, marker='o', color=mark_color, markersize=12, markeredgecolor=colors["marker_edge"])

    # Remove ticks
    court_ax.set_xticks([])
    court_ax.set_yticks([])

    # Set axis limits
    court_ax.set_xlim(-250, 250)
    court_ax.set_ylim(0, 470)

    stat_count = 0
    for c in [0.34, 0.58, 0.79]:
      for r in [0.106, 0.072, 0.038, 0.004]:
        a = fig.add_axes([c, r, 0.16, 0.05], anchor='SW', zorder=-1)
        a.set_xticks([])
        a.set_yticks([])
        stat_box_props = dict(facecolor=background_color, edgecolor="none")
        a.text(
          0.0, 0.5,
          bottom_stats[stat_count],
          fontsize=15,
          color=chart_text_color,
          ha="left",
          va="center",
          bbox=stat_box_props
        )
        a.axis('off')
        stat_count += 1

    name_title_txt_ax = fig.add_axes([0.30, 0.87, 0.4, 0.1], anchor='SW', zorder=-1)
    name_title_txt_ax.set_xticks([])
    name_title_txt_ax.set_yticks([])

    name_title_txt_box_props = dict(facecolor=background_color, edgecolor="none")
    name_title_team_txt = self._name_title_txt_by_category(team_context)

    name_title_txt_box_text = \
      f"{player_full_name}\n" + name_title_team_txt

    name_title_txt_ax.text(
      0.5, 0.5,
      name_title_txt_box_text,
      fontsize=24,
      color=chart_text_color,
      ha="center",
      va="center",
      bbox=name_title_txt_box_props,
      linespacing=1.2,
    )
    name_title_txt_ax.set_facecolor(background_color)
    name_title_txt_ax.axis('off')

    game_title_txt_ax = fig.add_axes([0.30, 0.74, 0.4, 0.1], anchor='SW', zorder=-1)
    game_title_txt_ax.set_xticks([])
    game_title_txt_ax.set_yticks([])

    game_info = self._get_game_info()

    game_title_txt_box_props = dict(facecolor=background_color, edgecolor="none")
    game_title_txt_box_text = \
      f"{game_info['game_date']}\n" + \
      f"{game_info['away_team_abbr']}  ({game_info['away_score']})  vs.  {game_info['home_team_abbr']}  ({game_info['home_score']})\n" + \
      f"Mins: {top_stats['minutes']},  Pts: {top_stats['points']},  +/-: {top_stats['plus_minus']},  Starting: {top_stats['starting']}\n" + \
      f"{player_categories[self.category]['twitter_handle']}"

    game_title_txt_ax.text(
      0.5, 0.5,
      game_title_txt_box_text,
      fontsize=14,
      color=chart_text_color,
      ha="center",
      va="center",
      bbox=game_title_txt_box_props,
      linespacing=1.5,
    )
    game_title_txt_ax.set_facecolor(background_color)
    game_title_txt_ax.axis('off')

    player_img_ax = fig.add_axes([0.0, 0.0, 0.34, 0.18], anchor='SW', zorder=-1)
    player_img_ax.imshow(player_img)
    player_img_ax.axis('off')

    export_filename = f"{player_slug}-{team_context['abbreviation']}-{self.game_id}.png"

    plt.subplots_adjust(left=0.02, right=0.98, top=0.72, bottom=0.16)
    plt.savefig(f"{self.local_img_location}/{export_filename}")
    storage_client.upload_object("nba-shot-plot-shot-plots", export_filename, self.local_img_location)
    plt.close(fig)

    for file in [f"{self.local_img_location}/{player_slug}.png", f"{self.local_img_location}/{team_context['abbreviation']}.png"]:
      try:
        os.remove(file)
      except:
        pass

    self.image_link = f"{self.local_img_location}/{export_filename}"
    self.tweet_text = self._build_tweet_text(
      player_game_stats = {
        "top_stats": top_stats,
        "bottom_stats": bottom_stats
      },
      player_context = player_context,
      team_context = team_context,
      game_info = game_info
    )

  def _build_court(self):
    # i feel like i should be able to pass around the figure somehow and the plt
    pass

  def _build_tweet_text(self, player_game_stats: dict, player_context, team_context, game_info):

    # TODO: Make sure use actual hashtags from team context
    return f"{player_context['full_name']}\n" \
      f"{team_context['name']} {team_context['hashtag']}\n\n" \
      f"Final: {game_info['away_team_name']} {game_info['away_score']} // {game_info['home_team_name']} {game_info['home_score']}\n" \
      f"#{game_info['away_team_abbr']}vs{game_info['home_team_abbr']} // #{game_info['home_team_abbr']}vs{game_info['away_team_abbr']}\n\n" \
      f"Minutes: {player_game_stats['top_stats']['minutes']}\n" \
      f"Points: {player_game_stats['top_stats']['points']}\n" \
      f"Shots: {player_game_stats['bottom_stats'][0].split(':')[-1].strip()}\n" \
      f"Threes: {player_game_stats['bottom_stats'][1].split(':')[-1].strip()}\n" \
      f"Frees: {player_game_stats['bottom_stats'][2].split(':')[-1].strip()}\n"

  def _player_slug(self, full_name):
    return re.sub(r'[^a-z-]', '', full_name.lower().replace(" ", "-"))

  def _get_game_boxscore(self):
    delay_between_1_and_2_secs()
    data = boxscore.BoxScore(self.game_id)
    return data.game.get_dict()

  def _get_game_info(self):
    boxscore_data = self._get_game_boxscore()

    return {
      "game_date": datetime.strptime(boxscore_data["gameTimeHome"][:19], '%Y-%m-%dT%H:%M:%S').strftime("%A, %m/%d/%Y"),
      "away_team_abbr": boxscore_data["awayTeam"]["teamTricode"],
      "away_score": boxscore_data["awayTeam"]["score"],
      "away_team_name": boxscore_data["awayTeam"]["teamName"],
      "home_team_abbr": boxscore_data["homeTeam"]["teamTricode"],
      "home_score": boxscore_data["homeTeam"]["score"],
      "home_team_name": boxscore_data["homeTeam"]["teamName"],
    }

  def _get_team_stats(self, boxscore_data):
    return boxscore_data["awayTeam"] if boxscore_data["awayTeam"]["teamId"] == self.team_id else boxscore_data["homeTeam"]

  def _get_player_game_stats(self, team_stats):
    player_stats = [player for player in team_stats["players"] if player['personId'] == self.player_id][0]
    plus_minus = int(player_stats["statistics"]["plusMinusPoints"])
    if plus_minus > 0:
      str_plus_minus = f"+{str(plus_minus)}"
    else:
      str_plus_minus = str(plus_minus)

    top_stats = {
      "minutes": int(re.sub(r'[a-zA-Z]', '', player_stats["statistics"]["minutesCalculated"])),
      "starting": 'Yes' if player_stats["starter"] == '1' else 'No',
      "plus_minus": str_plus_minus,
      "points": player_stats["statistics"]["points"],
      "status": player_stats["status"]
    }

    bottom_stats = [
      f"FGs: {player_stats['statistics']['fieldGoalsMade']}/{player_stats['statistics']['fieldGoalsAttempted']}",
      f"3FGs: {player_stats['statistics']['threePointersMade']}/{player_stats['statistics']['threePointersAttempted']}",
      f"FTs: {player_stats['statistics']['freeThrowsMade']}/{player_stats['statistics']['freeThrowsAttempted']}",
      f"EFG%: {self._calc_efg(player_stats)}",
      f"ASTs: {player_stats['statistics']['assists']}",
      f"TOs: {player_stats['statistics']['turnovers']}",
      f"REBs: {player_stats['statistics']['reboundsTotal']}",
      f"OREBs: {player_stats['statistics']['reboundsOffensive']}",
      f"STLs: {player_stats['statistics']['steals']}",
      f"BLKs: {player_stats['statistics']['blocks']}",
      f"PFs: {player_stats['statistics']['foulsPersonal']}",
      f"USG%: {self._calc_usage_rate(team_stats, player_stats)}",
    ]

    return [top_stats, bottom_stats]

  def _calc_efg(self, player_data):
    player_fgs_made     = player_data['statistics']['fieldGoalsMade']
    player_fgs_attempts = player_data['statistics']['fieldGoalsAttempted']
    player_3fgs_made    = player_data['statistics']['threePointersMade']

    effective_field_goal_perc = (player_fgs_made + 0.5 * player_3fgs_made) / player_fgs_attempts

    return str(int(round(effective_field_goal_perc * 100, 0)))

  def _calc_usage_rate(self, team_data, player_data):
    player_fgs  = int(player_data['statistics']['fieldGoalsAttempted'])
    player_fts  = int(player_data['statistics']['freeThrowsAttempted'])
    player_tos  = int(player_data['statistics']['turnovers'])
    player_mins = int(re.sub(r'[a-zA-Z]', '', player_data["statistics"]["minutesCalculated"]))

    team_fgs  = int(team_data['statistics']['fieldGoalsAttempted'])
    team_fts  = int(team_data['statistics']['freeThrowsAttempted'])
    team_tos  = int(team_data['statistics']['turnovers'])
    team_mins = int(re.sub(r'[a-zA-Z]', '', team_data["statistics"]["minutesCalculated"]))

    usage_percentage = ((player_fgs + (0.44 * player_fts) + player_tos) * (team_mins / 5)) \
    / (player_mins * (team_fgs + (.44 * team_fts) + team_tos))

    return str(int(round(usage_percentage * 100, 0)))

  def _name_title_txt_by_category(self, team_context):
    if self.category in ["rookies", "sophomores"]:
      category_context_module = getattr(importlib.import_module(f"static.{self.category}"), self.category)
      category_context = [p for p in category_context_module if p["id"] == self.player_id][0]

      return f"Drafted: {category_context['draft_year']} #{category_context['draft_pick']} ({team_context['abbreviation'].upper()})"
    else:
      return f"{team_context['name']}"


# should i have a helper class to isolate player's stats for a specific game? GameStats (player_id, game_id)
# maybe? if i feel like it's going to be reused; but right now it's not

# class for font handling.. again if you are going to repeat it then separate it FontHandler

# make player.json so you don't have to make a request

# GameShotPlot < ShotPlot
# build shouldn't know about the shot_values - this should be a separate method?
