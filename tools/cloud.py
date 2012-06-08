"""
Generate LaTeX tables which summarise the cloud cover statistics for a number
of different conditions.
"""

from db.query import query

dates = [("060401", "060501", "April"),
         ("060501", "060601", "May"),
         ("060601", "060701", "June"),
         ("060701", "060801", "July"),
         ("060801", "060901", "August"),
         ("060901", "061001", "September"),
         ("061001", "061101", "October"),
         ("060501", "061101", "May-Oct")]

conditions = ["header.sunzd > 1.69",
              "header.sunzd > 1.69 and header.sunzd < 1.88",
              "header.sunzd > 1.88"]

def has_stars(result):
    stars = result["nstars"]
    return len(stars[stars > 0]), len(stars) 

def good_smag(result):
    smag = result["smag"]
    good = smag[smag < 0.0]
    good = good[good > -1.0]
    return len(good), len(smag)

def both_good(result):
    smag = result["smag"]
    good = result[smag < 0.0]
    smag = good["smag"]
    good = good[smag > -1.0]
    stars = good["nstars"]
    good = good[stars > 0]
    return len(good), len(result)

def make_file(filename, fields, fn):
    
    sss = "\\begin{table}[!hbt]\n\\centering\n\\begin{tabular}{|l|l|l|l|l|}"
    sss += "\hline\n & & $sunzd > 1.69$ & $1.69 < sunzd \\le 1.88$ & $sunzd > 1.88$ \\\\\n\hline\n"
    for d in dates:
        print d
        ss = d[2]
        for exp in [8, 40, None]:
            if exp == None:
                s = " & Any"
            else:
                s = " & " + str(exp)
            
            for condition in conditions:
                condition += " and time(image.time) != '23:48:00'"
                result = query(fields, cam="sky", exp=exp, dates=d[:2], condition=condition)
                a, b = fn(result)
                if b:
                    percentage = 100*float(a)/b
                else:
                    percentage = 0
            
                s += " & %d/%d = %2.1f\\%%" % (a, b, percentage)
            if exp is None:
                s += "\\\\\n\hline\n"
            else:
                s += "\\\\\n\cline{2-5}\n"
            ss += s
        sss += ss
    f = open("/home/timl/thesis/" + filename, "w")
    f.write(sss)
    f.close()
    print sss


def main():
    make_file("cloud-star-table.tex", ["starcount.nstars"], has_stars)
    make_file("cloud-smag-table.tex", ["astrom.smag"], good_smag)
    make_file("cloud-both-table.tex", ["astrom.smag", "starcount.nstars"], both_good)

if __name__ == '__main__':
    main()
