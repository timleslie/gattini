#!/usr/bin/env python
"""
An intereactive database browser.
"""

import gtk
import gtk.gdk

import PIL
import PIL.Image
import PIL.ImageFilter

from pyfits import getdata

from scipy.optimize import fmin
from scipy import signal
import scipy.fftpack as fft

import numpy as N
from pylab import clip, gray

from db.query import query, count
from db.db import run_sql
from util.display import single_display, multi_display
from processing.new_ops import get_cam_flat_filename, produce_flat, unzip, get_unzipped_filename
from util.regress import regress
from util.smooth import blur_image

from gui_lib import make_button, make_cb, DropDownCheckEntryBox, make_box, \
     make_integer_spinner, make_float_spinner, \
     make_radio_list, make_entry_button, refill_cb, get_combo_item, \
     set_combo_item, OutputList
from fields import per_image_fields, per_star_fields, SimpleField
from mpl_lib import get_combo_cmap, make_cmap_combo, make_figure, get_orig_pos


exp_times = map(str, [None, 40, 10, 8, 5, 4, 2, 1, 0.8, 0.5, 0.4, 0.2, 0.1,
                      0.05, 0.005, 0.002, 0])


date_keys = ["All",
             "April",
             "May",
             "June",
             "July",
             "August",
             "September",
             "October",
             "April +",
             "SBC 2 Weeks"]

date_vals = [("060101", "070101"),
             ("060401", "060501"),
             ("060501", "060601"),
             ("060601", "060701"),
             ("060701", "060801"),
             ("060801", "060901"),
             ("060901", "061001"),
             ("061001", "061101"),
             ("060401", "070101"),
             ("060701", "060714")]



def get_image_data(image_id):
    filename, _ = get_cam_flat_filename(image_id)
    produce_flat(image_id, True)
    return getdata(filename)

def get_raw_image_data(image_id):
    filename = get_unzipped_filename(image_id)
    unzip(image_id)
    return getdata(filename)



def argmin(data):
    data = N.asarray(data)
    if data.size > 1:
        a = data
        try:
            return ((a[:-1] - a[1:]) < 0).tolist().index(True)
        except ValueError:
            return data.size
    else:
        return 0


def get_points(a, b):
    Y, X = 1200, 1600

    size = 2
    tmp = b[b < b.mean() + 3*b.std()]
    mu, sigma = tmp.mean(), tmp.std()
    limit = mu + 2.0*sigma
    
    indices = N.indices(b.shape).transpose((1,2,0))[b > limit]
    
    maxima = []
    ii, jj, ss = [], [], []
    for i,j in indices:
        i1, i2 = max(0, i - size), min(Y-1, i + size)
        j1, j2 = max(0, j - size), min(X-1, j + size)
        view = a[i1:i2,j1:j2]
        mx = view.max()
        if a[i,j] == mx:

            i0, i1 = max(0, i-30), min(1200, i+30)
            j0, j1 = max(0, j-30), min(1600, j+30)            
            n, S, E, W = a[i:i1,j], a[i0:i,j][::-1], a[i,j:j1], a[i,j0:j][::-1]
            NE = [a[i + x,j + x] for x in range(30) if 0 <= i+x < 1200 and 0 <= j+x < 1600]
            NW = [a[i + x,j - x] for x in range(30) if 0 <= i+x < 1200 and 0 <= j-x < 1600]
            SE = [a[i - x,j + x] for x in range(30) if 0 <= i-x < 1200 and 0 <= j+x < 1600]
            SW = [a[i - x,j - x] for x in range(30) if 0 <= i-x < 1200 and 0 <= j-x < 1600]
            s = min([argmin(x) for x in [n,S,E,W]] +
                    [N.sqrt(2)*argmin(x) for x in [NE, NW, SW, SE]])

            low = min([x[int(s)] for x in [n,S,E,W] if int(s) < len(x)] +
                      [x[int(s/N.sqrt(2))] for x in [NE,NW,SE,SW] if int(s/N.sqrt(2)) < len(x)])
            if mx - low > 3*sigma:
                ii.append(i)
                jj.append(j)
                ss.append(s)

    print "LIMIT =", limit, mu, sigma            
    return ii, jj, ss


