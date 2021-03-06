"""
Split Pandas DataFrame
"""


def split_df(df, N):
    """
    Split Dataframe making each sub dataframe
    having only N rows
    """
    
    __len = int(df.shape[0])
    
    if __len < N:
        L = [df]
    
    else:
        L= []
        for i in range(0, __len, N):
            if i + N < __len:
                L.append(df.iloc[i:i+N])
            else:
                L.append(df.iloc[i:__len])
    
    return L


def split_df_inN(df, N_new_Df):
    """
    Split df in several dataframe in number equal to N_new_Df
    """
    
    __len = float(df.shape[0])
    
    N = int(round(__len / N_new_Df, 0))
    
    return split_df(df, N)


"""
Splitting with OGR
"""


def splitShp_by_range(shp, nrFeat, outFolder):
    """
    Split one feature class by range
    """
    
    import os
    from gasp.oss       import get_filename, get_fileformat
    from gasp.prop.feat import feat_count
    from gasp.mng.fld   import lst_fld
    from gasp.anls.exct import sel_by_attr
    
    rowsN = feat_count(shp, gisApi='ogr')
    
    nrShp = int(rowsN / float(nrFeat)) + 1 if nrFeat != rowsN else 1
    
    fields = lst_fld(shp)
    
    offset = 0
    exportedShp = []
    for i in range(nrShp):
        outShp = sel_by_attr(
            shp,
            "SELECT {cols}, geometry FROM {t} ORDER BY {cols} LIMIT {l} OFFSET {o}".format(
                t=os.path.splitext(os.path.basename(shp))[0],
                l=str(nrFeat), o=str(offset),
                cols=", ".join(fields)
            ),
            os.path.join(outFolder, "{}_{}{}".format(
                get_filename(shp, forceLower=True), str(i),
                get_fileformat(shp)
            )), api_gis='ogr'
        )
        
        exportedShp.append(outShp)
        offset += nrFeat
    
    return exportedShp


"""
Split Raster
"""


def gdal_split_bands(inRst, outFolder):
    """
    Export all bands of a raster to a new dataset
    
    TODO: this could be done using gdal_translate
    """
    
    from osgeo import gdal
    import numpy; import os
    from gasp.prop.rst import get_nodata
    from gasp.to.rst import array_to_raster
    
    rst = gdal.Open(inRst)
    
    if rst.RasterCount == 1:
        return
    
    nodata = get_nodata(inRst, gisApi='gdal')
    
    for band in range(rst.RasterCount):
        band += 1
        src_band = rst.GetRasterBand(band)
        if src_band is None:
            continue
        else:
            # Convert to array
            array = numpy.array(src_band.ReadAsArray())
            array_to_raster(
                array,
                os.path.join(
                    outFolder,
                    '{r}_{b}.tif'.format(
                        r=os.path.basename(os.path.splitext(inRst)[0]),
                        b=str(band)
                    )
                ),
                inRst,
                None,
                gdal.GDT_Float32, noData=nodata, gisApi='gdal'
            )

"""
Split Excel tables
"""

def split_table_by_number(xlsTable, row_number, output,
                          sheetName=None, sheetIndex=None):
    """
    Split a table by row number
    
    Given a number of rows, this method will split an input table
    in several tables with a number of rows equal to row_number.
    
    TODO: Do it with Pandas
    """
    
    import xlrd;          import xlwt
    from gasp.mng.fld.xls import columns_by_order
    from gasp.fm          import tbl_to_obj
    
    COLUMNS_ORDER = columns_by_order(
        xlsTable, sheet_name=sheetName, sheet_index=sheetIndex
    )
    
    DATA = tbl_to_obj(xlsTable,
        sheet=sheetIndex if sheetIndex else sheetName, output='array'
    )
    
    # Create output
    out_xls = xlwt.Workbook()
    
    l = 1
    s = 1
    base = sheetName if sheetName else 'data'
    for row in DATA:
        if l == 1:
            sheet = out_xls.add_sheet('{}_{}'.format(base, s))
            
            # Write Columns
            for col in range(len(COLUMNS_ORDER)):
                sheet.write(0, col, COLUMNS_ORDER[col])
        
        for col in range(len(COLUMNS_ORDER)):
            sheet.write(l, col, row[COLUMNS_ORDER[col]])
        
        l += 1
        
        if l == row_number + 1:
            l = 1
            s += 1
    
    # Save result
    out_xls.save(output)

