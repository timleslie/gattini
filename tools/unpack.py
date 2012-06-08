"""
Unpack the preliminary Gattini data from the available tarballs.
"""

import os

def main():
    os.system("cd /home/timl; pwd; tar zxvf /home/timl/all_data.tar.gz")
    os.system("cd /home/timl/data; pwd; tar xvf /home/timl/data/sbc_dark.tar")
    os.system("cd /home/timl/data; pwd; tar xvf /home/timl/data/sky_dark.tar")
    os.system("cd /home/timl/data; pwd; tar xvf /home/timl/data/sbc_flats.tar")
    os.system("cd /home/timl/data; pwd; tar xvf /home/timl/data/sky_flats.tar")
    os.system("cd /home/timl/data; pwd; tar zxvf /home/timl/data/06fits.tar.gz")

if __name__ == '__main__':
    main()
