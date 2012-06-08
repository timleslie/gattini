"""
Generate histograms of the dark file images to see if their distributions are
of any particular form.

This code is quick, dirty and ugly, use at own risk :)
"""

import os

from pylab import subplot, imshow, hist, title, savefig, clf, cm, show, plot, exp, log, sqrt

ln = log

from pyfits import getdata, getheader
import numpy as N
import scipy.stats
from scipy.optimize import fmin, anneal

from scipy import mean, std, histogram
import scipy.stats
from scipy.linalg import norm

from util.files import darkfiles
from scipy.misc.common import factorial as fact
from scipy.special import digamma

P = scipy.stats.distributions.poisson.pmf
B = scipy.stats.distributions.binom.pmf
Nm = scipy.stats.distributions.norm.pdf
G = scipy.stats.distributions.gamma.pdf


def trigamma(k):
    if k < 8:
        return trigamma(k+1) + 1/k**2
    else:
        return (1 + (1 + (1 - (1./5  - 1/(7*k**2))/k**2)/(3*k))/(2*k))/k

def new_k(k, s):
    return k - (ln(k) - digamma(k) - s)/((1/k) - trigamma(k))

def est1(data, _):
    mu = data.mean()
    sd = data.std()
    theta = sd**2/mu
    k = mu/theta

    return k, theta, 0


def est2(data, _):
    n = float(len(data))

    s = ln(sum(data)/n) - sum(ln(data[data > 0]))/n
    k = (3 - s + sqrt((s-3)**2 + 24*s))/(12*s)

    k = new_k(new_k(k, s), s)
    return k, sum(data)/(n*k), 0

def hist_dist((x0, theta, k), h, ns):
    g = N.nan_to_num(gamma(k, theta, ns, x0))
    #print x0, theta, k
    dist = norm(h - g)
    print x0, theta, k, dist
    return dist

def est3(data, (_x0, _theta, _k)):

    h = histogram(data, data.max(), normed=1)[0]
    ns = N.arange(0, data.max())

    #k, theta, x0 = est2(data)
    k, theta, x0 = _k, _theta, _x0

    x0, theta, k = fmin(hist_dist, (x0, theta, k), args=(h, ns), maxiter=10000, maxfun=10000, xtol=1.0)
    #f = open("hist_results.txt", 'a')
    #f.write("%f, %f, %f\n" % (x0, theta, k))
    #f.close()
    #k, theta, x0 = anneal(hist_dist, (k, theta, x0), args=(h, ns))
    # 297, 524
    #k, theta, x0, mu, sd 2.81512082346 107.938664162 302.190920629 606.051301768 32798.2836321
    #k, theta, x0, mu, sd 2.81512082346 107.938664162 302.190920629 606.051301768 32798.2836321


    return k, theta, x0

def pois(x0, mu, ns):
    return N.array([P(n, mu) for n in ns - x0])

i = 0
def hist_dist_P((x0, ), mu, h, ns):
    global i
    x0 = int(x0)
    mu = mu - x0
    p = N.nan_to_num(pois(x0, mu, ns))
    dist = norm(h - p)
    plot(ns, p)
    print N.max(h), N.argmax(h), N.max(p), N.argmax(p)
    print x0, mu, sum(p), dist
    i += 1
    if i == 10:
        show()
    return dist



def est4(data, _):
    h = histogram(data, data.max(), range=(0, data.max()), normed=1)[0]
    ns = N.arange(0, data.max())

    #k, theta, x0 = est2(data)
    #k, theta, x0 = _k, _theta, _x0
    print "shape =", len(data), type(data), data.shape
    x0 = data.min()
    x0 = 10
    sd = data.std()
    print "SD", sd, sd**2, data.mean()
    x0 = data.mean() - 4*sd
    x0 = fmin(hist_dist_P, (x0,), args=(data.mean(), h, ns), xtol=1.0)

    return 0, 0, x0

def gamma(k, theta, ns, x0=0):
    return N.array([float(G(n, k, x0, theta)) for n in ns])


def ests(data, (_x0, _theta, _k)):
    x0 = data.min()
    #data -= data.min()
    data = data.astype(float)
    ns = N.arange(0, data.max())
    ests = []
    for est in [est4]:#[est3, est2, est1]:
        k, theta, x0 = est(data, (_x0, _theta, _k))
        print "k, theta, x0, mu, sd", k, theta, x0, x0 + k*theta, k*theta**2
        #ests.append(gamma(k, theta, ns, x0))
        ests.append(pois(int(x0), (data - x0).mean(), ns))
        print ests[0]
    return ests
    

def main():    
    results_dir = "../results/hist"


    lines = open("hist_results.txt", "r").readlines()
    #print len(lines)
    
    for filename, line in zip((darkfiles("sbc") + darkfiles("sky")), lines)[1:2]:
        x0, theta, k = map(float, line.split(","))
        print x0, theta, k
        
        base, _ = os.path.splitext(filename)
        outname = base + ".hist.png"
        _, outname = os.path.split(outname)
        outname = os.path.join(results_dir, outname)
        print filename, outname
        
        data = N.asarray(getdata(filename))
        #print "min =", min(data.flat)
    
        #subplot(211)
        #imshow(scipy.stats.zs(data) < 5, cmap=cm.gray)
    
        #subplot(212)
        data = data.flatten()
        data = data[abs(scipy.stats.zs(data)) < 6]
        
        x0 = min(data.flat)
        mu = data.astype(float).mean()
        sd = data.astype(float).std()
        p = (mu - x0)/data.size
        
        #x0 = mu - 2*(mu - x0)
        print (x0, data.max())
        ns = N.arange(x0, data.max())
        #print "mu =", mu, mu - x0, std(data.flatten())**2
        #print "a"
        header = dict(getheader(filename).items())
        #print "b", len(data.flat), data.max() - data.min(), histogram(data.flat)
        hist(data.flat, data.max() - data.min(), normed=1)
        #print "c"
        # plot(ns, [float(P(n - x0, mu - x0)) for n in ns], linewidth=2, c='r')
        # plot(ns, [float(Nm(n, mu, sd)) for n in ns], linewidth=2, c='y')
        # plot(ns, [float(G(n, 6.0, x0, sd*0.7)) for n in ns], linewidth=2, c='g')
        # plot(ns, [float(G(n, k, 0, theta)) for n in ns], linewidth=2, c='g')

        #gdat, gdat0, gdat1 = ests(data, (x0,theta,k))
        [gdat] = ests(data, (x0,theta,k))
        print N.max(gdat), N.argmax(gdat)
        plot(gdat, linewidth=2, c='y')
        #plot(ns, gdat0, linewidth=2, c='r')
        #plot(ns, gdat1, linewidth=2, c='y')

        title("Time: %1.3fs, Temp: %1.1fC (%1.0fC) (%1.0f += %1.1f)" %
              (header['EXPTIME'], header['CCD-TEMP'], header['SET-TEMP'],
               mean(data.flatten().astype(float)), std(data.flatten().astype(float)) ))
        #savefig(outname)
        show()
        clf()

if __name__ == '__main__':
    main()
    #files = (darkfiles("sbc") + darkfiles("sky"))
    #lines = open("hist_results.txt", "r").readlines()
    #print len(files), len(lines)
