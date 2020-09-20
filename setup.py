import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='clilib',
    version='1.6.1',
    scripts=[],
    author="Gage LeBlanc",
    author_email="gleblanc@symnet.io",
    description="A library for setting up cli applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gageleblanc/clilib",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
