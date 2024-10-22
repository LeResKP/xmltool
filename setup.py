from setuptools import find_packages, setup

# Hack to prevent TypeError: 'NoneType' object is not callable error
# on exit of python setup.py test
try:
    import multiprocessing
except ImportError:
    pass

version = "1.1.0"

setup(
    name="xmltool",
    version=version,
    description="Tool to manipulate XML files",
    long_description=open("README.rst").read().split("Build Status")[0],
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: JavaScript",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    keywords="",
    author="Aurélien Matouillot",
    author_email="a.matouillot@gmail.com",
    url="http://xmltool.lereskp.fr/",
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "tests", "tests.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "lxml",
        "requests",
        "dogpile.cache",
    ],
    tests_require=[
        "pytest",
        "mock",
    ],
    entry_points="""
      # -*- Entry points: -*-
      """,
)
