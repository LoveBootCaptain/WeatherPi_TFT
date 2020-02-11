# pylint: disable=invalid-name, too-few-public-methods
""" Glaph utility class
"""

import io
import threading
import pygame
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator, HourLocator

# graph parameters
matplotlib.pyplot.switch_backend('Agg')
style = "dark_background"
colormaps = "Dark2"
dpi = 100


def _plot_2axis_graph(screen, surface, rect, times, y1, ylabel1, y2, ylabel2):
    # plot graph
    plt.style.use(style)
    fig, ax1 = plt.subplots(figsize=(rect.width / dpi, rect.height / dpi))
    if y1 is not None:
        c = plt.get_cmap(colormaps)(0)
        ax1.yaxis.label.set_color(c)
        ax1.set_ylabel((ylabel1))
        ax1.plot(times, y1, color=c)
    if y2 is not None:
        c = plt.get_cmap(colormaps)(1)
        ax2 = ax1.twinx()
        ax2.yaxis.label.set_color(color=c)
        ax2.set_ylabel((ylabel2))
        ax2.plot(times, y2, color=c)

    # setting tics
    if (max(times) - min(times)).days > 1:
        ax1.xaxis.set_major_locator(DayLocator())
        ax1.xaxis.set_minor_locator(HourLocator(interval=6))
        ax1.xaxis.set_major_formatter(DateFormatter("%m-%d"))
    else:
        ax1.xaxis.set_major_locator(HourLocator())
        ax1.xaxis.set_major_formatter(DateFormatter("%H"))

    # convert to pygame image
    f = io.BytesIO()
    plt.tight_layout()
    plt.savefig(f, format="png")
    plt.close(fig)
    f.seek(0)
    image = pygame.image.load(f)

    # draw image
    surface.fill(pygame.Color("black"))
    surface.blit(image, (0, 0))
    screen.blit(surface, (rect.left, rect.top))


class GraphUtils:
    """Graph Utility class
    """

    @staticmethod
    def plot_2axis_graph(screen, surface, rect, times, y1, ylabel1, y2,
                         ylabel2):
        """plot 2axis graph in another thread
        """
        threading.Thread(target=_plot_2axis_graph,
                         args=(screen, surface, rect, times, y1, ylabel1, y2,
                               ylabel2)).start()
