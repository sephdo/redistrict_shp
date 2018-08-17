"""from setuptools import setup

setup(
   name='shpConvert',
   version='1.0',
   description="Command-line program that converts CSV and XML exports from Dave's Redistricting App to standard shapefiles.",
   author='Joseph F. Donahue',
   author_email='josephfdonahue@gmail.com',
   packages=['shpConvert'],  #same as name
   install_requires=['shapefile', 'shapely'], #external packages as dependencies
)"""

from setuptools import setup

setup(
    name = 'redistrict_shp',
    version = '1.0',
    packages = ['redistrict_shp'],
    install_requires = ['pyshp','requests','shapely'],
    entry_points = {
        'console_scripts': [
            'redistrict_shp = redistrict_shp.__main__:main'
        ]
    })
