"""
Investigate the proportion of images on which C{AptAstrom} was successful as a
function of sun zenith distance.
"""

from db.db import run_sql_single

import numpy as N
from pylab import plot, show


def f(cam):
    hit = []
    miss = []
    x = N.arange(0.95, 2.23, 0.02)
    for sunzd in x:
        
        
        sql = "select count(*) from header inner join astrom on header.image_id=astrom.image_id inner join image on image.id = header.image_id where header.sunzd > %f and astrom.success=1 and image.cam_id = %d" % (sunzd, cam)
        hit.append(run_sql_single(sql))
        
        sql = "select count(*) from header inner join astrom on header.image_id=astrom.image_id inner join image on image.id = header.image_id where header.sunzd > %f and astrom.success=0 and image.cam_id = %d" % (sunzd, cam)
        miss.append(run_sql_single(sql))
        
        print sunzd, float(hit[-1])/ miss[-1]
        
    
    plot(x, N.array(hit, dtype=float)/N.array(miss))

if __name__ == '__main__':
    f(1)
    f(2)
    
    show()
     
