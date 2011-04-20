import distutils
from distutils.core import setup, Extension

setup(name = "cfstring-typemaps-example",
      version = "1.0",
      ext_modules = [Extension("_example",
                               ["example.i","example.c"],
                               extra_link_args=['-framework','CoreFoundation'])])
