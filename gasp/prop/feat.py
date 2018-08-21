# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Feature Classes Properties
"""

def feat_count(shp, gisApi='pandas'):
    """
    Count the number of features in a feature class
    
    API'S Available:
    * gdal;
    * arcpy;
    * pygrass;
    * pandas;
    """
    
    if gisApi == 'ogr':
        from osgeo        import ogr
        from gasp.prop.ff import drv_name
    
        data = ogr.GetDriverByName(drv_name(shp)).Open(shp, 0)
        lyr = data.GetLayer()
        fcnt = int(lyr.GetFeatureCount())
        data.Destroy()
    
    elif gisApi == 'arcpy':
        import arcpy
        
        fcnt = int(arcpy.GetCount_management(lyr).getOutput(0))
    
    elif gisApi == 'pygrass':
        from grass.pygrass.vector import VectorTopo
        
        open_shp = VectorTopo(shp)
        open_shp.open(mode='r')
        fcnt = open_shp.num_primitive_of(geom)
    
    elif gisApi == 'pandas':
        from gasp.fm.shp import shp_to_df
        
        gdf = shp_to_df(shp)
        
        fcnt = int(gdf.shape[0])
        
        del gdf
    
    else:
        raise ValueError('The api {} is not available'.format(gisApi))
    
    return fcnt


def get_geom_type(shp, name=True, py_cls=None, geomCol="geometry",
                  gisApi='pandas'):
    """
    Return the Geometry Type of one Feature Class or GeoDataFrame
    
    API'S Available:
    * ogr;
    * pandas;
    """
    
    if gisApi == 'pandas':
        from pandas import DataFrame
        
        if not isinstance(shp, DataFrame):
            from gasp.fm.shp import shp_to_df
            
            gdf     = shp_to_df(shp)
            geomCol = "geometry"
        
        else:
            gdf = shp
        
        g = gdf[geomCol].geom_type.unique()
        
        if len(g) == 1:
            return g[0]
        
        elif len(g) == 0:
            raise ValueError(
                "It was not possible to identify geometry type"
            )
        
        else:
            for i in g:
                if i.startswith('Multi'):
                    return i
    
    elif gisApi == 'ogr':
        from osgeo        import ogr
        from gasp.prop.ff import drv_name
        
        def geom_types():
            return {
                "POINT"           : ogr.wkbPoint,
                "MULTIPOINT"      : ogr.wkbMultiPoint,
                "LINESTRING"      : ogr.wkbLineString,
                "MULTILINESTRING" : ogr.wkbMultiLineString,
                "POLYGON"         : ogr.wkbPolygon,
                "MULTIPOLYGON"    : ogr.wkbMultiPolygon
            }
        
        d = ogr.GetDriverByName(drv_name(shp)).Open(shp, 0)
        l = d.GetLayer()
        
        geomTypes = []
        for f in l:
            g = f.GetGeometryRef()
            n = str(g.GetGeometryName())
            
            if n not in geomTypes:
                geomTypes.append(n)
        
        if len(geomTypes) == 1:
            n = geomTypes[0]
        
        elif len(geomTypes) == 2:
            for i in range(len(geomTypes)):
                if geomTypes[i].startswith('MULTI'):
                    n = geomTypes[i]
        
        else:
            n = None
        
        d.Destroy()
        del l
        
        return {n: geom_types()[n]} if name and py_cls else n \
                if name and not py_cls else geom_types()[n] \
                if not name and py_cls else None
    
    else:
        raise ValueError('The api {} is not available'.format(gisApi))