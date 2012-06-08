import os

if __name__ == '__main__':

    from pyraf import iraf
    iraf.apt()
    
    from util.files import getfiles
    
    files = getfiles("SBC", ("0607010000", "0607020000"))
    for f in files:
        os.system("cp %s ." % f)
        zipname = f.split("/")[-1]
        
        os.system("bunzip2 %s" % zipname)
        fitsname = ".".join(zipname.split(".")[:-1])
        os.system("/home/mcba/apt_ephem -obs domec %s" % fitsname)
        
        number = zipname.split(".")[0]
        print zipname, number, fitsname
        
        try:
            iraf.AptMagFlat(number + ".SBC", "flats/" + number + ".SBC.flat", rm=True)
        except:
            pass

        print f