def colour_scatter(result, x_field, y_field, c_field, ax, factor=1.0, **kwargs):
    if result.size == 0:
        return None

    c_data = c_field.value(result)
    x_data = x_field.value(result)
    y_data = y_field.value(result)

    s = ax.scatter(x_data, y_data, c=c_data, picker=True, faceted=False, s=9, label="I'm a label!", **kwargs) 
    ax.set_xlabel(str(x_field))
    ax.set_ylabel(str(y_field))

    s.data = result
    return s


class Tab:

    def __init__(self, parent):
        self.parent = parent
        self.make_figure()
        box = self._make_box()
        self.statusbar = gtk.Statusbar()
        message = "Welcome to the Gattini Data Explorer"
        self.context_id = self.statusbar.get_context_id(message)
        self.set_status(message)

        self.box = gtk.VBox()
        self.box.pack_start(box, True, True, 0)
        self.box.pack_start(self.statusbar, False, False, 0)
        self.label = gtk.Label(self.label)

        self.cb = None

        self.x = 0
        self.y = 0
        self.c = 0

    def __eq__(self, other):
        return self.label.get_text() == other

    def on_unfocus(self):
        self.x = self.parent.x_val_combo.get_active()
        self.y = self.parent.y_val_combo.get_active()
        self.c = self.parent.c_val_combo.get_active()

    def on_focus(self):
        refill_cb(self.parent.x_val_combo, self.fields, self.x)
        refill_cb(self.parent.y_val_combo, self.fields, self.y)
        refill_cb(self.parent.c_val_combo, self.fields, self.c)


    def make_figure(self):
        self.f, self.toolbar, self.image_box = make_figure(self.parent.win)
        self.mpl_callbacks = []

    def clear_callbacks(self):
        for cid in self.mpl_callbacks:
            self.f.canvas.mpl_disconnect(cid)        
        self.mpl_callbacks = []

    def set_callbacks(self, callbacks):
        self.clear_callbacks()
        for trigger, fn, args in callbacks:
            self.mpl_callbacks.append(self.f.canvas.mpl_connect(trigger, fn, *args))


    def make_left_right_arrows(self, spinner):
        buttons = []
        for lab, offset in [("<<<", -50), ("<<-", -10), ("<-", -1),
                              ("->", 1), ("->>", 10), (">>>", 50)]:
            buttons.append(make_button(lab, self.left_right, *(offset, spinner)))
        return  make_box(gtk.HBox, buttons)
        
        
    def left_right(self, button, offset, spinner):
        spinner.spin(gtk.SPIN_STEP_FORWARD, offset)
        self.plot()

    def on_pick(self, event):
        image_id = event.artist.data[event.ind[0]]["id"]
        self.set_busy_message("Processing image %d..." % image_id)
        self.parent.image_spin.set_value(image_id)
        self.parent.image.plot()
        self.unset_busy_message()

    def pre_draw(self):
        """
        Get the current axis, clear it and return it
        """
        self.clear_callbacks()
        self.f.clear()
        ax = self.gca()
        ax.clear()
        self.cb = None
        return ax

    def clear(self, button, *args):
        self.pre_draw()
        self.f.canvas.draw()

    def gca(self):
        return self.f.gca()

    def make_clear_button(self):
        return make_button("Clear", self.clear)

    def add_colorbar(self, mappable, c_field):
        if self.cb is not None:
            print self.cb, self.f.axes
            self.f.delaxes(self.cb.ax)
            ax = self.gca()
            print "BOX", self.f.bbox.get_bounds()
            ax.set_position(get_orig_pos())
        self.cb = self.f.colorbar(mappable, fraction = 0.08)
        self.cb.set_label(str(c_field))

    def query(self, fields, filter, image_id=None, star_id=None, condition=None):
        if filter:
            cam, exp, dates, zframes, cond, filts = self.parent.get_filters()
        else:
            cam, exp, dates, zframes, cond, filts = None, None, None, None, None, None


        if filts is None:
            filts = []
        filts = " and ".join(filts)

        print "filts = ", filts

        if zframes == "No z-frames":
            z_cond = "time(image.time) != '23:48:00'"
        elif zframes == "only z-frames":
            z_cond = "time(image.time) = '23:48:00'"
        else:
            z_cond = ""

        condition = " and ".join([s for s in [cond, condition, filts, z_cond] if s])
        if condition == "":
            condition = None
        print "condition here =", condition

        if image_id:
            image_id = self.get_image_id()
        if star_id:
            star_id = self.get_star_id()
        all_fields = []
        for f in fields:
            all_fields += f.get_fields()
        return query(all_fields, cam=cam, exp=exp, dates=dates, condition=condition, image_id=image_id, star_id=star_id)

    def scatter(self, x_field, y_field, c_field, ax, filter=True, condition=None, image_id=None, star_id=None, **kwargs):
        data = self.query([x_field, y_field, c_field, SimpleField("image.id")], filter=filter, condition=condition, image_id=image_id, star_id=star_id)
        if data.size:
            cmap = self.get_cmap()
            s = colour_scatter(data, x_field, y_field, c_field, ax, cmap=cmap, **kwargs)        
            if x_field == "image.time":
                print "AHA, time!"
                ax.xaxis_date()
                self.f.autofmt_xdate()
            self.add_colorbar(s, c_field)
            self.set_callbacks([("pick_event", self.on_pick, ())])
        return data


    def set_status(self, message):
        # pop this tabs current message
        return self.statusbar.push(self.context_id, message)

    def set_temp_message(self, message):
        self.statusbar.push(self.context_id, message)
        gtk.gdk.window_process_all_updates()

    def unset_temp_message(self):
        self.statusbar.pop(self.context_id)

    def set_busy_cursor(self):
        if self.f.canvas.window:
            self.parent.win.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))        
            self.f.canvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            self.disable_mpl_callbacks()
            gtk.gdk.window_process_all_updates()

    def unset_busy_cursor(self):
        if self.f.canvas.window:
            self.parent.win.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
            self.f.canvas.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
            self.enable_mpl_callbacks()
        
    def set_busy_message(self, message):
        self.set_temp_message(message)
        self.set_busy_cursor()

    def unset_busy_message(self):
        self.unset_temp_message()
        self.unset_busy_cursor()

    def disable_mpl_callbacks(self):
        self.f.canvas._tmp_d = self.f.canvas.callbacks.callbacks['motion_notify_event']
        self.f.canvas.callbacks.callbacks['motion_notify_event'] = {}

    def enable_mpl_callbacks(self):
        self.f.canvas.callbacks.callbacks['motion_notify_event'] = self.f.canvas._tmp_d


    def get_cmap(self):        
        return get_combo_cmap(self.parent.cmap_combo)

    def get_star_id(self):
        return self.parent.star_spin.get_value_as_int() 

    def get_image_id(self):
        return self.parent.image_spin.get_value_as_int() 

    def get_hist_params(self):
        return None

    def set_hist_params(self, params):
        pass

