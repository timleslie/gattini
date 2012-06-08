from numpy import *
from pylab import *

from scipy.optimize import fmin

def gen_exp((x0, C, tau), t, y):
    delta_y = y - f(x0, C, tau, t) #(x0 + C*exp(-t/tau))
    #delta_y = y - (x0 + C*10**(-t/tau))
    print x0, C, tau, sqrt(sum(delta_y**2))
    return sqrt(sum(delta_y**2))


def f(x0, C, tau, t):
    return x0 + C*log10(t/tau)
    return x0 + C*exp(-t/tau)

def main():
    y = array([-13.29, -14.18, -14.76, -15.  , -16.5 ])
    t = array([ 2,  5,  8, 10, 40])

    
    #x0 = (-16.58, 3.94, 10.5)
    x0 = (-12.5, - 2.5, 1)

    x1 = fmin(gen_exp, x0, (t, y))
    (x, C, tau) = x1
    plot(t, f(x, C, tau, t))
    plot(t, y)
    #show()
    print x0, x1

main()
# /home/iraf/iraf/noao/digiphot/apphot/phot/t_phot.x
