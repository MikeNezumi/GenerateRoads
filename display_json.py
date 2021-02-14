"""
This is the main script, the application.

Inputs: GLOBALS (set below the docstring)
Output: Window animation + console metrics (potentially)
"""
WINDOW_RESOLUTION = (1920, 1020)  # 1020 + win head = 1080

import pyglet
from pyglet.gl import *
from Scripts.render_json import graph_lines, rails_lines
from Scripts.write_json import insert_rails

win = pyglet.window.Window(*WINDOW_RESOLUTION, caption = "Generated JSON")

@win.event
def on_draw():
    #roads = rails_lines("Data/DilyReal.json", (1,1,1), half_gauge=2, padding=(40, 40))

    roads = graph_lines("Data/step2.json", (0.5, 0.5, 0.5), half_gauge=2, multiplier=4)
    for road in roads:
        road.draw(GL_LINES)

    roads = rails_lines("Data/step2.json", (1,1,1), half_gauge=2, multiplier=4)
    for road in roads:
        road.draw(GL_LINES)

if __name__ == "__main__":
    pyglet.app.run()
