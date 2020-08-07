from setuptools import setup

setup(
    name = 'aprsjson',
    version = '1.0',
    description = 'Module for parsing APRS packet as JSON',
    url = 'https://github.com/josefmtd/aprs-json',
    author = 'Josef Matondang',
    author_email = 'admin@josefmtd.com',
    packages = ['aprsjson'],
    install_requires=['aprs']
)
