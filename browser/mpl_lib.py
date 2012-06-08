"""
Utilities to help incorporate matplotlib items into a gtk GUI.
"""

import gtk

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.cm import cmapnames, get_cmap
from matplotlib import rcParams

from gui_lib import get_combo_item, make_cb

rcParams["figure.subplot.left"] = 0.05
rcParams["figure.subplot.right"] = 0.95
rcParams["font.size"] = 14
rcParams["axes.labelsize"] = 14
rcParams["xtick.labelsize"] = 14
rcParams["ytick.labelsize"] = 14


def make_cmap_combo(default="jet"):
    """
    Create a drop ComboBox with all the available matplotlib colourmaps.
    """
    cmap_combo = make_cb(cmapnames + [c + "_r" for c in cmapnames])
    cmap_combo.set_active(cmapnames.index(default))
    return cmap_combo

def get_combo_cmap(cmap_combo):        
    """
    Return the colourmap object from the combo of colour map names.
    """
    return get_cmap(get_combo_item(cmap_combo))


def make_figure(win):
    """
    Create a figure with toolbar and associated boxes.
    Return the figure, toolbar, and encapsulating box.
    """
    fig = Figure()
    FigureCanvas(fig)
    toolbar = NavigationToolbar(fig.canvas, win)
    image_box = gtk.VBox()
    image_box.pack_start(fig.canvas)
    image_box.pack_start(toolbar, False, False)
    return fig, toolbar, image_box

def get_orig_pos():
    """
    Return the (left, width, right, height) of the original image as defined by
    the rcParams.
    """
    l, r, t, b = [rcParams["figure.subplot." + k] for k in ["left", "right", "top", "bottom"]]
    return l, b, r-l, t-b
