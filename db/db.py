import MySQLdb
import numpy as N


GDB = "test"
""" The Gattini Database (GDB) name. """

def recarray_wrap(data, names):
    if not len(data):
        dt = zip(names, ["i4"]*len(names))
        return N.empty((0,), dtype=dt)
    else:
        return N.rec.array(data, names=names)

def result_to_recarray(cursor):
    desc = cursor.description
    if desc is None:
        return []

    data = list(cursor.fetchall())
    names = [d[0] for d in desc]

    if not data :
        # empty recarray hack
        dt = zip(names, ["i4"]*len(names))
        return N.empty((0,), dtype=dt)

    return recarray_wrap(data, names)

def run_sql(sql, name=GDB):
    db = MySQLdb.connect(db=name)
    cursor = MySQLdb.cursors.Cursor(db)
    cursor.execute(sql)
    db.commit()
    return result_to_recarray(cursor)

def run_sql_single(sql):
    return run_sql(sql)[0][0]


def drop_table(table):
    run_sql("drop table if exists %s" % table)

def create_table(table, fields, engine="InnoDB"):
    drop_table(table)
    sql = "create table %s (%s) ENGINE=%s" % (table, ", ".join(fields), engine)
    run_sql(sql)

def id_field(name, type):
    return pk_field(name, type) + " PRIMARY KEY"

def pk_field(name, type):
    return type_field(name, type, True) + " PRIMARY KEY"

def fk_field(key, ref):
    return "FOREIGN KEY (%s) REFERENCES %s" % (key, ref)

def int_field(name, unique=False):
    return type_field(name, "INT", unique)

def float_field(name, unique=False):
    return type_field(name, "FLOAT", unique)

def str_field(name, length, unique=False):
    return type_field(name, "VARCHAR(%d)" % length, unique)

def type_field(name, type_, unique=False):
    s = "%s %s NOT NULL" % (name, type_)
    if unique:
        s += " UNIQUE"
    return s
