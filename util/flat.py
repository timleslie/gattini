"""
Tools for processing flat files.
"""

import os

from image import valid_images, groupby, Image, avg_images
from files import FLATPATH, flatfiles, filter_filenames

#import iraf
#iraf.images()


def get_light_sbc(filenames, onoff=True):    
    """
    Filter sbc filenames for light on or off
    """
    if onoff:
        param = "on"
    else:
        param = "off"
    return filter_filenames(filenames, [param])

def get_light_sky(filenames, onoff=True):
    """
    Filter sky filenames for light on or off
    """
    return filter_filenames(filenames, ["light-off"], onoff)

def get_lens(filenames, yesno=True):
    """
    Filter filenames for lens yes/no.
    """
    if yesno:
        param = "yes_lens"
    else:
        param = "no_lens"
    return filter_filenames(filenames, [param])


def get_ndc(filenames, yesno=True):
    """
    Filter filenames for ncd on/off.
    """
    return filter_filenames(filenames, ["ndc"], not yesno)

def get_good(filenames, good=True):
    """
    Filter filenames for good/not good.
    """
    return filter_filenames(filenames, ["good"], not good)

def get_window_sbc(filenames, yesno=True):
    """
    Filter sbc filenames for window yes/no.
    """
    return filter_filenames(filenames, ["yes_window"], not yesno)

def get_window_sky(filenames, yesno=True):
    """
    Filter sky filenames for window yes/no.
    """
    return filter_filenames(filenames, ["window"], not yesno)

def process_images(images, cam, params):
    """
    Process a set of images for a given camera with the given params.
    For the sbc cam, params = (light, lens, window)
    For the sky cam, params = (light, lens, ndc, good, window)

    This finds the appropriate images, groups them by exposure time
    and then makes average flats at each exp time.
    """
    print cam, params
    groups = groupby(images, "EXPTIME")
    for time, ims in groups.items():
        func = {"sbc": make_sbc_flat_name, "sky": make_sky_flat_name}[cam]
        out = func(time, params)
        out = os.path.join(FLATPATH, out)
        print time, len(ims), out
        make_flat_avg(ims, out)

def make_sbc_flat_name(time, (light, lens, window)):
    """
    Make a file name for an sbc flat with given params.
    """
    return "sbc_flat_avg_%1.3f%s%s%s.fit" % (time,
                                             ["", "_light"][light],
                                             ["", "_lens"][lens],
                                             ["", "_window"][window])

def make_sky_flat_name(time, (light, lens, ndc, good, window)):
    """
    Make a file name for a sky flat with given params.
    """
    return "sky_flat_avg_%1.3f%s%s%s%s%s.fit" % (time,
                                                 ["", "_light"][light],
                                                 ["", "_lens"][lens],
                                                 ["", "_ndc"][ndc],
                                                 ["", "_good"][good],
                                                 ["", "_window"][window])


def make_flat_avg(images, out):    
    """
    Create a flat average of images and also a normalised version.
    """
    image = Image(avg_images(images, out))
    image.normalise()
    return out

def make_uber_flat(cam):
    """
    Create a flat which is the average of all available flats for camera.
    """
    files = flatfiles(cam)
    images = valid_images(files)
    make_flat_avg(images, os.path.join(FLATPATH, "uber_flat_%s.fit" % cam))

def sbc_groups():
    """
    Process each of the different parameter groups for the sbc cam.
    """
    cam = "sbc"
    for light, lens, window in [(True, True, True),
                                (True, True, False),
                                (True, False, False),
                                (False, False, False)]:        
        filenames = flatfiles(cam)
        filenames = get_light_sbc(filenames, light)
        filenames = get_lens(filenames, lens)
        filenames = get_window_sbc(filenames, window)
        images = valid_images(filenames)
        process_images(images, cam, (light, lens, window))

def sky_groups():
    """
    Process each of the different parameter groups for the sky cam.
    """
    cam = "sky"
    for light, lens, ndc, good, window in [(True, True, False, True, True),
                                           (True, True, False, True, False),
                                           (True, True, False, False, False),
                                           (True, False, False, True, False),
                                           (True, False, False, False, False),
                                           (False, True, False, True, True),
                                           (False, True, False, False, True)]:
        filenames = flatfiles(cam)
        filenames = get_light_sky(filenames, light)
        filenames = get_lens(filenames, lens)
        filenames = get_ndc(filenames, ndc)
        filenames = get_good(filenames, good)
        filenames = get_window_sky(filenames, window)
        images = valid_images(filenames)
        process_images(images, cam, (light, lens, ndc, good, window))
        
def main():
    sbc_groups()
    sky_groups()
    make_uber_flat("sbc")
    make_uber_flat("sky")


if __name__ == '__main__':
    print "main..."
    main()
