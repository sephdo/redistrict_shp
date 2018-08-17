from .config import *

import csv
import datetime
import io
import requests
import shapefile
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import cascaded_union
import os
import xml.etree.ElementTree as etree
import zipfile

class DRFExport(object):
    def __init__(self,infile):
        self.fields = []
        self.precincts = {}
        self.root = etree.parse(infile).getroot()
        self.states = self.root.findall('.//state')
        self.state = self.states[0]
        self.precinctType = "VTD" if self.state.get("useVotingDistricts") == "True" else "BG"
        self.vintage = "2010" if self.state.get("is2010") == "True" else "2000"
        self.districtTypes = set(s.get('kind').upper() for s in self.state.findall('.//scenario'))
        if 'CCD' in self.districtTypes:
            self.districtTypes.remove('CCD')
        self.fips_state = self.state.find(".//voteDist").get("geoID2")[:2]
        self.tigerPath = TIGER_PATHS[self.precinctType+self.vintage].format(fips=self.fips_state)
        self.tigerUrl = TIGER_URLS[self.precinctType+self.vintage].format(fips=self.fips_state)

        self.districtCounts = {districtType:0 for districtType in self.districtTypes}
        self.districtCounts['CCD'] = {}
        self.fips_counties = []
        for voteDist in self.state.findall(".//voteDist"):
            fips = voteDist.get('geoID2')
            self.precincts[fips] = {}
            for districtType in self.districtTypes:
                districtNumber = voteDist.get(districtType.lower())
                self.precincts[fips][districtType] = districtNumber
                if districtNumber and not districtType == 'CCD':
                    self.districtCounts[districtType] = max(self.districtCounts[districtType],int(districtNumber))
            if 'ccd' in voteDist.attrib:
                districtNumber = voteDist.get('ccd')
                if districtNumber:
                    if not fips[:5] in self.fips_counties:
                        self.districtCounts['CCD'][fips[:5]] = int(districtNumber)
                        self.fips_counties.append(fips[:5])
                    else:
                        self.districtCounts['CCD'][fips[:5]] = max(self.districtCounts['CCD'][fips[:5]],int(districtNumber))

class CSVExport(object):
    def __init__(self,infile):
        """
        CSV exports contain population data, but only allow for congressional
        exports.
        """
        self.vintage = "2010"
        self.districtTypes = ["CD"]
        self.precincts = {}
        self.fips_counties = {}
        districtCount = 0
        with open(infile) as f:
            dr = csv.DictReader(f)
            dr.fieldnames = [CSV_MAP[field] for field in dr.fieldnames]
            self.fields = [field for field in dr.fieldnames if not field in CSV_EXCLUDE_FIELDS]
            next(dr) #skip original fieldnames
            for row in dr:
                fips = row['DrfGeoID']
                self.precincts[fips] = {}
                districtCount = max(districtCount,int(row["CD"]))
                for key, value in row.items():
                    if key in POPULATION_FIELDS:
                        self.precincts[fips][key] = int(value) if value else 0
                    else:
                        self.precincts[fips][key] = value
            self.fips_state = fips[:2]
            """
            BG fips codes have 12 chars. VTD fips codes usually have fewer than 12
            chars, excepting special cases (2000 Special VTDs in CA, TX, and NY),
            for which fips codes contain spaces.
            """
            if len(fips)==12 and not " " in fips:
                self.precinctType = "BG"
            else:
                self.precinctType = "VTD"
        self.tigerPath = TIGER_PATHS[self.precinctType+self.vintage].format(fips=self.fips_state)
        self.tigerUrl = TIGER_URLS[self.precinctType+self.vintage].format(fips=self.fips_state)
        self.districtCounts = {"CD":districtCount}

"""
Helper class that manages various fieldsets used in input files, output files,
and calculations. 
"""
class Fields(object):
    def __init__(self,districtType,drf_fields,reader):
        self.reader = [field[0] for field in reader.fields[1:]]
        self.area = [(field,i) for i, field in enumerate(self.reader) if field in AREA_FIELDS]
        self.population = [field for field in drf_fields if field in POPULATION_FIELDS]
        self.output = [districtType] + drf_fields + [field for field, index in self.area]
        self.writer = [(field,'N',18,0) if field in POPULATION_FIELDS + AREA_FIELDS else
                        (field,'C','40',0) for field in self.output]

