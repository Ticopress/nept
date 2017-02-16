#!/usr/bin/env python
import io

from setuptools import find_packages, setup


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

setup(
    name="nept",
    version="0.1.0.dev0",
    author="Emily Irvine",
    author_email="emily.m.irvine.gr@dartmouth.edu",
    packages=find_packages(),
    url="https://github.com/vandermeerlab/nept",
    description="Neuroelectrophysiology tools",
    long_description=read('README.md'),
    install_requires=[
        "numpy",
        "scipy",
        "shapely",
        "matplotlib"
    ],
    setup_requires=["numpy"],
    tests_require=["pytest"],
    extras_require={
        'docs': ["sphinx", "numpydoc", "mock"],
    }
)