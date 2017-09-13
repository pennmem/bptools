from setuptools import setup, find_packages
from bptools import __version__

with open('README.rst') as f:
    readme = f.read()

setup(
    name='btpools',
    version=__version__,
    packages=find_packages(),
    package_data={
        '': ['*.txt', '*.csv'],
    },
    install_requires=[
        'numpy',
        'pandas',
    ],
    author='Penn Computational Memory Lab',
    description='EEG bipolar montage helpers',
    long_description=readme,
)
