"""Package Setup for scikit-sequitur

Build binary extension in-place for testing with:

    $ python setup.py build_ext --inplace

Create annotations for optimization:

    $ cython -3 -a sksequitur/core.py
    $ python3 -m http.server
    # Open sksequitur/core.html in browser.

"""

from setuptools import Extension, setup
from setuptools.command.test import test as TestCommand

import sksequitur


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox

        errno = tox.cmdline(self.test_args)
        exit(errno)


with open("README.rst") as reader:
    readme = reader.read()

args = dict(
    name="scikit-sequitur",
    version=sksequitur.__version__,
    description="Sequitur algorithm for inferring hierarchies",
    long_description=readme,
    author="Grant Jenks",
    author_email="contact@grantjenks.com",
    url="http://www.grantjenks.com/docs/scikit-sequitur/",
    license="Apache 2.0",
    packages=["sksequitur"],
    tests_require=["tox"],
    cmdclass={"test": Tox},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)

try:
    from Cython.Build import cythonize

    ext_modules = [Extension("sksequitur._core", ["sksequitur/core.py"])]
    setup(
        ext_modules=cythonize(ext_modules, language_level="3"),
        **args,
    )
except Exception as exception:
    print("*" * 79)
    print(exception)
    print("*" * 79)
    print("Failed to setup sksequitur with Cython. See error message above.")
    print("Falling back to pure-Python implementation.")
    print("*" * 79)
    setup(**args)
