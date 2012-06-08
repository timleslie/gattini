"""
Functions to handle image filenames
"""

import os
from datetime import date, datetime, timedelta

def fullpathlist(path):
    """
    A list of filenames (path included) in the given path.
    """
    try:
        return [os.path.join(path, filename) for filename in os.listdir(path)]
    except OSError:
        return []

def darkpath(cam):
    """
    The path for the dark files for the given camera.
    """
    return os.path.join(BASEPATH, cam  + "_dark")

def flatpath(cam):
    """
    The path for the flat files for the given camera.
    """
    return os.path.join(BASEPATH, cam + "_flats")

def darkfiles(cam):
    """
    A list of dark files for the given camera.
    """
    return fullpathlist(darkpath(cam))

def flatfiles(cam):
    """
    A list of flat files for the given camera.
    """
    return fullpathlist(flatpath(cam))

def flatdatafiles(cam):
    return filter_filenames(fullpathlist(FLATDATAPATH), [cam])

def filter_filenames(filenames, filters, inverse=False):
    """
    A function to filter a list of filenames. filters is a list
    of substrings which must all exist in the filename for it to be kept.
    If inverse is True then all substrings must _not_ exist for the filename
    to be kept.
    """
    out = []
    for filename in filenames:
        for filt in filters:
            if (filt not in filename) + (inverse) == 1:
                break
        else:
            out.append(filename)
    return out

def remove_spaces(filenames):
    """
    Renames the list of filenames to replace any spaces in the filenames
    with underscores.
    """
    for filename in filenames:
        if " " in filename:
            new_name = filename.replace(" ", "_")
            print "replacing", filename, "with", new_name
            os.rename(filename, new_name)

# The root of all data.
if os.popen("hostname").read().strip() == 'feynman':
    # my home system
    BASEPATH = "/home/timl/data/gattini"
else:
    # mcba11
    BASEPATH = "/home/timl/data"

# The path to output dark frames to
DARKPATH = os.path.join(BASEPATH, "dark_avg")

# The path to output flat frames to
FLATPATH = os.path.join(BASEPATH, "flat_avg")

# The path with the original data
DATAPATH = os.path.join(BASEPATH, "06fits")

# The path where flattened images live
FLATDATAPATH = os.path.join(BASEPATH, "flat_data")

#
ALLDATA = "/data3/mcba"

def datafiles(cam, date=None):
    """
    Return a list of filenames of the data for a given camera. Filter by
    date if given
    """
    files = [fn for fn in fullpathlist(DATAPATH) if cam in fn]
    if date:
        files = filter_filenames(files, [date])
    return files



def unzipdir(path):
    """
    bunzip2 all bz2 images in a given path
    """
    filenames = fullpathlist(path)
    for filename in filenames:
        if filename.endswith("bz2"):
            print "doing", filename
            os.system('bunzip2 "%s"' % filename)
        else:
            print "skipping", filename


def strtodate(s):
    year, month, day = int(s[0:2]), int(s[2:4]), int(s[4:6])
    year += 2000 # Y2K bug :-)
    return date(year, month, day)

def strtodatetime(s):
    year, month, day, hour, minute = int(s[0:2]), \
                                     int(s[2:4]), \
                                     int(s[4:6]), \
                                     int(s[6:8]), \
                                     int(s[8:10])
    year += 2000
    return datetime(year, month, day, hour, minute)

def datetostr(d):
    year = str(d.year)[2:4]
    month = str(d.month).zfill(2)
    day = str(d.day).zfill(2)
    return year + month + day
    

def dates_from_tuple((frm, to)):
    # FIXME: implement this
    frm = strtodate(frm)
    to = strtodate(to)

    single_day = timedelta(1)
    dates = []
    while frm < to:
        dates.append(frm)
        frm += single_day

    return map(datetostr, dates)

def _prepare_dates(dates):
    if type(dates) == str:
        dates = [dates]
    elif type(dates) == tuple:
        dates = dates_from_tuple(dates)
    elif dates is None:
        dates = [dir for dir in os.listdir(ALLDATA) if dir.startswith("07")]
    return dates

def getdirs(dates=None):
    dates = _prepare_dates(dates)
    return [os.path.join(ALLDATA, date) for date in dates]

def getfiles(cam, dates=None, times=None):
    dates = _prepare_dates(dates)

    if type(times) == str:
        times = [times]
    elif type(times) == tuple:
        times = tuple(map(int, times))
    elif times is None:
        times = (0, 2400)

    filenames = []
    for date in dates:
        path = os.path.join(ALLDATA, date)
        files = filter_filenames(fullpathlist(path), cam)
        files = [(f, os.path.split(f)[1][6:10]) for f in files]
        if type(times) == list:
            files = [f for (f, t) in files if t in times]
        elif type(times) == tuple:
            files = [f for (f, t) in files if times[0] <= int(t) < times[1]]
        filenames += files
    filenames = filter_filenames(filenames, [".fits."])
    return filenames

def get_stripped_files(cam, dates=None, times=None):
    files = getfiles(cam, dates, times)
    return strip_files(files)

def strip_files(files):
    files = [os.path.split(fn)[1] for fn in files]
    files = [os.path.splitext(fn)[0] for fn in files]
    files = [os.path.splitext(fn)[0] for fn in files]
    return files


def file_from_base(base):
    dir = base[:6]
    path = os.path.join(ALLDATA, dir)
    return os.path.join(path, base) + ".fits.bz2"

    
def main():
    os.mkdir(DARKPATH)
    os.mkdir(FLATPATH)
    os.mkdir(FLATDATAPATH)

    unzipdir(darkpath("sky"))
    unzipdir(darkpath("sbc"))
    unzipdir(flatpath("sky"))
    unzipdir(flatpath("sbc"))

    remove_spaces(darkfiles("sky"))
    remove_spaces(darkfiles("sbc"))
    remove_spaces(flatfiles("sky"))
    remove_spaces(flatfiles("sbc"))

    unzipdir(DATAPATH)


if __name__ == '__main__':
    #main()

    #getfiles("SBC", ["060702", "060703"], ("0033", "0133"))
    #getfiles("Sky", ["060702", "060703"], ("0033", "0133"))
    files = getfiles("SBC", ("070701", "070801"))
    print len(files)
    files = getfiles("Sky")
    print len(files)
    files = getfiles("SBC")
    print len(files)