class PlottingTab(Tab):

    label = "Plot"

    def __init__(self, parent):
        Tab.__init__(self, parent)
        self.fields = per_image_fields

    def _make_box(self):
        return self.image_box
        
    def plot(self):
        self.set_busy_message("Plotting...")
        x, y, c = self.parent.get_xyc()
        condition = None 
        self.pre_draw()
        ax = self.gca()
        data = self.scatter(x, y, c, ax, filter=True, condition=condition)

        #X = (x.value(data), c.value(data), SimpleField("header.moonphase").value(data))
        #X = (x.value(data), c.value(data))
        #X = x.value(data)
        #Y = y.value(data)
        #self.plot_regression(ax, X, Y)
        #self.plot_fit(ax, X, Y)

        self.f.canvas.draw()
        self.unset_busy_message()

    def plot_regression(self, ax, X, Y):
        dat = N.vstack((Y, X)).transpose()
        b, m = regress(dat)
        print b, m
        xs = N.linspace(X.min(), X.max(), 10)
        ax.plot(xs, b + m*xs, linewidth=2)

    def plot_fit(self, ax, X, Y):

        def _g((a, b, c), X):
            return a - 10**(b + c*X)

        def _h((a,b,c), (X, P)):
            return a - P*10**(b + c*X)

        def _f(args, X, Y, fn):
            dist = fn(args, X) - Y
            print args,  len(Y), N.sqrt(N.sum(dist**2)), abs(dist).mean()
            return N.sqrt(N.sum(dist**2))

        def _i((a, b, c, d, e), (sun, moon, phase)):
            return a - 10**(b + c*sun) - phase*10**(d + e*moon)

        #fn = _i
        #args = fmin(_f, (21, 10.0, -10.0, -1.0, -1.0), (X, Y, fn), maxiter=5000, maxfun=25000)        
        #xs = N.linspace(X[0].min(), X[0].max(), 100)
        #ax.plot(xs, fn(args, (xs, 1.0, 50)), linewidth=3)
        #ax.plot(xs, fn(args, (xs, 1.5, 50)), linewidth=3)
        #ax.plot(xs, fn(args, (xs, 2.0, 50)), linewidth=3)
        # Sun
        #fn = _g
        #args = fmin(_f, (20.8, 1.0, 1.0), (X, Y, fn), xtol=0.00000001, ftol=0.00000001, maxiter=1000, maxfun=3000) # <-- sun params
        #xs = N.linspace(X.min(), X.max(), 100)
        #ax.plot(xs, fn(args, xs), linewidth=3)
        
        # Moon
        fn = _h
        args = fmin(_f, (22.0, 1.0, 1.0), (X, Y, fn)) # <-- moon params
        xs = N.linspace(X[0].min(), X[0].max(), 100)
        ax.plot(xs, fn(args, (xs, 0)), linewidth=3)
        ax.plot(xs, fn(args, (xs, 50)), linewidth=3)
        ax.plot(xs, fn(args, (xs, 100)), linewidth=3)
            
