"""
Display Gattini images using the program C{ds9}.
"""

import os
import time

from pyraf import iraf
iraf.reset(stdimage="imt1600")

from processing.new_ops import produce_flat, get_cam_flat_filename

def _prep_ds9():
    """
    Open up an instance of C{ds9} if one is not already running.
    """
    if len(os.popen("ps aux | grep ds9 | grep $USER | grep -v grep").readlines()) == 0:
        os.system("ds9 &")
        time.sleep(3)

def display(outfile, frame=1):
    """
    Display a given file, using an optional frame number.
    """
    iraf.display(outfile, frame)

def single_display(image_id, frame=1):
    """
    Display the flat field reduced image for a given image ID (as defined in the GDB).
    """
    _prep_ds9()
    produce_flat(image_id, True)
    print "single", image_id
    filename, cam = get_cam_flat_filename(image_id)
    iraf.display(filename, frame)


def multi_display(image_ids):
    """
    Display multiple images, given as a list of image IDs (as defined in the GDB).
    """
    _prep_ds9()
    for i, image_id in enumerate(image_ids):
        single_display(image_id, i+1)
    

def main():
    """
    An example of using this module to open a set of images.
    """
    _prep_ds9()

    filenames = get_stripped_files("Sky", "060703", ("0100", "0300"))[:16]
    multi_display(filenames)


if __name__ == '__main__':
    from files import get_stripped_files
    
    main()
    print "DONE"


