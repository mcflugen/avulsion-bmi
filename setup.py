#! /usr/bin/env python
from setuptools import setup, find_packages


setup(
    name="rafem",
    version="0.1.0",
    author="Katherine Ratliff",
    author_email="k.ratliff@duke.edu",
    description="River Avulsion Flooplain Evolution Model",
    long_description=open("README.rst").read(),
    url="https://github.com/katmratliff/avulsion-bmi",
    license="MIT",
    packages=find_packages(),
)