class ImageTab(Tab):

    label = "Image"

    def __init__(self, parent):
        Tab.__init__(self, parent)

        self.image_function = self.imshow
        self.marker_function = self.noop
        self.fields = []
    
    def _make_box(self):
        im_box = self._make_imshow_box()
        ax = self.gca()
        ax.imshow([[1,2],[4,5]])
        return im_box

    def _make_imshow_box(self):

        self.output_box = OutputList([field.label for field in per_image_fields])
        radio_box = make_radio_list([("Image", (self.imshow,)),
                                     ("Raw Image", (self.raw_imshow,)),
                                     ("X axis spectra", (self.x_spectra,)),
                                     ("Edge", (self.edge,)),
                                     ("B&W", (self.threshold,))],
                                    self.radio_callback)

        marker_box = make_radio_list([("None", (self.noop,)),
                                      ("marker", (self.marker,)),
                                      ("stars", (self.stars,)),
                                      ("threshold", (self.threshold_points,))],
                                     self.marker_callback)
                                     

        button_box = self.make_left_right_arrows(self.parent.image_spin)
        radio_box.pack_start(marker_box, False, False, 0)
        radio_box.pack_start(button_box, False, False, 0)
        
        self.display_button = make_button("Display", self.display)        
        self.display16_button = make_button("Display x16", self.display16)
        self.comment, comment_box = make_entry_button(64, "comment", self.add_comment)

        disp_box = make_box(gtk.HBox, [self.display_button, self.display16_button])
        radio_box.pack_start(disp_box, False, False, 0)
        radio_box.pack_start(comment_box, False, False, 0)
    
        vbox = make_box(gtk.VBox, [self.output_box.box, radio_box])

        box = gtk.HBox()
        box.pack_start(vbox, False, False, 0)
        box.pack_start(self.image_box, True, True, 0)        
        return box

    def noop(self, ax, data, new_data):
        pass

    def display(self, button):
        image_id = self.get_image_id()
        self.set_busy_message("Displaying image %d..." % image_id )
        print "display", image_id
        single_display(image_id)
        self.unset_busy_message()
        
    def display16(self, button):
        self.set_busy_message("Displaying multiple images. This may take a while...")
        image_id = self.get_image_id()
        image_ids = [x for x in range(image_id-8, image_id + 8) if x > 0]
        print image_ids
        print len(image_ids)
        multi_display(image_ids)
        self.unset_busy_message()

    def add_comment(self, button):
        comment = self.comment.get_text()
        f = open("comments.txt", "a")
        f.write("%d: %s\n" % (self.get_image_id(), comment))
        f.close()


    def plot(self):
        image_id = self.get_image_id()
        self.update_image(image_id)

    def update_image(self, image_id):
        self.set_busy_message("Processing %d..." % image_id)
        result = self.query(per_image_fields, filter=False, image_id=image_id)

        self.output_box.update([field.str_value(result[0]) for field in per_image_fields])

        data = get_image_data(image_id)

        ax = self.pre_draw()

        new_data = self.image_function(ax, data)
        self.marker_function(ax, data, new_data)

        self.f.canvas.draw()
        self.unset_busy_message()

    def imshow(self, ax, data):
        mu, sd = data.mean(), data.stddev()
        data = clip(data, mu - 3*sd, mu + 3*sd)

        #data = signal.detrend(signal.detrend(data, axis=0), axis=1)
        #data -= data.min()
        #data = signal.spline_filter(data)

        cmap = self.get_cmap()
        im = ax.imshow(data, origin="lower", cmap=cmap, interpolation='nearest')
        self.set_callbacks([("button_release_event", self.imclick, ())])
        self.f.colorbar(im, fraction = 0.08)

        return data

    def raw_imshow(self, ax, data):
        data = get_raw_image_data(self.get_image_id())
        return self.imshow(ax, data)

    def edge(self, ax, data):

        data = N.array(data, dtype=float)
        arr = data.__array_interface__
        print arr['shape'], arr['typestr']

        image = PIL.Image.fromarray(N.array(data, dtype=float))
        print "SIZE", image.size, image.mode
        image = image.filter(PIL.ImageFilter.EDGE_ENHANCE)
        data = N.asarray(image)
        print "shape", data.shape
        #data = data.reshape((1200, 1600))

        cmap = self.get_cmap()
        im = ax.imshow(data, origin="lower", cmap=cmap, interpolation='nearest')
        self.set_callbacks([("button_release_event", self.imclick, ())])
        self.f.colorbar(im, fraction = 0.08)

        return data

    def marker(self, ax, data, new_data, star_id=True, condition=None):
        fields = [SimpleField("phot.X"), SimpleField("phot.Y")]
        data = self.query(fields, filter=False, image_id=True, star_id=star_id, condition=condition)
        if data.size:
            ax.scatter(data['X'] - 1, data['Y'] - 1, s=20, c='r')
        ax.set_xlim(0, 1600)
        ax.set_ylim(0, 1200)

    def stars(self, ax, data, new_data):
        return self.marker(ax, data, new_data, False, "phot.image_id = image.id")


    def imclick(self, event):
        if event.xdata is None or event.ydata is None:
            return
        x, y = event.xdata + 1, event.ydata + 1
        if x and y and self.toolbar._active not in ["ZOOM", "PAN"]:
            self.find_closest_star(x, y, self.get_image_id())
            if self.marker_function == self.marker:
                self.plot()

    def find_closest_star(self, x, y, image_id):
        sql = "select star_id, X, Y from phot where image_id=%d" % image_id
        data = run_sql(sql)
        if len(data):
            i = N.argmin((data['X'] - x)**2 + (data['Y'] - y)**2)
            star_id = data[i][0]
            self.set_busy_message("Processing star %d..." % star_id)
            self.parent.star_spin.set_value(star_id)
            self.unset_busy_message()
        else:
            print "no stars"

    def x_spectra(self, ax, data):

        data = N.array(data)
        fs = []
        for d in data:
            n = d.shape[0]
            x = [n] + [n/float(i) for i in range(1, len(d)/2 + 1)]
            f = N.abs(N.fft.rfft(d))
            fs.append(f)
        f = N.array(fs)
        fav = f.mean(axis=0)
        std = f.std(axis=0)
        print f.shape, fav.shape
        ax.plot(x, fav)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 20000)



    def threshold_points(self, ax, data, new_data):
        data = blur_image(data, 5) 
        ii, jj, ss = get_points(data, new_data)
        print "POINTS", len(ii)

        for i, j, s in zip(ii, jj, ss):
            if True:
                #print s
                #print "==="
                ax.hlines(i, j-s, j+s, colors='r')
                ax.vlines(j, i-s, i+s, colors='r')

        #ax.scatter(jj, ii, c='y')
        print "COUNT", len(ii)
        ax.set_xlim(0, 1600)
        ax.set_ylim(0, 1200)

        #self.stars(ax, data, new_data)

    def threshold(self, ax, data):
        data = N.asarray(data)
        mu, sd = data.mean(), data.std()

        data = clip(data, mu - 3*sd, mu + 3*sd)
        data = blur_image(data, 5) 


        orig = data.copy()

        f = fft.fft2(data)
        f[0:5,:] = 0
        f[:,0:5] = 0
        data = N.abs(fft.ifft2(f))


        print "mu, std =", orig.mean(), orig.std()

        """
        mu, sigma = data.mean(), data.std()
        mask = data > mu + 2*sigma
        """
        #im = ax.imshow(data, origin="lower", interpolation='nearest')
        im = ax.imshow(orig, origin="lower", interpolation='nearest')
        self.set_callbacks([("button_release_event", self.imclick, ())])
        self.f.colorbar(im, fraction = 0.08)
        return data

        
    def radio_callback(self, button, arg):
        self.image_function = arg

    def marker_callback(self, button, arg):
        self.marker_function = arg




