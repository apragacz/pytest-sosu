#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    packages=find_packages(exclude=['tests.*', 'tests']),
    entry_points={"pytest11": ["sosu = pytest_sosu.plugin"]},
)
