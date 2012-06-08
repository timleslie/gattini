"""
A class and various functions for repreenting and manipulating images
and groups of images.
"""

import pyfits
from pyraf import iraf
iraf.images()

import os


class Image(object):
    """
    A class to represent a single camera image.
    """

    def __init__(self, filename):
        """
        Create an Image for the given filename. If successful the
        valid attribute is set to True
        """
        self.filename = filename
        self.stat = _imstat(filename)
        self.header, self.header_dict = _imheader(filename)
        self.header_attr = self._make_header_attr()
        if self.stat == {} or \
           self.header_dict == {}:
            self.valid = False
        else:
            self.valid = True

    def _make_header_attr(self):
        """
        Remove any '-' characters in dictionary keys, as these can't
        be accessed as image.key.
        """
        header = {}
        for key, val in self.header_dict.items():
            if "-" in key:
                key = key.replace("-", "")
            header[key] = val
        return header

    def __getattr__(self, key):
        """
        The various dictionaries can be accessed as if they were
        normal attributes.
        """    
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self.stat:
            return self.stat[key]
        elif key in self.header_attr:
            return self.header_attr[key]
        else:
            raise AttributeError, key


    def normalise(self, out=None):
        """
        Normalise the image.
        """
        if out is None:
            name, ext = os.path.splitext(self.filename)
            out = name + "_norm" + ext
        iraf.imarith(self.filename, "/", self.MEAN, out)
        return out

    def divide(self, image, out=None):
        """
        Divide this image by another image.
        """
        return self._op(image, "over", "/", out)

    def add(self, image, out=None):
        """
        Add another image to this one.
        """
        return self._op(image, "plus", "+", out)

    def subtract(self, image, out=None):
        """
        Subtract another image from this one.
        """
        return self._op(image, "minus", "-", out)

    def multiply(self, image, out=None):
        """
        Multiply this image by another one.
        """
        return self._op(image, "times", "*", out)

    def _op(self, image, name, symbol, out):
        """
        Apply a particular operation on this image and another image.
        """
        if type(image) == Image:
            filename = image.filename
        else:
            filename = image
        if out is None:
            name1, ext1 = os.path.splitext(self.filename)
            name2, _ = os.path.splitext(filename)
            path1, name1 = os.path.split(name1)
            _, name2 = os.path.split(name2)
            out = os.path.join(path1, name1 + "_%s_"  % name + name2 + ext1)
        iraf.imarith(self.filename, symbol, filename, out)

        return out



def _imstat(filename):
    """
    Call imstat on a file and convert the result to a dictionary.
    """
    s = iraf.imstat(filename, Stdout=1)
    if s[1].startswith("Error"):
        return {}

    stat_dict = dict(zip(s[0].split()[1:], s[1].split()))
    for key, val in stat_dict.items():
        try:
            val = float(val)
        except ValueError:
            pass
        stat_dict[key] = val
    return stat_dict

def _imheader(filename):
    """
    Use pyfits to generate a dictionary of header values for the given file.
    """
    header = pyfits.getheader(filename)
    header_dict = dict(header.items())
    return header, header_dict


def sortby(images, key):
    """
    Sort a list of images using a given attribute as the key
    """
    images.sort(key = lambda image: image.__getattr__(key))

def groupby(images, key):
    """
    Convert a list of images into a dictionary of {val: [image]} where
    val is the value of a given key for all [image].
    """
    groups = {}
    for im in images:
        val = im.__getattr__(key)
        groups[val] = groups.get(val, [])        
        groups[val].append(im)
    return groups

def avg_images(images, out):
    """
    Create an average image from a list of images using imcombine.
    Writes to the file out.
    """
    filelist = "tmp.txt"
    f = open(filelist, "w")
    for image in images:
        f.write("%s\n" % image.filename)
    f.close()
    iraf.imcombine(input="@%s" % filelist, output=out, Stdout=1)
    os.remove(filelist)
    return out

def valid_images(filenames):
    """
    Return a list of valid images from a list of filenames.
    """
    images = [Image(filename) for filename in filenames]
    return [image for image in images if image.valid]
