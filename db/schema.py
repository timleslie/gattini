"""
This module defines the GDB schema. Each function creates a single table which
together form the entire GDB.

WARNING: Running these functions will destroy any existing database. Only call
these functions if you are sure you want to start from scratch. This will
involve rerunning months of CPU time! Don't call these functions!
"""

from db import drop_table, create_table, id_field, pk_field, fk_field, \
     int_field, float_field, str_field, type_field, run_sql

def create_image_table():
    """
    The C{image} table defines a mapping between filenames and C{image_id}s.
    These C{image_id}s are used as the primary method of identifying images in
    the rest of the system.
    """
    create_table("image", 
                 [id_field("id", "INT"),
                  str_field("filename", 100, True),
                  str_field("basename", 50, True),
                  type_field("cam_id", "TINYINT"),
                  type_field("time", "DATETIME"),
                  fk_field("cam_id", "cam(id)")])
          

def create_cam_table():
    """
    The C{cam} table defines a mapping between camera names and C{cam_id}s.
    """
    drop_table("image")
    create_table("cam",
                 [id_field("id", "TINYINT"),
                  "name CHAR(3) NOT NULL UNIQUE"])



def create_unzip_table():
    """
    The C{unzip} table keeps track of which images have been unzipped and the
    resulting filenames.
    """
    create_table("unzip", 
                 [pk_field("image_id", "INT"),
                  type_field("success", "TINYINT"),
                  str_field("outputfile", 50, True),
                  fk_field("image_id", "image(id)")])


def create_imstat_table():
    """
    The C{imstat} table stores the result of running C{imstat} on each image.
    """
    create_table("imstat", 
                 [pk_field("image_id", "INT"),
                  int_field("min"),
                  int_field("max"),
                  int_field("mean"),
                  int_field("stddev"),
                  fk_field("image_id", "image(id)")])



def create_header_table():
    """
    The C{header} table stores a selection of FITS header fields from each image.
    """
    create_table("header", 
                 [pk_field("image_id", "INT"),
                  float_field("temp"),
                  float_field("exposure"),
                  type_field("time", "DATETIME"),
                  float_field("sunzd"),
                  float_field("moonzd"),
                  float_field("moondist"),
                  float_field("moonphase"),
                  float_field("moonmag"),
                  float_field("ra"),
                  float_field("decl"),
                  float_field("lst"),
                  float_field("jd"),
                  float_field("crval1"),
                  float_field("crval2"),
                  fk_field("image_id", "image(id)")])



def create_flat_table():
    """
    The C{flat} table keeps track of which images have been flat fielded and
    where the names of the resulting images.
    """
    create_table("flat", 
                 [pk_field("image_id", "INT"),
                  str_field("flatfile", 25),
                  str_field("outputfile", 50),
                  fk_field("image_id", "image(id)")])


def create_astrom_table():
    """
    The C{astrom} table records the results of running C{AptAstrom} on each
    image.
    """
    create_table("astrom", 
                 [pk_field("image_id", "INT"),
                  type_field("success", "TINYINT"),
                  float_field("smag"),
                  float_field("zmag"),
                  float_field("sky"),
                  fk_field("image_id", "image(id)")])



def create_star_table():
    """
    The C{star} table keeps track of the catalogue stars which are identified by
    AptPhot.
    """
    drop_table("phot")
    create_table("star", 
                 [id_field("star_id", "INT"),
                  int_field("cat_id", True),
                  float_field("ra"),
                  float_field("decl")])
    

def create_phot_table():
    """
    The C{phot} table keeps track of the individual stars which are identified
    in each image by AptPhot.
    """
    create_table("phot", 
                 [int_field("image_id"),
                  int_field("star_id"),
                  float_field("vmag"),
                  float_field("smag"),
                  float_field("mag3"),
                  float_field("mag4"),
                  str_field("err3", 100),
                  str_field("err4", 100),
                  float_field("X"),
                  float_field("Y"),
                  fk_field("star_id", "star(star_id)"),
                  fk_field("image_id", "image(id)"),
                  "KEY (image_id, star_id)"])

def create_starcount_table():
    """
    The C{starcount} table stores the number of stars identified by AptPhot in
    each image.
    """
    create_table("starcount", 
                 [int_field("image_id"),
                  int_field("nstars"),
                  fk_field("image_id", "image(id)")])



def populate_cam_table():
    for cam in ["sbc", "sky"]:
        sql = "insert into cam set name='%s'" % cam
        run_sql(sql)

def add_images(files):
    from util.files import strip_files, strtodatetime
    stripped = strip_files(files)

    for i, (f, s) in enumerate(zip(files, stripped)):
        if not i%1000:
            print i
        date, cam = s.lower().split(".")
        date = strtodatetime(date)
        sql = "insert ignore into image (filename, basename, cam_id, time) " \
              "select '%s', '%s', id, '%s' from cam where name='%s'" % \
              (f, s, date, cam)
        run_sql(sql)
    

def populate_image_table():
    from util.files import getfiles
    files = getfiles("Sky") + getfiles("SBC")
    add_images(files)


def populate_image_07():
    import os
    import os.path
    path = "/mnt/hda/timl/data/fits"
    files = [os.path.join(path, filename) for filename in os.listdir(path)]
    add_images(files)


def clean_zfiles():
    import os
    import os.path
    path = "/mnt/hda/timl/data/fits"
    files = [os.path.join(path, filename) for filename in os.listdir(path)]
    for file in files:
        if ".z" in file:
            new = file.replace(".z", ".")
            os.system("mv %s %s" %  (file, new))
            print new

def init_db():
    """
    Create and populate tables for the cameras and the images
    """
    create_cam_table()
    populate_cam_table()
    create_image_table()
    populate_image_table()


def main():
    """
    WARNING:
    """
    init_db()

    create_unzip_table()
    create_header_table()
    create_imstat_table()
    create_flat_table()
    create_astrom_table()

    create_star_table()
    create_phot_table()
    create_starcount_table()


if __name__ == '__main__':
    #clean_zfiles()
    #populate_image_07()
    #main()

    from util.files import getfiles

    files = getfiles("SBC") + getfiles("Sky")
    add_images(files)
