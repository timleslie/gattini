#
# THIS CODE IS COMPLETELY DEPRECATED (and probably broken) -- Timl
#

import MySQLdb
import numpy as N
from pylab import *
import time

from db.db import get_star_ids, get_summary_data, run_sql, recarray_wrap
from db.query import get_phot_data, get_star_ids

import matplotlib.axes3d as p3

""" The (x, y) coords of the celestial south pole in our images. """
c_x, c_y = 783, 709

def to_polar(X, Y):
    """
    Convert euclidean (X, Y) into polar (r, theta).
    """
    theta = N.arctan2(Y, X)
    rad = N.sqrt(X**2 + Y**2)
    return rad, theta

def from_polar(rad, theta):
    """
    Convert polar (r, theta) into euclidean (x, y).
    """
    x = rad*N.cos(theta)
    y = rad*N.sin(theta)
    return x, y

def to_deg(theta):
    """
    Convert radians to degrees
    """
    return 180*(theta + N.pi)/N.pi

def from_deg(deg):
    """
    Convert degrees to radians
    """
    return deg*N.pi/180 - N.pi

def radial_data(data):
    """
    Take a recarray of data with 'X' and 'Y' entries and return
    a recarray with 'r' and 'theta' entries representing the (X, Y)
    transformed to polar coordinates.    
    """
    x = data['X'] - c_x
    y = data['Y'] - c_y
    radius, angles = to_polar(x, y)
    angles = to_deg(angles)
    return recarray_wrap(zip(radius, angles), names=["r", "theta"])

def make_radial_ratio_data(star):
    """
    Obtain radial coords and magnitude ratios for a given star. Returns a
    recarray with entries 'ratio3', 'ratio4', 'theta', 'r', 'time'.
    """
    data = get_phot_data(star, ("Vmag", "smag", "mag3", "mag4", "X", "Y", "time"),
                         ["mag3 < 100", "mag3 > 1"])


    rad_data = radial_data(data)
    
    ratio3 = data['smag']#data['mag3']/data['Vmag']
    ratio4 = data['mag4']/data['Vmag']

    points = N.vstack((ratio3, ratio4, rad_data["theta"], rad_data["r"],
                       data['time'])).T
    return recarray_wrap(points, names=["ratio3", "ratio4", "theta", "r", "time"])

def make_summary(star, factor=2.5, clear=True):
    """
    Update the database with a summary for the given star using the given factor.
    """
    if clear:
        sql =  "DELETE FROM summaries where factor = %f and ID = %d" % (factor, star)
        run_sql(sql)

    if len(get_summary_data(star, factor)) > 0:
        print "returning??"
        return

    points = make_radial_ratio_data(star)    
    buckets = [[] for _ in range(int(360/factor))]

    for mag3, mag4, angle, radius, time in points:
        buckets[int(angle/factor)].append((mag3, mag4, radius))

    for angle, bucket in enumerate(buckets):
        if bucket:            
            bucket = recarray_wrap(bucket, names=["ratio3", "ratio4", "r"])
            mags3 = bucket["ratio3"]
            mags4 = bucket["ratio4"]
            radii = bucket["r"]
        else:
            mags3, mags4, radii = [0], [0], [0]
        sql = "INSERT INTO summaries VALUES " + \
              "(%d, %d, %f, %f, %f, %f, %f, %f, %f)" % \
              (star, angle, factor, mean(mags3), std(mags3),
               mean(mags4), std(mags4), mean(radii), std(radii))
        run_sql(sql)


def process(star, factor=2.5):
    """
    Process a single star using the given factor. Returns a recarray
    with the data summary and another with the outliers.
    """
    points = make_radial_ratio_data(star)    
    summary = get_summary_data(star, factor)
    outliers = get_outliers(summary, points, factor)
    return summary, outliers


def get_outliers(summary, points, factor):
    """
    Calculate the outliers from a set of points. Returns a recarray of points
    with fields 'mag3', 'theta', 'r', 'time'.
    """
    outliers = []
    Z = 2.0
    for mag3, mag4, angle, radius, time in points:        
        avg_m = summary["AVG3"][int(angle/factor)]
        std_m = summary["STD3"][int(angle/factor)]
        if std_m == 0:
            std_m = 0.0001
        if not (avg_m - Z*std_m <= mag3 <= avg_m + Z*std_m):
            outliers.append((mag3, angle, radius, time))
    if len(points):
        print float(len(outliers))/len(points), len(outliers), len(points)
    return recarray_wrap(outliers, names=["mag3", "theta", "r", "time"])

def plot_data(summary, outliers):
    """ REDUNDANT (more or less)"""
    #relmag = clip(data['mag3']/data['Vmag'], 0, 20)

    summary[:,0] = from_deg(summary[:,0])


    X, Y = from_polar(summary['AVGR'], summary['ANGLE'])
    X += c_x
    Y += c_y

    out_X, out_Y = from_polar(outliers['r'], outliers['theta'])
    out_X += c_x
    out_Y += c_y

    fig = figure()
    ax = p3.Axes3D(fig)
    #ax.scatter3D(data['X'], data['Y'], relmag, c=relmag)
    #ax.scatter3D(data['X'], data['Y'], relmag, c=data['time'])
    #ax.scatter3D(out_X, out_Y, outliers[:,0], c=outliers[:,3])
    ax.scatter3D(outliers['time'], out_X, out_Y, c=outliers['mag3'])
    #ax.plot3D(X, Y, summary[:,2], c='k')#, c=summary[:,2])
    #ax.plot3D(X, Y, summary[:,2] + 2.5*summary[:,3], c='r') #, c=summary[:,2])
    #ax.plot3D(X, Y, summary[:,2] - 2.5*summary[:,3], c='r')#, c=summary[:,2])
    #scatter(data[2], data[3], c=relmag, faceted=False)
    show()

def plot_outlier_spiral(outliers):
    """
    Plot x vs y vs time for a set of outliers. Colour points by mag3.
    """

    out_X, out_Y = from_polar(outliers['r'], outliers['theta'])
    out_X += c_x
    out_Y += c_y

    fig = figure()
    ax = p3.Axes3D(fig)
    #ax.scatter3D(outliers['time'], out_X, out_Y, c=outliers['mag3'])
    ax.scatter3D(outliers['time'], out_X, out_Y, c=outliers['time'])
    show()

def run_outliers(stars):
    """
    Do all calculations on the given stars and then plot the outliers
    """
    all_outliers = None
    for star in stars:
        print "STAR:", star
        make_summary(star)
        summary, outliers = process(star)
        if not len(outliers):
            continue
        if all_outliers is None:
            all_outliers = outliers
        else:
            all_outliers = N.hstack((all_outliers, outliers))
    print "N = ", len(all_outliers)
    plot_outlier_spiral(all_outliers)


if __name__=='__main__':
    stars = get_star_ids()

    run_outliers(stars[::30])
    
    

