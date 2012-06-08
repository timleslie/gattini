from pylab import log10

apt_phot_d = {"sbc": ("tycho", 20),
              "sky": ("tycho", 6)}

apt_phot_keys = ["RA", "Dec", "Vmag", "Vmag", "ID", "X", "Y", "smag", \
                 "mag3", "mag4", "err3", "err4"]



def foo():
    outfile="phot.txt"
    image_id = 37
    f = open(outfile)
    n = 0
    for line in f:
        vals = line.split()
        for i in range(len(vals)):
            if vals[i] == 'INDEF':
                vals[i] = '1e-40' #HACK. how to get an Nan in mysql?
        d = dict(zip(apt_phot_keys, vals))

        #sql = "INSERT IGNORE INTO star (cat_id, ra, decl) VALUES( %(ID)s, %(RA)s, %(Dec)s)" % d
        #run_sql(sql)
        #print sql
        
        sql = "INSERT INTO phot SELECT " + str(image_id)
        sql += (", star_id, %(Vmag)s, %(smag)s, %(mag3)s, %(mag4)s, '%(err3)s', '%(err4)s', %(X)s, %(Y)s from star where cat_id = %(ID)s" % d)


        print d["Vmag"], d["mag3"]

        #run_sql(sql)
        #print sql
        n += 1
    sql = "INSERT IGNORE INTO starcount values (%d, %d)" % (image_id, n)
    #run_sql(sql)
    #print sql


#foo()
def main():
    Z = 17.4
    pix_size = 11.3
    pix_mag = 2.5*log10(pix_size**2) 
    sky = 148
    offset = 68        
    print -2.5*log10(sky - offset) + Z  + pix_mag
