import numpy
import os
from osgeo        import gdal
from osgeo        import osr
from gasp.prop.ff import drv_name

def mapcalc(expression, exp_val_paths, outRaster, epsg, outNodata=-99999):
    """
    GDAL Raster Calculator
    
    TODO: Check if rasters dimensions are equal
    """
    
    from py_expression_eval import Parser
    from gasp.prop.rst import rst_dataType
    
    parser = Parser()
    
    EXPRESSION = parser.parse(expression)
    
    evalValue = {}
    noDatas   = {}
    rstTypes  = []
    c = 0
    for x in EXPRESSION.variables():
        img = gdal.Open(exp_val_paths[x])
        arr = numpy.array(img.ReadAsArray())
        
        band = img.GetRasterBand(1)
        no_value = band.GetNoDataValue()
        
        if not c:
            template = img
            c+=1
        
        evalValue[x] = arr
        noDatas[x]   = no_value
        rstTypes.append(rst_dataType(band))
    
    result = EXPRESSION.evaluate(evalValue)
    
    for v in noDatas:
        numpy.place(result, evalValue[v]==noDatas[v], outNodata)
        
    if gdal.GDT_Float64 in rstTypes:
        resultType = gdal.GDT_Float64
    else:
        if gdal.GDT_Float32 in rstTypes:
            resultType = gdal.GDT_Float32
        else:
            if gdal.GDT_UInt32:
                resultType = gdal.GDT_UInt32
            else:
                if gdal.GDT_UInt16:
                    resultType = gdal.GDT_UInt16
                else:
                    if gdal.GDT_Int32:
                        resultType = gdal.GDT_Int32
                    else:
                        if gdal.GDT_Int16:
                            resultType = gdal.GDT_Int16
                        else:
                            resultType = gdal.GDT_Byte
    
    # Write output
    geo_transform = template.GetGeoTransform()
    rows, cols = result.shape
    
    driver = gdal.GetDriverByName(drv_name(outRaster))
    out    = driver.Create(outRaster, cols, rows, 1, resultType)
    out.SetGeoTransform(geo_transform)
    
    outBand = out.GetRasterBand(1)
    
    outBand.SetNoDataValue(outNodata)
    outBand.WriteArray(result)
    
    outRstSRS = osr.SpatialReference()
    
    outRstSRS.ImportFromEPSG(epsg)
    out.SetProjection(outRstSRS.ExportToWkt())
    
    outBand.FlushCache()
    
    return outRaster
