import MySQLdb
from db import run_sql, run_sql_single

def _uniq(lst):
    return dict(zip(lst, lst)).keys()

def _make_id(table):
    if table == "image":
        return "image.id"
    else:
        return table + ".image_id"
    
def _join_tables(tables):
    tables = _uniq(tables)
    table = tables[0]
    left = _make_id(tables[0])
    for t in tables[1:]:
        right = _make_id(t)
        if t == "cam":
            l = "image.cam_id"
            r = "cam.id"
        else:
            l = left
            r = right
        s = " inner join %s on %s = %s" % (t, l, r)
        table += s
    return table

def _filter(cam=None, dates=None, exp=None, has_stars=None, image_id=None, star_id=None):
    tables = []
    conditions = []

    if cam or dates or exp:
        tables.append("image")

    if cam:
        tables.append("cam")
        conditions.append("cam.name = '%s'" % cam)

    if dates:
        frm, to = dates
        conditions.append("image.time > '%s' and image.time < '%s'" % (frm, to))

    if exp:
        conditions.append("header.exposure = %d" % exp)
        tables.append("header")

    if has_stars is not None:
        conditions.append("astrom.success = %d" % int(has_stars))
        tables.append("astrom")

    if image_id:
        conditions = ["image.id = %d" % image_id] + conditions

    if star_id:
        conditions = ["phot.star_id = %d" % star_id] + conditions

    return conditions, tables

def _table_from_condition(cond):
    cond = cond.split(".")[0]
    if "(" in cond:
        cond = cond.split("(")[1]
    return cond

def query(fields, cam=None, dates=None, exp=None, condition=None, has_stars=None, image_id=None, star_id=None):

    fields = _uniq(fields)

    if condition is None:
        condition = []
    elif type(condition) == str:
        condition = condition.split(" and ")

    conditions, tables = _filter(cam, dates, exp, has_stars, image_id, star_id)

    conditions =  conditions + condition

    tables += [field.split(".")[0] for field in fields]
    tables += [_table_from_condition(cond) for cond in conditions]
    tables = [t.strip() for t in tables]
    table = _join_tables(tables)
        
    fields = ", ".join(fields)

    if conditions == []:
        condition = "1"
    else:
        condition = " and ".join(conditions)

    sql = "select %s from %s where %s" % (fields, table, condition)

    return run_sql(sql)



def count(table):
    sql = "select count(*) from %s" % table
    return run_sql_single(sql)

def get_phot_data(star, keys, clauses=None):
    format = ", ".join(["%s"]*len(keys))

    sql = ("SELECT %s from phot where id=%d" % (format, star)) % keys
    if clauses:
        sql += " and " + " and ".join(clauses)

    return run_sql(sql)

def get_star_ids():
    db = MySQLdb.connect(db=GDB)
    d_cursor = MySQLdb.cursors.DictCursor(db)

    sql = "SELECT star_id from star"
    d_cursor.execute(sql)
    results = d_cursor.fetchallDict()
    return [int(res["star_id"]) for res in results]


per_image_fields = ["image.time", "astrom.sky", "astrom.smag", "astrom.zmag",
                    "header.ra", "header.decl", 
                    "header.crval1", "header.crval2", "header.lst",
                    "header.moondist", "header.moonmag", "header.moonphase",
                    "header.moonzd", "header.sunzd", "header.temp",
                    "header.exposure",
                    "imstat.max", "imstat.mean", "imstat.min", "imstat.stddev",
                    "starcount.nstars"]

per_star_fields = ["phot.X", "phot.Y", "phot.vmag", "phot.smag", "phot.mag3",
                  "phot.mag4", "phot.err3", "phot.err4"]

        