"""
District class accepts all voting districts or block groups associated with a
district, then produces a new shape that encompasses the entire district.
"""
class District(object):
    def __init__(self,districtType,districtNumber,fields):
        self.fields = fields
        self.precincts = []
        self.values = {districtType:districtNumber}
        for field,index in self.fields.area:
            self.values[field] = 0
        for field in self.fields.population:
            self.values[field] = 0
    def addPrecinct(self,rec,precinct):
        """
        rec.shape.points = a list of latlng coordinates
        
        rec.shape.parts = list of indexes within rec.shape.points
        where separate parts begin.

        len(rec.shape.points) is appended to parts so that the final
        part has an ending index. There may be a more clear way to code this.
        """
        parts = list(rec.shape.parts) + [len(rec.shape.points)]

        """
        Excluded areas of the shape are simply listed as separate parts,
        so we identify these and subtract them from their containing
        part(s). This method also accounts for concentric area exclusions.
        """
        # Iterate forward over the parts list.
        geoms = []
        for i in range(len(rec.shape.parts)):
            poly = Polygon(rec.shape.points[parts[i]:parts[i+1]])
            for i in range(len(geoms)):
                if poly.within(geoms[i]):
                    geoms.append(geoms.pop(i).difference(poly))
                    break
            else:
                geoms.append(poly)

        # Iterate backwards to catch any interiors that precede their
        # containing areas in the parts list.
        geoms_ = []
        while len(geoms) > 0:
            poly = geoms.pop(0)
            for i in range(len(geoms)):
                if poly.within(geoms[i]):
                    geoms.append(geoms.pop(i).difference(poly))
                    break
            else:
                geoms_.append(poly)

        """
        Add all refined geoms_ to self.precincts so that they are included in
        the cascaded union.
        """
        self.precincts.extend(geoms_)

        """
        If DRA has provided population fields, add these to the district
        total.
        """
        for field in self.fields.population:
            self.values[field] += precinct[field]

        # TIGER provides area fields, so add these to the district total.
        for field,index in self.fields.area:
            self.values[field] += rec.record[index]

    # record() and shape() methods resemble shapefile.ShapeRecord object
    def record(self):
        return [self.values[field] for field in self.fields.output]
    
    def shape(self):
        """
        Use shapely's cascaded_union function to merge precincts into a
        single shape.
        """
        union = cascaded_union(MultiPolygon(self.precincts))

        """
        Shapely will return a MultiPolygon or a Polygon, depending on if
        the union has multiple pieces. Extract a coordinate list from the
        union. Following shapefile format, exterior parts are listed before
        interiors.
        """
        parts = []
        if type(union) is Polygon:
            parts.append(list(union.exterior.coords))
            for interior in union.interiors:
                parts.append(list(interior.coords))
        else:
            for geom in union.geoms:
                parts.append(list(geom.exterior.coords))
                for interior in geom.interiors:
                    parts.append(list(interior.coords))
        return parts

def convert(infile,outfile):
    if infile[-3:] == "csv":
        drf = CSVExport(infile)
    elif infile[-3:] == 'drf':
        drf = DRFExport(infile)
    """
    If a local copy of the TIGER precinct shapefile for this state doesn't exist, then
    download it from the US Census FTP site.
    """
    if not os.path.isfile(drf.tigerPath):
        resp = requests.get(drf.tigerUrl,stream=True)
        with open(drf.tigerPath,'wb') as f:
            f.write(resp.content)
    zipshape = zipfile.ZipFile(drf.tigerPath,'r')
    dbfname, prjname, shpname, shpxmlname, shxname = zipshape.namelist()
    r = shapefile.Reader(
        shp=io.BytesIO(zipshape.read(shpname)),
        shx=io.BytesIO(zipshape.read(shxname)),
        dbf=io.BytesIO(zipshape.read(dbfname))
    )
    filename, ext = os.path.splitext(os.path.split(outfile)[-1])
    with zipfile.ZipFile(outfile,'w',zipfile.ZIP_DEFLATED) as z:
        #for scenario in scenarios:
        def exportDistrict(districts,shpfile_name):
            w = shapefile.Writer()
            fields = None
            for district in districts.values():
                if not fields:
                    fields = district.fields
                    w.fields = fields.writer
                w.records.append(district.record())
                w.poly(parts=district.shape())
            shp = io.BytesIO()
            shx = io.BytesIO()
            dbf = io.BytesIO()
            prj = zipshape.read(prjname)
            w.saveShp(shp)
            w.saveShx(shx)
            w.saveDbf(dbf)
            z.writestr("{}.shp".format(shpfile_name), shp.getvalue())
            z.writestr("{}.shx".format(shpfile_name), shx.getvalue())
            z.writestr("{}.dbf".format(shpfile_name), dbf.getvalue())
            z.writestr("{}.prj".format(shpfile_name), prj)

        statewide = {}
        counties = {}
        for districtType in drf.districtTypes:
            count = drf.districtCounts[districtType]
            fields = Fields(districtType,drf.fields,r)
            statewide[districtType] = {str(n):District(districtType,str(n),fields) for n in range(count+1)}
        for fips_county in drf.fips_counties:
            count = drf.districtCounts['CCD'][fips_county]
            fields = Fields('CCD',drf.fields,r)
            counties[fips_county] = {str(n):District("CCD",str(n),fields) for n in range(count+1)}

        for rec in r.shapeRecords():
            precinctNumber = rec.record[3 if drf.precinctType == 'VTD' else 4]
            if precinctNumber in drf.precincts:
                precinct = drf.precincts[precinctNumber]
                if precinctNumber[:5] in drf.fips_counties:
                    counties[precinctNumber[:5]][precinct['CCD']].addPrecinct(rec,precinct)
                for districtType, districts in statewide.items():
                    districts[precinct[districtType]].addPrecinct(rec,precinct)

        for districtType, districts in statewide.items():
            exportDistrict(districts,"{}_{}".format(filename,districtType))
        for fips_county, districts in counties.items():
            exportDistrict(districts,"{}_{}_{}".format(filename,'CCD',fips_county))
