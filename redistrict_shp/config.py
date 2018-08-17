import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR,'assets')
TIGER_PATHS = {
    'VTD2010':os.path.join(BASE_DIR,'TIGER','VTD','tl_2012_{fips}_vtd10.zip'),
    'BG2010':os.path.join(BASE_DIR,'TIGER','BG','tl_2012_{fips}_bg.zip'),
    'BG2000':os.path.join(BASE_DIR,'TIGER','BG','tl_2010_{fips}_bg00.zip'),
    }

"""
URLs are for the US Census's FTP site. VTD files for the 2000 census are not
available statewide, just for individual counties.
"""

TIGER_URLS = {
    'VTD2010':"https://www2.census.gov/geo/tiger/TIGER2012/VTD/tl_2012_{fips}_vtd10.zip",
    #'VTD2000':"https://www2.census.gov/geo/tiger/TIGER2010/VTD/2000/tl_2010_{fips}_vtd00.zip",
    'BG2010':"https://www2.census.gov/geo/tiger/TIGER2012/BG/tl_2012_{fips}_bg.zip",
    'BG2000':"https://www2.census.gov/geo/tiger/TIGER2010/BG/2000/tl_2010_{fips}_bg00.zip",
    }
"""
Shapefile fieldnames (exported into the .dbf file) are limited to 10
characters. CSV_FIELDMAP provides alternative fieldnames for population
fields included in CSV exports.
"""
CSV_MAP = {
    'GeoID2':'DrfGeoID',
    'District':'CD',
    'Name':'Name',
    'County':'County',
    'Total Population':'Population',
    'Total Population 18+':'Population18+',
    'White (NH)':'White',
    'White 18+ (NH)':'White18+',
    'Black (NH)':'Black',
    'Black 18+ (NH)':'Black18+',
    'Hispanic':'Hispanic',
    'Hispanic 18+':'Hispanic18+',
    ' Asian and Pacific Islander (NH)':'AAPI',
    'Asian and Pacific Islander 18+ (NH)':'AAPI18+',
    'Native American (NH)':'Native',
    'Native American 18+ (NH)':'Native18+',
    'Other (NH)':'Other',
    'Other 18+ (NH)':'Other18+',
    'Pres08 Total Vote':'Pres08Total',
    'Pres08 Dem Vote':'Pres08Dem',
    'Pres08 Rep Vote':'Pres08Rep',
    'Avg Dem Vote':'AvgVoteDem',
    'Avg Rep Vote':'AvgVoteRep',    
    }
"""
INT_FIELDS and AREA_FIELDS will be added when VTD or BG data is compiled
into a larger district.
CSV_EXCLUDE_FIELDS, apart from the district number, can't be compiled.
"""
CSV_EXCLUDE_FIELDS = ['DrfGeoID','CD','Name','County']
POPULATION_FIELDS = [field for field in CSV_MAP.values() if not field in CSV_EXCLUDE_FIELDS]
AREA_FIELDS = ['ALAND10','AWATER10','ALAND00','AWATER00']
