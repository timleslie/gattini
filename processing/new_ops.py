import os
from datetime import datetime
import time

from pyfits import getheader
from pyraf import iraf
from pyraf.subproc import SubprocessError
from pyraf import irafglobals
iraf.apt()

from db.db import run_sql, run_sql_single
from util.image import _imstat, Image
from util.files import FLATPATH

def lparam(function):    
    s = iraf.lparam(function, Stdout=1)
    s = [line.strip().split("   ")[0].strip("()").split(" =") for line in s]
    s = dict(s)
    for k, v in s.items():
        s[k] = v.strip()
    return s

def get_cam_filename(image_id):
    sql = "SELECT filename, cam.name FROM image " \
          "INNER JOIN cam ON image.cam_id = cam.id "\
          "WHERE image.id = %d" % image_id
    return run_sql(sql)[0]

def get_unzipped_filename(image_id):
    sql = "SELECT outputfile FROM unzip WHERE image_id=%d" % image_id
    return run_sql_single(sql)


def get_cam_unzipped_filename(image_id):
    sql = "SELECT unzip.outputfile, cam.name FROM image " \
          "INNER JOIN cam ON image.cam_id = cam.id "\
          "INNER JOIN unzip ON image.id = unzip.image_id "\
          "WHERE image.id = %d" % image_id
    return run_sql(sql)[0]

def get_cam_flat_filename(image_id):
    sql = "SELECT flat.outputfile, cam.name FROM image " \
          "INNER JOIN cam ON image.cam_id = cam.id "\
          "INNER JOIN flat ON image.id = flat.image_id "\
          "WHERE image.id = %d" % image_id
    return run_sql(sql)[0]



##############

def unzip_fail(image_id):
    sql = "REPLACE INTO unzip values(%d, 0, NULL)" % image_id
    print "UNZIP FAIL!"
    run_sql(sql)

def unzip_pass(image_id, outfile):
    sql = "REPLACE INTO unzip values (%d, 1, '%s')" % (image_id, outfile)
    print "I put it in", outfile
    run_sql(sql)
    
def unzip(image_id):

    filename, cam = get_cam_filename(image_id)

    path = os.path.join("/mnt/hda/timl/data", cam)
    if not os.path.exists(filename):
        return unzip_fail(image_id)
    print "copying from", filename, "to", path
    os.system("cp %s %s" % (filename, path))
    base_name = os.path.split(filename)[1]
    zip_file = os.path.join(path, base_name)
    try:
        os.system("bunzip2 %s 2&> /dev/null" % zip_file )
    except OSError:
        return unzip_fail(image_id)
    outfile = os.path.splitext(zip_file)[0]
    return unzip_pass(image_id, outfile)


###########

def read_header(image_id):
    filename = get_unzipped_filename(image_id)
    header = getheader(filename)
    d = dict(header.items())
    sql = "INSERT IGNORE INTO header VALUES (" \
          "%d, %f, %f, '%s', %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f)" % \
          (image_id, d["TEMP"], d["EXPOSURE"], " ".join(d["DATE"].split("T")),
           d["SUNZD"], d["MOONZD"], d["MOONDIST"], d["MOONPHSE"], d["MOONMAG"],
           d["RA"], d["DEC"], d["LST"], d["JD"], d["CRVAL1"], d["CRVAL2"])
    run_sql(sql)
       

###########

def apt_ephem(image_id):
    filename = get_unzipped_filename(image_id)
    os.system("apt_ephem -obs domec %s > /dev/null" % filename)        

################


apt_astrom_d = {"sbc": (-42, False, "tycho", 5, 20),
                "sky": (189, True, "tycho", 3, 6)}

    
def apt_astrom(image_id):
    print "apt_astrom"
    sql = "SELECT * FROM astrom where image_id=%d" % image_id
    if len(run_sql(sql)) > 0:
        print "bailing"
        #return


    filename, cam = get_cam_flat_filename(image_id)
    rot, refine, cat, range, maxmag= apt_astrom_d[cam]
    
    try:
        print "running aptastrom", filename, range, rot, refine, cam, cat, maxmag
        iraf.AptAstrom(filename, range=range, rotate=rot,
                       display=False, refine=refine, Stdout=1,
                       box=300, telescope=cam, cat=cat, maxmag=maxmag)
    except SubprocessError, e:
        print "failing on subprocess error"
        success = False
    except irafglobals.IrafError:
        print "failing on iraf error"
        success = False

    d2 = dict(getheader(filename).items())
    print "d2 =", d2
    try:
        sql = "REPLACE INTO astrom VALUES (" \
              "%d, %d, %f, %f, %f)" % \
              (image_id, d2["ASTROMOK"], d2["SMAG"], d2["ZMAG"], d2["SKY"])
    except KeyError:
        sql = "REPLACE INTO astrom VALUES (%d, 0, 0, 0, 0)" % image_id
    print "SQL:", sql
    run_sql(sql)

##################    