class StarTab(Tab):

    label = "Stars"

    def __init__(self, parent):
        Tab.__init__(self, parent)        
        self.image_function = self.xy_plot
        self.fields = per_image_fields + per_star_fields

    def _make_box(self):
        radio_box = make_radio_list([("XY plot", (self.xy_plot,)),
                                     ("Generic Plot", (self.full_plot,))],
                                    self.radio_callback)

        button_box = self.make_left_right_arrows(self.parent.star_spin)

        left_box = make_box(gtk.VBox, [radio_box, button_box])

        hbox = gtk.HBox()
        hbox.pack_start(left_box, False, False, 0)
        hbox.pack_start(self.image_box)
        return hbox

    def plot(self):
        star_id = self.get_star_id()
        self.update_image(star_id)

    def update_image(self, star_id):
        self.set_busy_message("Processing star %d..." % star_id)
        ax = self.pre_draw()
        condition = " and ".join(["phot.mag3 > 1", "phot.err3='NoError'", "phot.err4='NoError'"])
        self.image_function(ax, condition)
        self.f.canvas.draw()
        self.unset_busy_message()

    def radio_callback(self, button, arg):
        self.image_function = arg

    def xy_plot(self, ax, condition):
        x_field = SimpleField("phot.X")
        y_field = SimpleField("phot.Y")
        _, _, c_field = self.parent.get_xyc()
        self.scatter(x_field, y_field, c_field, ax, filter=True, condition=condition, star_id=True)

        ax = self.gca()
        ax.set_xlim(0, 1600)
        ax.set_ylim(0, 1200)

    def full_plot(self, ax, condition):
        x, y, c = self.parent.get_xyc()
        data = self.scatter(x, y, c, ax, filter=True, condition=condition, star_id=True)


