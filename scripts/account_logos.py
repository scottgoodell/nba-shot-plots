import matplotlib as mpl
import matplotlib.pyplot as plt
import nba_api.stats.static.players as players
import re
import random

from services.google_storage_handler import GoogleStorageHandler
from static.colors import colors
from static.teams import teams

class AccountLogo:
  
  def __init__(self, player_id, team_id, category) -> None:
    self.player_id = player_id
    self.team_id = team_id
    self.category = category
    
  def build(self):
    court_color = colors["chart_background"]
    background_color = colors["chart_background"]
    lines_width = 4
    lines_opacity = 0.85

    if self.category == "rookies":
      account = "Rookie"
    elif self.category == "sophomores":
      account = "Sophomore"
    elif self.category == "westbrook":
      account = "Russ"
    else:
      account = "NBA"

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

    player_context = players.find_player_by_id(self.player_id)
    player_full_name = player_context["full_name"]
    player_slug = self._player_slug(player_full_name)

    storage_client.download_object("nba-shot-plot-player-images", f"{player_slug}.png", ".")
    storage_client.download_object("nba-shot-plot-team-images", f"{team_context['abbreviation']}.png", ".")
    player_img = plt.imread(f"./{player_slug}.png")

    fig = plt.figure(num=1, clear=True)
    court_ax = fig.add_subplot()

    fig.set_figheight(9)
    fig.set_figwidth(5.5)
    court_ax.set_facecolor(court_color)

    SIDES = ["top", "bottom", "right", "left"]
    for side in SIDES:
      court_ax.spines[side].set_color(lines_color)

    # Short corner 3PT lines
    court_ax.plot([-214, -214], [0, 140], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([214, 214], [0, 140], linewidth=lines_width, color=lines_color, alpha=lines_opacity)

    # 3PT Arc
    court_ax.add_artist(mpl.patches.Arc((0, 125), 430, 310, theta1=4, theta2=176, facecolor='none', edgecolor=lines_color, lw=lines_width, snap=True, alpha=lines_opacity))

    for _ in range(60):
      mark_color = colors["made_shot"] if random.randint(0, 4) in [0,1,2] else colors["missed_shot"]
      shot_x = random.randint(-240, 240)
      shot_y = random.randint(0, 290)+30
      if (abs(shot_x) > 165 and shot_y < 50) or (shot_y > 50 and abs(shot_x) > 100) or (shot_y > 260):
        court_ax.plot(shot_x, shot_y, marker='o', color=mark_color, markersize=26, markeredgecolor=colors["marker_edge"])

    # Remove ticks
    court_ax.set_xticks([])
    court_ax.set_yticks([])

    # Set axis limits
    court_ax.set_xlim(-250, 250)
    court_ax.set_ylim(0, 470)

    # Player image as key
    court_ax.imshow(player_img, extent=[-171, 171, 0, 250])

    name_title_txt_ax = fig.add_axes([0.30, 0.05, 0.4, 0.1], anchor='SW', zorder=-1)
    name_title_txt_ax.set_xticks([])
    name_title_txt_ax.set_yticks([])

    name_title_txt_box_props = dict(facecolor=background_color, edgecolor="none")

    name_title_txt_box_text = \
      f"{account}\nShot Plots"

    name_title_txt_ax.text(
      0.5, 0.5,
      name_title_txt_box_text,
      fontsize=28,
      color=lines_color,
      ha="center",
      va="center",
      bbox=name_title_txt_box_props,
      linespacing=1.2,
    )
    name_title_txt_ax.set_facecolor(background_color)
    name_title_txt_ax.axis('off')

    plt.subplots_adjust(left=0.02, right=0.98, top=0.72, bottom=0.16)
    plt.savefig(f"./{self.category}-logo-{player_slug}.png")
    
  def _player_slug(self, full_name):
    return re.sub(r'[^a-z-]', '', full_name.lower().replace(" ", "-"))


if __name__ == "__main__":
  a = AccountLogo(
    player_id = 201566,
    team_id = 1610612747,
    category = "westbrook"
  )

a.build()