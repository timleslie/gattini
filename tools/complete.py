"""
Unpacks and preprocesses all of the data from the tarball of partial data,
which includes the flats and dark frames.
"""

import tools.unpack
import util.files
import util.dark
import util.flat

def main():
    tools.unpack.main()
    util.files.main()
    util.dark.main()
    util.flat.main()


if __name__ == '__main__':
    main()
