#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import pathlib

from setuptools import find_packages, setup

root_dir = pathlib.Path(__file__).parent


def read(*names, **kwargs):
    with open(root_dir.joinpath(*names), "r") as fh:
        return fh.read()


setup(
    name="openzim_uploader",
    version="1.3",
    summary="SCP/SFTP helper for openZIM uploads to our dropbox",
    description="SCP/SFTP helper for openZIM uploads to our dropbox",
    long_description=read("README.md"),
    long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    author="kiwix",
    author_email="reg@kiwix.org",
    url="https://github.com/openzim/zimfarm/tree/master/uploader",
    keywords="scp sftp upload kiwix",
    license="GPLv3+",
    packages=find_packages(),
    zip_safe=True,
    install_requires=[
        line.strip()
        for line in read("requirements.txt").splitlines()
        if not line.strip().startswith("#")
    ],
    extras_require={
        "all": ["humanfriendly==10.0"],
    },
    entry_points={
        "console_scripts": [
            "openzim-uploader=openzim_uploader:main",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    ],
    python_requires=">=3.13,<3.14",
)