class HistTab(Tab):

    label = "Histogram"

    def __init__(self, parent):
        Tab.__init__(self, parent)
        self.fields = per_image_fields + per_star_fields
        self.image_function = self.image_hist
        self.fields = per_image_fields

    def _make_box(self):
        radio_box = make_radio_list([("Image Fields", (self.image_hist, per_image_fields)),
                                     ("Image Data", (self.data_hist, [])),
                                     ("Image Stars", (self.image_stars_hist, per_star_fields)),
                                     ("Star Fields", (self.star_hist, per_image_fields + per_star_fields)),
                                     ("Sky Value", (self.sky_value_hist, []))],
                                    self.radio_callback)

        self.min_spin = make_float_spinner(0, 0, 1, 0.1)
        self.max_spin = make_float_spinner(1, 0, 1, 0.1)

        self.output_box = OutputList(["N: ", "mean: ", "stddev: "])

        button = make_button("set", self.replot)

        self.bin_spin = make_integer_spinner(5, 1000)
        
        radio_box.pack_start(make_box(gtk.HBox, [self.min_spin, self.max_spin, button]), False, False, 0)
        radio_box.pack_start(self.bin_spin, False, False, 0)
        radio_box.pack_start(self.output_box.box, False, False, 0)

        
        hbox = gtk.HBox()
        hbox.pack_start(radio_box, False, False, 0)
        hbox.pack_start(self.image_box)
        return hbox

    def replot(self, button):
        self.plot(use_range=True)

    def plot(self, use_range=False):
        self.set_busy_message("Plotting...")
        x, _, _ = self.parent.get_xyc()
        self.pre_draw()
        self.image_function(x, self.gca(), use_range)
        self.f.canvas.draw()
        self.unset_busy_message()

    def hist(self, x, ax, star_id, image_id, filter, use_range, data=None):
        bins = self.bin_spin.get_value_as_int()
        if data is None:
            data = self.query([x, SimpleField("image.id")], filter=filter, star_id=star_id, image_id=image_id)
            data = x.value(data)

        data = N.asarray(data)
        if use_range:
            min = self.min_spin.get_value()
            max = self.max_spin.get_value()
            data = data[min <= data]
            data = data[data <= max]

        if data.size:
            result = ax.hist(data, bins)
            ax.set_xlabel(str(x))
            if use_range:
                range = min, max, len(result[1])
            else:
                range = data.min(), data.max(), len(result[1])
                self.min_spin.set_range(range[0], range[1])
                self.max_spin.set_range(range[0], range[1])

            self.min_spin.set_value(range[0])
            self.max_spin.set_value(range[1])
            self.min_spin.set_increments((range[1] - range[0])/range[2], 0)
            self.max_spin.set_increments((range[1] - range[0])/range[2], 0)

            self.output_box.update([str(len(data)), str(data.mean()), str(data.std())])
            
            if x == "image.time":
                print "AHA, time!"
                ax.xaxis_date()
                self.f.autofmt_xdate()

        #data.sort()
        #thirty = data[int(0.3*len(data))]
        #fifty = data[int(0.5*len(data))]
        #ymin, ymax = ax.get_ylim()
        #ax.vlines([thirty, fifty], ymin, ymax)
        return data

    def image_hist(self, x, ax, use_range):
        return self.hist(x, ax, False, False, True, use_range)

    def data_hist(self, x, ax, use_range):
        data = get_image_data(self.get_image_id()).flat
        #data = get_raw_image_data(self.get_image_id()).flat
        return self.hist("pixel count", ax, None, None, None, use_range, data)

    def star_hist(self, x, ax, use_range):
        return self.hist(x, ax, True, False, True, use_range)

    def image_stars_hist(self, x, ax, use_range):
        return self.hist(x, ax, False, True, False, use_range)

    def sky_value_hist(self, x, ax, use_range):
        data = get_image_data(self.get_image_id())
        mu = data.flat.mean()
        data = data[600][320:1280]
        ret = self.hist("pixel count", ax, None, None, None, use_range, data)
        data.sort()
        thirty = data[int(0.3*len(data))]
        ymin, ymax = ax.get_ylim()
        ax.vlines([thirty, mu], ymin, ymax)
        return ret

    def radio_callback(self, button, fn, fields):
        self.fields = fields
        self.on_focus()
        self.image_function = fn
    
    def on_focus(self):
        refill_cb(self.parent.x_val_combo, self.fields, self.x)
        refill_cb(self.parent.y_val_combo, [], self.y)
        refill_cb(self.parent.c_val_combo, [], self.c)

    def get_hist_params(self):
        return (self.min_spin.get_value(), self.max_spin.get_value(), self.bin_spin.get_value_as_int())

    def set_hist_params(self, params):
        print "setting", params
        if params is not None:
            min, max, bin = params
            self.min_spin.set_value(float(min))
            self.max_spin.set_value(float(max))
            self.bin_spin.set_value(int(bin))



