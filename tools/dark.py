"""
Attempt to analyse the properties of dark frames as a function of exposure time
and CCD temperature.
"""

from util.dark import group_darks
from util.regress import regress

def analyse_darks(cam):    
    """
    Try to fit a linear model to dark frames.
    """

    # Collect the data
    groups = group_darks(cam, "EXPTIME", "SETTEMP")
    print cam
    data = []
    for time in groups:
        for temp in groups[time]:
            for image in groups[time][temp]:
                data.append([image.MEAN, time, temp])
             
    # Do the regression
    beta0, beta1, beta2 = regress(data)
    print "count = %f + %ft + %fT" % (beta0, beta1, beta2)

    # Calculate residuals
    resids = []
    key_sorted = groups.keys()
    key_sorted.sort()
    for time in key_sorted:
        res = []
        key2_sorted = groups[time].keys()
        key2_sorted.sort()
        for temp in key2_sorted:
            r = []
            for image in groups[time][temp]:
                r.append(image.MEAN - (beta0 + beta1*time + beta2*temp))
            res.append(avg(r))
        resids.append(res)


    # Display residual results
    print resids
    print key_sorted, key2_sorted

def count_darks(cam, key1="EXPTIME", key2="SETTEMP"):    
    """
    Count the number of dark frames we have for the given
    camera. Report by key1 then key2.
    """
    groups = group_darks(cam, key1, key2)
    print "Dark Frame Count for", cam
    for key in groups:
        print key
        for key2 in groups[key]:
            print "\t", key2, len(groups[key][key2]), \
                  avg([im.MEAN for im in groups[key][key2]]), \
                  avg([im.STDDEV for im in groups[key][key2]]), \
                  avg([im.MIN for im in groups[key][key2]])

def avg(lst):
    """ Calculate the average of a list of values.

    Raises ZeroDivisionError on empty input.
    """
    return sum(lst)/len(lst)


def main():
    analyse_darks("sbc")
    analyse_darks("sky")

    count_darks("sbc", "SETTEMP", "EXPTIME")
    count_darks("sky")

if __name__ == '__main__':
    main()
