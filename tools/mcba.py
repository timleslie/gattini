"""
Quick and dirty script to provide some number of interest to Michael.
"""

from db.db import run_sql
import numpy as N

if __name__ == '__main__':

    sql = "select header.sunzd, header.moonzd, astrom.sky from header inner join astrom on header.image_id = astrom.image_id inner join image on image.id = header.image_id where header.exposure=40 and image.time > 060401 and image.cam_id = 2"
    run_sql(sql).tofile("sky-40.txt", sep="\n")
    
    sql = "select header.sunzd, header.moonzd, astrom.sky from header inner join astrom on header.image_id = astrom.image_id inner join image on image.id = header.image_id where header.exposure=8 and image.time > 060401 and image.cam_id = 2"
    run_sql(sql).tofile("sky-8.txt", sep="\n")
    
    sql = "select header.sunzd, header.moonzd, astrom.smag from header inner join astrom on header.image_id = astrom.image_id inner join image on image.id = header.image_id where header.exposure=40 and image.time > 060401 and image.cam_id = 2"
    run_sql(sql).tofile("smag-40.txt", sep="\n")
    
    sql = "select header.sunzd, header.moonzd, astrom.smag from header inner join astrom on header.image_id = astrom.image_id inner join image on image.id = header.image_id where header.exposure=8 and image.time > 060401 and image.cam_id = 2"
    run_sql(sql).tofile("smag-8.txt", sep="\n")
    
