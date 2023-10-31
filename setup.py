#!/usr/bin/env python3

import setuptools
import re

with open("telemongo/__init__.py", encoding="utf-8") as f:
    version = re.search(r"^__version__[\s\t=]*[\"']*([\w\d.\-_+]+)[\"']*$",
                        f.read(), re.M).group(1)

package_name = "telemongo"

setuptools.setup(
    name=package_name,
    packages=[package_name],
    version=version,

    url="https://github.com/watzon/telethon-session-mongo",
    download_url="https://github.com/watzon/telethon-session-mongo/releases",

    author="Chris Watson",
    author_email="cawatson1993@gmail.com",

    description="MongoDB backend for Telethon session storage",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",

    license="MIT",

    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="telegram session sessions mongo mongodb",
    python_requires="~=3.7",

    install_requires=[
        "mongoengine>=0.19.1",
        "telethon>=1.11.3"
    ],
)
