from pylab import *
from pyfits import getdata


if __name__ == '__main__':
    rcParams['figure.figsize'] = (13.5, 8)

    for filename in[ "/home/timl/data/flat_avg/uber_flat_sky_norm.fit",
                     "/home/timl/data/flat_avg/uber_flat_sbc_norm.fit"]:

        clf()
        f_base = filename.split("/")[-1].split(".")[0]
        cam = f_base.split("_")[2]
        data = array(getdata(filename))
        
        imshow(data)
        colorbar()
        savefig("/home/timl/thesis/images/flat_%s.eps" % cam)
        #show()
