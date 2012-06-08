from time import mktime
import MySQLdb
from random import choice
import numpy as N
from pylab import plot, show, scatter, colorbar
import matplotlib.axes3d as p3
import pylab as p
from scipy.stats import std, mean
from scipy.optimize import fmin

from db.db import result_to_recarray
from db.query import get_star_ids

def count_stars():
    db = MySQLdb.connect(db="test")
    cursor = MySQLdb.cursors.DictCursor(db)

    sql = "SELECT star_id from star"
    cursor.execute(sql)
    results = cursor.fetchallDict()
    for ID in [int(res["star_id"]) for res in results]:
        sql = "SELECT * from phot where star_id=%d and err3='NoError'" % ID
        #print ID, cursor.execute(sql)
        xvals = [(res["Y"], res["mag3"]) for res in cursor.fetchallDict()]
        f = open("results/" + str(ID) + ".txt", 'w')
        for x, mag in xvals:
            f.write("%f %f\n" % (x, mag))
        f.close()



    
class Scatter:

    def __init__(self, x, y, z=None, s=None, c=None):
        self.x = x
        self.y = y
        self.z = z
        self.s = s
        self.c = c

    def plot(self, star):
        #print "getting"
        data = self.get_data(star)
        #print star, type(data), data.size
        if data.size == 0:
            return
        #print "got"
        if self.z:
            self._plot3D(star, data)
        else:
            self._plot2D(star, data)

    def _getcs(self, data):
        if self.c:
            c = data[self.c]
            #print data, c
            sigma, mu = std(c), mean(c)
            c = N.clip(c, mu - 2*sigma, mu + 2*sigma)
            c = (max(c) - c)/(max(c) - min(c))
        else:
            c = 'b'
        if self.s:
            s = data[self.s]
        else:
            s = 10.0
        return c, s

    def _plot3D(self, star, data):
        fig = p.figure(1)
        if fig.axes:
            ax = fig.axes[0]
        else:
            ax = p3.Axes3D(fig)
        ax.set_xlabel(self.x)
        ax.set_ylabel(self.y)
        ax.set_zlabel(self.z)
        #print data
        c, s = self._getcs(data)
        #print "plotting"
        ax.scatter3D(data[self.x], data[self.y], data[self.z], c=c, s=s, faceted=False)
        #print "done"

    def _plot2D(self, star, data):
        #print data
        c, s = self._getcs(data)
        scatter(data[self.x], data[self.y], c=c, s=5*s, faceted=False, alpha=0.2)        

    def get_data(self, star):
        #print "DB"
        keys = [self.x, self.y]
        keys += [k for k in [self.z, self.s, self.c] if k]

        db = MySQLdb.connect(db="test")
        cursor = MySQLdb.cursors.Cursor(db)

        ss = ", ".join(["%s"]*len(keys))
        sql = ("SELECT %s from phot where star_id=%d and mag3 > 1 and err3='NoError' and err4='NoError'" % (ss, star))
        sql = sql % tuple(keys)
        #print sql
        cursor.execute(sql)
        data = result_to_recarray(cursor)
        return data

def foo(arg):
    print arg


def plot_stars():
    #print "getting ids"
    db = MySQLdb.connect(db="test")
    cursor = MySQLdb.cursors.Cursor(db)
    stars = get_star_ids()
    #print "got ids"

    for _ in range(1):
        ID = choice(stars)
        ID = 2000
        print "scatter", ID
        
        #Scatter("X", "Y", "mag3", c="time").plot(ID)
        Scatter("X", "Y", c="mag3").plot(ID)

    #print "save"
    #p.savefig("tmp.png")
    #print "return"
    colorbar()
    p.xlim(0, 1600)
    p.ylim(0, 1200)
    show()

def find_center(id):
    db = MySQLdb.connect(db="test")
    cursor = MySQLdb.cursors.Cursor(db)


    sql = "SELECT X, Y from phot where star_id=%d and mag3 > 1 and err3='NoError' and err4='NoError'" % id
    cursor.execute(sql)
    data = result_to_recarray(cursor)
    res = fmin(f, (800, 600, 150), (data['X'], data['Y']))
    return res

if __name__ == '__main__':
    """
    results = []
    stars = get_star_ids()
    for star in stars:
        print star, stars[-1]
        res = find_center(star)
        results.append(res)
    N.asarray(results).tofile("results.dat")

    plot_stars()
else:
    """
    print "starting"
    #plot_stars()
    import hotshot, hotshot.stats
    prof = hotshot.Profile("stones.prof")
    benchtime = prof.runcall(plot_stars)
    prof.close()
    stats = hotshot.stats.load("stones.prof")
    stats.strip_dirs()
    stats.sort_stats('cumulative', 'calls')
    stats.print_stats(20)

