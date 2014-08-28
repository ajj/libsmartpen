#!/usr/bin/env python3

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
if __name__ == "__main__":
    extensions = [ 
        Extension("pysmartpen", ["pysmartpen.pyx"], libraries = ["smartpen"],
                  library_dirs=["."])
        ]
    setup(
      version = "0.6",
      author = "Steven Walter",
      author_email = "stevenrwalter@gmail.com",
      url = "https://github.com/srwalter/libsmartpen/",
      license = "GPLv2",
      name = "pysmartpen",
      py_modules=["parsestf"],
      ext_modules=cythonize(extensions),
    )
