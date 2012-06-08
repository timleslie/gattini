"""
2D image smoothing code.

Taken from U{http://www.scipy.org/Cookbook/SignalSmooth}.
"""
from scipy import signal, exp, mgrid

def gauss_kern(size, sizey=None):
    """ Returns a normalized 2D gauss kernel array for convolutions """
    size = int(size)
    if not sizey:
        sizey = size
    else:
        sizey = int(sizey)
    x, y = mgrid[-size:size+1, -sizey:sizey+1]
    g = exp(-(x**2/float(size)+y**2/float(sizey)))
    return g / g.sum()

def blur_image(im, n, ny=None) :
    """
    Blurs the image by convolving with a gaussian kernel of typical
    size C{n}. The optional keyword argument C{ny} allows for a different
    size in the y direction.
    """
    print "blur"
    g = gauss_kern(n, sizey=ny)
    print "got gauss"
    improc = signal.fftconvolve(im,g, mode='same')
    print "got new image", improc.shape, improc[0,0]

    
    return improc
