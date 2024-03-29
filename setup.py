import setuptools
import clilib

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='clilib',
    version=clilib.__version__,
    scripts=[],
    entry_points={
        'console_scripts': ["wheel_utils = clilib.util.wheel:cli"]
    },
    author="Gage LeBlanc",
    author_email="gleblanc@symnet.io",
    description="A library for setting up cli applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gageleblanc/clilib",
    packages=setuptools.find_packages(),
    install_requires=['pyyaml'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