def imstat(image_id):
    filename = get_unzipped_filename(image_id)
    d = _imstat(filename)
    sql  = "INSERT IGNORE INTO imstat VALUES ("\
           "%d, %d, %d, %d, %d)" % (image_id, d["MIN"], d["MAX"],
                                    d["MEAN"], d["STDDEV"])
    run_sql(sql)

#########


def get_outfile(filename):
    base, ext = os.path.splitext(filename)
    return base + ".phot.txt"


apt_phot_d = {"sbc": ("tycho", 20),
              "sky": ("tycho", 6)}

apt_phot_keys = ["RA", "Dec", "Vmag", "Vmag", "ID", "X", "Y", "smag", \
                 "mag3", "mag4", "err3", "err4"]


def apt_phot(image_id):
    print "apt_phot"
    sql = "SELECT * from phot where image_id=%d" % image_id
    if len(run_sql(sql)) > 0:
        return

    sql = "SELECT success FROM astrom where image_id=%d" % image_id
    if run_sql_single(sql) == 0:
        sql = "INSERT IGNORE INTO starcount values (%d, 0)" % image_id
        run_sql(sql)
        print "taking the easy way out"
        return 

    filename, cam = get_cam_flat_filename(image_id)
    outfile = get_outfile(filename)
    cat, maxmag = apt_phot_d[cam]
    iraf.AptPhot(filename, outfile, cat, maxmag=maxmag)

    f = open(outfile)
    n = 0
    for line in f:
        vals = line.split()
        for i in range(len(vals)):
            if vals[i] == 'INDEF':
                vals[i] = '1e-40' #HACK. how to get an Nan in mysql?
        d = dict(zip(apt_phot_keys, vals))

        sql = "INSERT IGNORE INTO star (cat_id, ra, decl) VALUES( %(ID)s, %(RA)s, %(Dec)s)" % d
        run_sql(sql)
        
        sql = "INSERT INTO phot SELECT " + str(image_id)
        sql += (", star_id, %(Vmag)s, %(smag)s, %(mag3)s, %(mag4)s, '%(err3)s', '%(err4)s', %(X)s, %(Y)s from star where cat_id = %(ID)s" % d)
        run_sql(sql)
        n += 1
    sql = "INSERT IGNORE INTO starcount values (%d, %d)" % (image_id, n)
    run_sql(sql)

##############

flat_d = {"sbc": "uber_flat_sbc_norm.fit",
          "sky": "uber_flat_sky_norm.fit"}

def flat(image_id):
    filename, cam = get_cam_unzipped_filename(image_id)

    flatfile = os.path.join(FLATPATH, flat_d[cam])
    image = Image(filename)
    name, ext = os.path.splitext(filename)
    out = name + ".flat" + ext
    image.divide(flatfile, out)

    sql = "REPLACE INTO flat VALUES (%d, '%s', '%s')" % \
          (image_id, flatfile, out)
    run_sql(sql)

def _produce_flat(image_id, filename=None):
    if filename and os.path.exists(filename):
        print "already there"
        return

    print "making flat"
    unzip(image_id)
    print "unzipped"
    apt_ephem(image_id)
    print "ephemed"
    imstat(image_id)
    print "stated"
    read_header(image_id)
    print "REad header"
    flat(image_id)
    print "made flat"

def produce_flat(image_id, flag=False):
    print "MAKING FLAT"
    flag = True
    try:
        filename = get_cam_flat_filename(image_id)[0]
        print "got filename:", filename
    except IndexError:
        print "got NONE"
        filename = None
    if filename is None or flag:
        print "_producing_flat"
        _produce_flat(image_id, filename)
        

def run_photometry(image_id):
    apt_astrom(image_id)
    apt_phot(image_id)

def clean_up(image_id):
    sql = "select outputfile from unzip where image_id = %d" % image_id
    filename = run_sql_single(sql)
    try:
        os.remove(filename)
    except OSError:
        pass
    
    sql = "select outputfile from flat where image_id = %d" % image_id
    filename = run_sql_single(sql)
    try:
        os.remove(filename)
    except OSError:
        pass
    

def single_phot(image_id):
    t0 = time.time()
    print image_id
    
    # Initial processing
    produce_flat(image_id)
    
    # Photometry
    run_photometry(image_id)
    clean_up(image_id)
    print time.time() - t0
    
def batch_phot(cam, frm, to):

    images = get_images_by_date_and_cam(cam, frm, to)

    #images = range(22001, 23000, 51)

    for image_id in images[::20]:
        single_phot(image_id)

def get_images_by_date_and_cam(cam, frm, to):

    sql = "select image.id from " \
          "image inner join cam on image.cam_id=cam.id " \
          "where time > '%s' and time < '%s' and cam.name='%s'" % \
          (frm, to, cam)
    return run_sql(sql)['id']

if __name__ == '__main__':
    #main()
    #batch_phot("sky", "060723", "060724")
    #batch_phot("sbc", "060101", "061201")
    #batch_phot("sbc", "060608", "060718")
    #batch_phot("sbc", "060701", "0607010100")
    single_phot(90000)
    pass