FILTER_CACHE = ".cache"

class GuiQuery:

    def __init__(self):
        
        self.win = gtk.Window()
        self.win.connect("destroy", lambda x: gtk.main_quit())
        self.win.set_default_size(800,600)
        self.win.set_title("Gattini Data Explorer")

        plot_button = make_button("Plot", self._plot)                
        self.make_cmap_combo()
        self.make_filter_combos()
        self.make_xyc_combos(per_image_fields + per_star_fields)
        self.image_spin = make_integer_spinner(1, count("image"))
        self.star_spin = make_integer_spinner(1, count("star"))

        vsep = [gtk.VSeparator() for i in range(4)]
        [v.set_property("width-request", 1) for v in vsep]
        toolbar1 = make_box(gtk.HBox, [plot_button, vsep[0],
                                       self.xyc_box, vsep[1],
                                      self.image_spin, self.star_spin,
                                      vsep[3],
                                      self.cmap_combo])

        toolbar2 = make_box(gtk.HBox, [self.filter_box, vsep[2]])

        self.nb = gtk.Notebook()
        self.nb.set_tab_pos(gtk.POS_TOP)
        self.nb.connect("switch-page", self.change_page)

        self.tabs = []
        for tab, name in [(PlottingTab, "plot"),
                          (ImageTab, "image"),
                          (StarTab, "star"),
                          (HistTab, "hist")]:
            tab = tab(self)
            self.tabs.append(tab)
            self.nb.append_page(tab.box, tab.label)
            setattr(self, name, tab)

        box = gtk.VBox()
        box.pack_start(toolbar1, False, False, 0)
        box.pack_start(toolbar2, False, False, 0)
        box.pack_start(self.nb)
        self.win.add(box)
        self.win.show_all()

    def change_page(self, notebook, page, page_num):
        self.get_active_tab().on_unfocus()
        self.tabs[page_num].on_focus()

    def get_active_tab(self):
        return self.tabs[self.nb.get_current_page()]

    def _plot(self, button):
        """
        Call the plot method of the selected tab.
        """

        self.get_active_tab().plot()
        self.filters.update()


    def make_cmap_combo(self):
        self.cmap_combo = make_cmap_combo()

        
    def make_filter_combos(self):
        self.cam_combo = make_cb(["sky", "sbc"])
        self.exp_combo = make_cb(exp_times)
        self.date_combo = make_cb(date_keys)
        self.zframe_combo = make_cb(["No z-frames", "only z-frames", "all"])
        self.filters = DropDownCheckEntryBox(FILTER_CACHE)
        save_group = self.make_save_group()

        self.filter_box = make_box(gtk.HBox, [self.cam_combo, self.exp_combo,
                                              self.date_combo, self.zframe_combo,
                                              self.filters.box, save_group])


    def get_filters(self):
        cam = get_combo_item(self.cam_combo)
        dates = date_vals[date_keys.index(get_combo_item(self.date_combo))]
        exp = get_combo_item(self.exp_combo)
        zframes = get_combo_item(self.zframe_combo)
        if exp == "None":
            exp = None
        else:
            exp = float(exp)
        filters, condition = self.filters.get_items_and_entry()

        print filters
        return cam, exp, dates, zframes, condition, filters


    def make_xyc_combos(self, fields):        
        self.x_val_combo = make_cb(fields)
        self.y_val_combo = make_cb(fields)
        self.c_val_combo = make_cb(fields)
        self.xyc_box = make_box(gtk.HBox, [self.x_val_combo,
                                           self.y_val_combo,
                                           self.c_val_combo])


    def get_tab(self):
        return self.get_active_tab().label.get_text()

    def save(self, button):
        print "self =", self
        self._plot(None)

        tab = self.get_tab()
        x, y, c = self.get_xyc()
        image = self.image_spin.get_value_as_int()
        star = self.star_spin.get_value_as_int()

        cmap = get_combo_item(self.cmap_combo)
        cam, exp, dates, zframes, _, filters = self.get_filters()
        hist = self.get_active_tab().get_hist_params()
        print "Saving hist", hist

        save_name = self.save_load_list.child.get_text()

        s = ":".join(map(str, [save_name, tab, x, y, c, image, star, cmap, cam, exp, dates, zframes, hist, filters])) + "\n"
        entries = open(".savefile", "r").readlines()
        
        f = open(".savefile", "w")    
        f.write(s)

        for ent in entries:
            sn = ent.split(":")[0]
            if sn != save_name:
                f.write(ent)        
        f.close()
        self.get_active_tab().f.savefig("/home/timl/thesis/images/%s.eps" % save_name)


    def load(self, button):

        load_name = self.save_load_list.child.get_text()

        print "loading", load_name
        
        f = open(".savefile", "r")
        for line in f.readlines():
            save_name, tab, x, y, c, image, star, cmap, cam, exp, dates, zframes, hist, filters = line.split(":")
            if save_name == load_name:
                print "loading", save_name, tab, x, y, c, image, star, cmap, exp, dates, zframes, hist, filters
                break

        self.nb.set_current_page(self.tabs.index(tab))

        set_combo_item(self.x_val_combo, x)
        set_combo_item(self.y_val_combo, y)
        set_combo_item(self.c_val_combo, c)

        self.image_spin.set_value(int(image))
        self.star_spin.set_value(int(star))
        
        set_combo_item(self.cmap_combo ,cmap)

        set_combo_item(self.cam_combo, cam)
        set_combo_item(self.exp_combo, exp)
        set_combo_item(self.date_combo, date_keys[date_vals.index(eval(dates))])
        set_combo_item(self.zframe_combo, zframes)

        tab = self.get_active_tab().set_hist_params(eval(hist))

        self.filters.load(eval(filters))

        self._plot(None)
        

    def make_save_group(self):
        save_button = make_button("save", self.save)
        load_button = make_button("load", self.load)
        self.save_load_list = gtk.combo_box_entry_new_text()

        f = open(".savefile", "r")
        for line in f.readlines():
            save_name = line.split(":")[0]
            self.save_load_list.append_text(save_name)
        
        return make_box(gtk.HBox, [self.save_load_list, save_button, load_button])

    def get_xyc(self):
        x_field = get_combo_item(self.x_val_combo)
        y_field = get_combo_item(self.y_val_combo)
        c_field = get_combo_item(self.c_val_combo)
        return x_field, y_field, c_field

if __name__ == '__main__':
    g = GuiQuery()
    gtk.main()
 
