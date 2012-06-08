"""
Utils for analysing the dark frames.
"""

import os

from pyraf import iraf
iraf.images()

from util.image import valid_images, groupby
from util.files import DARKPATH, darkfiles



def group_darks(cam, key1, key2):
    """
    Group the dark frames into a nested dictionary of Images,
    keyed by key1, then key2.
    """
    filenames = darkfiles(cam)
    images = valid_images(filenames)
    groups = groupby(images, key1)
    for key in groups:
        groups[key] = groupby(groups[key], key2)
    return groups


def make_dark_avg(images, out):
    """
    Create an average dark frame from a set of images.
    """
    filenames = [im.filename for im in images]
    iraf.imcombine(input=",".join(filenames), output=out, Stdout=0,
                   combine="median")
    return out

def make_dark_filename(cam, time, temp):
    """
    Create a filename for a given camera, exposure time and temperature.
    """
    filename = "%s_dark_avg_%1.3f_%d.fit" % (cam, time, int(temp))
    return os.path.join(DARKPATH, filename)

def make_dark_files(cam):
    """
    Create average dark frames for all combinations of exposure time
    and temperature for the given camera.
    """
    groups = group_darks(cam, "EXPTIME", "SETTEMP")
    for time in groups:
        for temp in groups[time]:
            images = groups[time][temp]
            out = make_dark_filename(cam, time, temp)
            make_dark_avg(images, out)
            print "Created", out
    
def main():
    make_dark_files("sbc")
    make_dark_files("sky")


if __name__ == '__main__':
    main()
