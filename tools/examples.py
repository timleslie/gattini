"""
An example of using some of the libraries.
"""

from util.image import Image, sortby, valid_images
from util.files import darkfiles


def image_sort_example():
    """
    Sort a bunch of images based on different keys
    """
    files = darkfiles("sbc")
    images = valid_images(files)

    image = Image(files[0])
    print image.MIN
    print image.BSCALE

    sortby(images, "MAX")
    print [image.MAX for image in images]

    sortby(images, "MEAN")
    print [image.MEAN for image in images]

if __name__ == '__main__':
    image_sort_example()
