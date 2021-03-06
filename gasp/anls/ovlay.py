# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Data analysis By Overlay Tools
"""

def clip(inFeat, clipFeat, outFeat, api_gis="grass"):
    """
    Clip Analysis
    
    api_gis Options:
    * grass
    * grass_cmd
    """
    
    if api_gis == "grass":
        from grass.pygrass.modules import Module
        
        vclip = Module(
            "v.clip", input=inFeat, clip=clipFeat,
            output=outFeat, overwrite=True, run_=False, quiet=True
        )
        
        vclip()
    
    elif api_gis == "grass_cmd":
        from gasp import exec_cmd
        
        rcmd = exec_cmd(
            "v.clip input={} clip={} output={} --overwrite --quiet".format(
                inFeat, clipFeat, outFeat
            )
        )
    
    else:
        raise ValueError("{} is not available!".format(api_gis))
    
    return outFeat


def clip_shp_by_listshp(inShp, clipLst, outLst):
    """
    Clip shapes using as clipFeatures all SHP in clipShp
    Uses a very fast process with a parallel procedures approach
    
    For now, only works with GRASS GIS
    
    Not Working nice with v.clip because of the database
    """
    
    """
    import copy
    from grass.pygrass.modules import Module, ParallelModuleQueue
    
    op_list = []
    
    clipMod = Module(
        "v.clip", input=inShp, overwrite=True, run_=False, quiet=True
    )
    qq = ParallelModuleQueue(nprocs=5)
    
    for i in range(len(clipLst)):
        new_clip = copy.deepcopy(clipMod)
        
        op_list.append(new_clip)
        
        m = new_clip(clip=clipLst[i], output=outLst[i])
        
        qq.put(m)
    qq.wait()
    """
    
    o = [clip(
        inShp, clipLst[i], outLst[i], api_gis="grass_cmd"
    ) for i in range(len(clipLst))]
    
    return outLst


def union(lyrA, lyrB, outShp, api_gis="arcpy"):
    """
    Calculates the geometric union of the overlayed polygon layers, i.e.
    the intersection plus the symmetrical difference of layers A and B.
    
    API's Available:
    * arcpy;
    * saga;
    * grass_cmd;
    * grass_cmd;
    """
    
    if api_gis == "arcpy":
        import arcpy
        
        if type(lyrB) == list:
            lst = [lyrA] + lyrB
        else:
            lst = [lyrA, lyrB]
        
        arcpy.Union_analysis(";".join(lst), outShp, "ALL", "", "GAPS")
    
    elif api_gis == "saga":
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "saga_cmd shapes_polygons 17 -A {} -B {} -RESULT {} -SPLIT 1"
        ).format(lyrA, lyrB, outShp))
    
    elif api_gis == "grass":
        from grass.pygrass.modules import Module
        
        un = Module(
            "v.overlay", ainput=lyrA, atype="area",
            binput=lyrB, btype="area", operator="or",
            output=outShp, overwrite=True, run_=False, quiet=True
        )
        
        un()
    
    elif api_gis == "grass_cmd":
        from gasp import exec_cmd
        
        outcmd = exec_cmd((
            "v.overlay ainput={} atype=area binput={} btype=area "
            "operator=or output={} --overwrite --quiet"
        ).format(lyrA, lyrB, outShp))
    
    else:
        raise ValueError("{} is not available!".format(api_gis))
    
    return outShp


def union_for_all_pairs(inputList):
    """
    Calculates the geometric union of the overlayed polygon layers 
    for all pairs in inputList
    
    THis is not a good idea! It is only an example!
    """
    
    import copy
    from grass.pygrass.modules import Module, ParallelModuleQueue
    
    op_list = []
    
    unionTool = Module(
        "v.overlay", atype="area", btype="area", operator="or",
        overwrite=True, run_=False, quiet=True
    )
    
    qq = ParallelModuleQueue(nprocs=5)
    outputs = []
    for lyr_a, lyr_b in inputList:
        new_union = copy.deepcopy(unionTool)
        op_list.append(new_union)
        
        un_result = "{}_{}".format(lyr_a, lyr_b)
        nu = new_union(
            ainput=lyr_a, binput=lyr_b, ouput=un_result
        )
        
        qq.put(nu)
        outputs.append(un_result)
    
    qq.wait()
    
    return outputs


def optimized_union_anls(lyr_a, lyr_b, outShp, ref_boundary, epsg,
                         workspace=None, multiProcess=None):
    """
    Optimized Union Analysis
    
    Goal: optimize v.overlay performance for Union operations
    """
    
    import os
    from gasp.oss        import get_filename
    from gasp.mng.sample import create_fishnet
    from gasp.mng.feat   import eachfeat_to_newshp
    from gasp.mng.gen    import merge_feat
    from gasp.session    import run_grass
    from gasp.anls.exct  import split_shp_by_attr
    
    if workspace:
        if not os.path.exists(workspace):
            from gasp.oss.ops import create_folder
            
            create_folder(workspace, overwrite=True)
    
    else:
        from gasp.oss.ops import create_folder
        
        workspace = create_folder(os.path.join(
            os.path.dirname(outShp), "union_work"))
    
    # Create Fishnet
    gridShp = create_fishnet(
        ref_boundary, os.path.join(workspace, 'ref_grid.shp'),
        rowN=4, colN=4
    )
    
    # Split Fishnet in several files
    cellsShp = eachfeat_to_newshp(gridShp, workspace, epsg=epsg)
    
    if not multiProcess:
        # INIT GRASS GIS Session
        grsbase = run_grass(workspace, location="grs_loc", srs=ref_boundary)
        
        import grass.script.setup as gsetup
        
        gsetup.init(grsbase, workspace, "grs_loc", 'PERMANENT')
        
        # Add data to GRASS GIS
        from gasp.to.shp.grs import shp_to_grs
        cellsShp   = [shp_to_grs(
            shp, get_filename(shp), asCMD=True
        ) for shp in cellsShp]
        
        LYR_A = shp_to_grs(lyr_a, get_filename(lyr_a), asCMD=True)
        LYR_B = shp_to_grs(lyr_b, get_filename(lyr_b), asCMD=True)
        
        # Clip Layers A and B for each CELL in fishnet
        LYRS_A = [clip(
            LYR_A, cellsShp[x], LYR_A + "_" + str(x), api_gis="grass_cmd"
        ) for x in range(len(cellsShp))]; LYRS_B = [clip(
            LYR_B, cellsShp[x], LYR_B + "_" + str(x), api_gis="grass_cmd"
        ) for x in range(len(cellsShp))]
        
        # Union SHPS
        UNION_SHP = [union(
            LYRS_A[i], LYRS_B[i], "un_{}".format(i), api_gis="grass_cmd"
        ) for i in range(len(cellsShp))]
        
        # Export Data
        from gasp.to.shp.grs import grs_to_shp
        _UNION_SHP = [grs_to_shp(
            shp, os.path.join(workspace, shp + ".shp"), "area"
        ) for shp in UNION_SHP]
    
    else:
        def clip_and_union(la, lb, cell, work, ref, proc, output):
            # Start GRASS GIS Session
            grsbase = run_grass(work, location="proc_" + str(proc), srs=ref)
            import grass.script.setup as gsetup
            gsetup.init(grsbase, work, "proc_" + str(proc), 'PERMANENT')
            
            # Import GRASS GIS modules
            from gasp.to.shp.grs import shp_to_grs
            from gasp.to.shp.grs import grs_to_shp
            
            # Add data to GRASS
            a = shp_to_grs(la, get_filename(la), asCMD=True)
            b = shp_to_grs(lb, get_filename(lb), asCMD=True)
            c = shp_to_grs(cell, get_filename(cell), asCMD=True)
            
            # Clip
            a_clip = clip(a, c, "{}_clip".format(a), api_gis="grass_cmd")
            b_clip = clip(b, c, "{}_clip".format(b), api_gis="grass_cmd")
            
            # Union
            u_shp = union(a_clip, b_clip, "un_{}".format(c), api_gis="grass_cmd")
            
            # Export
            o = grs_to_shp(u_shp, output, "area")
        
        import multiprocessing
        
        thrds = [multiprocessing.Process(
            target=clip_and_union, name="th-{}".format(i), args=(
                lyr_a, lyr_b, cellsShp[i],
                os.path.join(workspace, "th_{}".format(i)), ref_boundary, i,
                os.path.join(workspace, "uniao_{}.shp".format(i))
            )
        ) for i in range(len(cellsShp))]
        
        for t in thrds:
            t.start()
        
        for t in thrds:
            t.join()
        
        _UNION_SHP = [os.path.join(
            workspace, "uniao_{}.shp".format(i)
        ) for i in range(len(cellsShp))]
    
    # Merge all union into the same layer
    MERGED_SHP = merge_feat(_UNION_SHP, outShp, api="ogr2ogr")
    
    return outShp


def intersection(inShp, intersectShp, outShp, api='geopandas'):
    """
    Intersection between ESRI Shapefile
    
    'API's Available:
    * geopandas
    * saga;
    * pygrass
    """
    
    if api == 'geopandas':
        import geopandas
    
        from gasp.fm     import tbl_to_obj
        from gasp.to.shp import df_to_shp
    
        dfShp       = tbl_to_obj(inShp)
        dfIntersect = tbl_to_obj(intersectShp)
    
        res_interse = geopandas.overlay(dfShp, dfIntersect, how='intersection')
    
        df_to_shp(res_interse, outShp)
    
    elif api == 'saga':
        from gasp import exec_cmd
        
        cmdout = exec_cmd((
            "saga_cmd shapes_polygons 14 -A {} -B {} -RESULT {} -SPLIT 1"
        ).format(inShp, intersectShp, outShp))
    
    elif api == 'pygrass':
        from grass.pygrass.modules import Module
        
        clip = Module(
            "v.overlay", ainput=inShp, atype="area",
            binput=intersectShp, btype="area", operator="and",
            output=outShp,  overwrite=True, run_=False, quiet=True
        )
        
        clip()
        
    else:
        raise ValueError("{} is not available!".format(api))
    
    return outShp


def self_intersection(polygons, output):
    """
    Create a result with the self intersections
    """
    
    from gasp import exec_cmd
    
    cmd = (
        'saga_cmd shapes_polygons 12 -POLYGONS {in_poly} -INTERSECT '
        '{out}'
    ).format(in_poly=polygons, out=output)
    
    outcmd = exec_cmd(cmd)
    
    return output


def check_shape_diff(SHAPES_TO_COMPARE, OUT_FOLDER, REPORT, conPARAM, DB, SRS_CODE,
                     GIS_SOFTWARE="GRASS", GRASS_REGION_TEMPLATE=None):
    """
    Script to check differences between pairs of Feature Classes
    
    Suponha que temos diversas Feature Classes (FC) e que cada uma delas
    possui um determinado atributo; imagine também que,
    considerando todos os pares possíveis entre estas FC,
    se pretende comparar as diferenças na distribuição dos valores
    desse atributo em cada par.
    
    * Dependências:
    - ArcGIS;
    - GRASS;
    - PostgreSQL;
    - PostGIS.
    
    * GIS_SOFTWARE Options:
    - ARCGIS;
    - GRASS.
    """
    
    import datetime
    import os;             import pandas
    from gasp.fm.sql       import query_to_df
    from gasp.sql.mng.tbl  import tbls_to_tbl
    from gasp.sql.mng.geom import fix_geom, check_geomtype_in_table
    from gasp.sql.mng.geom import select_main_geom_type
    from gasp.sql.mng.qw   import ntbl_by_query
    from gasp.prop.ff      import check_isRaster
    from gasp.oss          import get_filename
    from gasp.sql.mng.db   import create_db
    from gasp.to.sql       import shp_to_psql, df_to_db
    from gasp.to.shp       import rst_to_polyg
    from gasp.to.shp       import shp_to_shp, psql_to_shp
    from gasp.to           import db_to_tbl
    
    # Check if folder exists, if not create it
    if not os.path.exists(OUT_FOLDER):
        from gasp.oss.ops import create_folder
        create_folder(OUT_FOLDER, overwrite=None)
    else:
        raise ValueError('{} already exists!'.format(OUT_FOLDER))
    
    # Start GRASS GIS Session if GIS_SOFTWARE == GRASS
    if GIS_SOFTWARE == "GRASS":
        if not GRASS_REGION_TEMPLATE:
            raise ValueError(
                'To use GRASS GIS you need to specify GRASS_REGION_TEMPLATE'
            )
        
        from gasp.session import run_grass
        
        gbase = run_grass(
            OUT_FOLDER, grassBIN='grass76', location='shpdif',
            srs=GRASS_REGION_TEMPLATE
        )
        
        import grass.script as grass
        import grass.script.setup as gsetup
        
        gsetup.init(gbase, OUT_FOLDER, 'shpdif', 'PERMANENT')
        
        from gasp.mng.grstbl import rename_col
        from gasp.to.shp.grs import shp_to_grs, grs_to_shp
        from gasp.to.rst     import rst_to_grs
        from gasp.mng.fld    import rename_column
    
    # Convert to SHAPE if file is Raster
    # Import to GRASS GIS if GIS SOFTWARE == GRASS
    i = 0
    _SHP_TO_COMPARE = {}
    for s in SHAPES_TO_COMPARE:
        isRaster = check_isRaster(s)
    
        if isRaster:
            if GIS_SOFTWARE == "ARCGIS":
                d = rst_to_polyg(s, os.path.join(
                    os.path.dirname(s), get_filename(s) + '.shp'
                ), gisApi='arcpy')
        
                _SHP_TO_COMPARE[d] = "gridcode"
            
            elif GIS_SOFTWARE == "GRASS":
                # To GRASS
                rstName = get_filename(s)
                inRst   = rst_to_grs(s, "rst_" + rstName, as_cmd=True)
                # To Raster
                d       = rst_to_polyg(inRst, rstName,
                    rstColumn="lulc_{}".format(i), gisApi="grasscmd")
                
                # Export Shapefile
                shp = grs_to_shp(
                    d, os.path.join(OUT_FOLDER, d + '.shp'), "area")
                
                _SHP_TO_COMPARE[shp] = "lulc_{}".format(i)
    
        else:
            if GIS_SOFTWARE == "ARCGIS":
                _SHP_TO_COMPARE[s] = SHAPES_TO_COMPARE[s]
            
            elif GIS_SOFTWARE == "GRASS":
                # To GRASS
                grsV = shp_to_grs(s, get_filename(s), asCMD=True)
                
                # Change name of column with comparing value
                rename_col(
                    grsV, SHAPES_TO_COMPARE[s],
                    "lulc_{}".format(i), as_cmd=True
                )
                
                # Export
                shp = grs_to_shp(
                    grsV, os.path.join(OUT_FOLDER, grsV + '_rn.shp'), "area")
                
                _SHP_TO_COMPARE[shp] = "lulc_{}".format(i)
        
        i += 1
    
    SHAPES_TO_COMPARE = _SHP_TO_COMPARE
    if GIS_SOFTWARE == "ARCGIS":
        from gasp.cpu.arcg.mng.fld    import calc_fld
        from gasp.cpu.arcg.mng.wspace import create_geodb
        from gasp.mng.gen             import copy_feat
        
        # Sanitize data and Add new field
        __SHAPES_TO_COMPARE = {}
        i = 0
    
        # Create GeoDatabase
        geodb = create_geodb(OUT_FOLDER, 'geo_sanitize')
    
        """ Sanitize Data """
        for k in SHAPES_TO_COMPARE:
            # Send data to GeoDatabase only to sanitize
            newFc = shp_to_shp(
                k, os.path.join(geodb, get_filename(k)), gisApi='arcpy')
    
            # Create a copy to change
            newShp = copy_feat(newFc,
                 os.path.join(OUT_FOLDER, os.path.basename(k)), gisApi='arcpy'
            )
    
            # Sanitize field name with interest data
            NEW_FLD = "lulc_{}".format(i)
            calc_fld(
                newShp, NEW_FLD, "[{}]".format(SHAPES_TO_COMPARE[k]),
                isNewField={"TYPE" : "INTEGER", "LENGTH" : 5, "PRECISION" : ""}
            )
    
            __SHAPES_TO_COMPARE[newShp] = NEW_FLD
    
            i += 1
    
    else:
        __SHAPES_TO_COMPARE = SHAPES_TO_COMPARE
    
    # Create database
    conPARAM["DATABASE"] = create_db(conPARAM, DB)
    
    """ Union SHAPEs """
    
    UNION_SHAPE = {}
    FIX_GEOM = {}
    
    def fix_geometry(shp):
        # Send data to PostgreSQL
        nt = shp_to_psql(conPARAM, shp, SRS_CODE, api='shp2pgsql')
    
        # Fix data
        corr_tbl = fix_geom(
            conPARAM, nt, "geom", "corr_{}".format(nt),
            colsSelect=['gid', __SHAPES_TO_COMPARE[shp]]
        )
    
        # Check if we have multiple geometries
        geomN = check_geomtype_in_table(conPARAM, corr_tbl)
    
        if geomN > 1:
            corr_tbl = select_main_geom_type(
                conPARAM, corr_tbl, "corr2_{}".format(nt))
    
        # Export data again
        newShp = psql_to_shp(
            conPARAM, corr_tbl,
            os.path.join(OUT_FOLDER, corr_tbl + '.shp'),
            api='pgsql2shp', geom_col='geom'
        )
        
        return newShp
    
    SHPS = __SHAPES_TO_COMPARE.keys()
    for i in range(len(SHPS)):
        for e in range(i + 1, len(SHPS)):
            if GIS_SOFTWARE == 'ARCGIS':
                # Try the union thing
                unShp = union(SHPS[i], SHPS[e], os.path.join(
                    OUT_FOLDER, "un_{}_{}.shp".format(i, e)
                ), api_gis="arcpy")
        
                # See if the union went all right
                if not os.path.exists(unShp):
                    # Union went not well
            
                    # See if geometry was already fixed
                    if SHPS[i] not in FIX_GEOM:
                        # Fix SHPS[i] geometry
                        FIX_GEOM[SHPS[i]] = fix_geometry(SHPS[i])
            
                    if SHPS[e] not in FIX_GEOM:
                        FIX_GEOM[SHPS[e]] = fix_geometry(SHPS[e])
            
                    # Run Union again
                    unShp = union(FIX_GEOM[SHPS[i]], FIX_GEOM[SHPS[e]], os.path.join(
                        OUT_FOLDER, "un_{}_{}_f.shp".format(i, e)
                    ), api_gis="arcpy")
            
            elif GIS_SOFTWARE == "GRASS":
                # Optimized Union
                print "Union between {} and {}".format(SHPS[i], SHPS[e])
                time_a = datetime.datetime.now().replace(microsecond=0)
                __unShp = optimized_union_anls(
                    SHPS[i], SHPS[e],
                    os.path.join(OUT_FOLDER, "un_{}_{}.shp".format(i, e)),
                    GRASS_REGION_TEMPLATE, SRS_CODE,
                    os.path.join(OUT_FOLDER, "work_{}_{}".format(i, e)),
                    multiProcess=True
                )
                time_b = datetime.datetime.now().replace(microsecond=0)
                print time_b - time_a
                
                # Rename cols
                unShp = rename_column(__unShp, {
                    "a_" + __SHAPES_TO_COMPARE[SHPS[i]] : __SHAPES_TO_COMPARE[SHPS[i]],
                    "b_" + __SHAPES_TO_COMPARE[SHPS[e]] : __SHAPES_TO_COMPARE[SHPS[e]]
                }, os.path.join(OUT_FOLDER, "un_{}_{}_rn.shp".format(i, e)))
            
            UNION_SHAPE[(SHPS[i], SHPS[e])] = unShp
    
    # Send data one more time to postgresql
    SYNTH_TBL = {}
    
    for uShp in UNION_SHAPE:
        # Send data to PostgreSQL
        union_tbl = shp_to_psql(
            conPARAM, UNION_SHAPE[uShp], SRS_CODE, api='shp2pgsql'
        )
        
        # Produce table with % of area equal in both maps
        areaMapTbl = ntbl_by_query(conPARAM, "{}_syn".format(union_tbl), (
            "SELECT CAST('{lulc_1}' AS text) AS lulc_1, "
            "CAST('{lulc_2}' AS text) AS lulc_2, "
            "round("
                "CAST(SUM(g_area) / 1000000 AS numeric), 4"
            ") AS agree_area, round("
                "CAST((SUM(g_area) / MIN(total_area)) * 100 AS numeric), 4"
            ") AS agree_percentage, "
            "round("
                "CAST(MIN(total_area) / 1000000 AS numeric), 4"
            ") AS total_area FROM ("
                "SELECT {map1_cls}, {map2_cls}, ST_Area(geom) AS g_area, "
                "CASE "
                    "WHEN {map1_cls} = {map2_cls} "
                    "THEN 1 ELSE 0 "
                "END AS isthesame, total_area FROM {tbl}, ("
                    "SELECT SUM(ST_Area(geom)) AS total_area FROM {tbl}"
                ") AS foo2"
            ") AS foo WHERE isthesame = 1 "
            "GROUP BY isthesame"
        ).format(
            lulc_1 = get_filename(uShp[0]), lulc_2 = get_filename(uShp[1]),
            map1_cls = __SHAPES_TO_COMPARE[uShp[0]],
            map2_cls = __SHAPES_TO_COMPARE[uShp[1]],
            tbl = union_tbl
        ), api='psql')
        
        # Produce confusion matrix for the pair in comparison
        lulcCls = query_to_df(conPARAM, (
            "SELECT fcol FROM ("
                "SELECT CAST({map1_cls} AS text) AS fcol FROM {tbl} "
                "GROUP BY {map1_cls} "
                "UNION ALL SELECT CAST({map2_cls} AS text) FROM {tbl} "
                "GROUP BY {map2_cls}"
            ") AS foo GROUP BY fcol ORDER BY fcol"
        ).format(
            tbl = union_tbl,
            map1_cls = __SHAPES_TO_COMPARE[uShp[0]],
            map2_cls = __SHAPES_TO_COMPARE[uShp[1]]
        ), db_api='psql').fcol.tolist()
        
        matrixTbl = ntbl_by_query(conPARAM, "{}_matrix".format(union_tbl), (
            "SELECT * FROM crosstab('"
                "SELECT CASE "
                    "WHEN foo.{map1_cls} IS NOT NULL "
                    "THEN foo.{map1_cls} ELSE jtbl.flyr "
                "END AS lulc1_cls, CASE "
                    "WHEN foo.{map2_cls} IS NOT NULL "
                    "THEN foo.{map2_cls} ELSE jtbl.slyr "
                "END AS lulc2_cls, CASE "
                    "WHEN foo.garea IS NOT NULL "
                    "THEN round(CAST(foo.garea / 1000000 AS numeric)"
                    ", 3) ELSE 0 "
                "END AS garea FROM ("
                    "SELECT CAST({map1_cls} AS text) AS {map1_cls}, "
                    "CAST({map2_cls} AS text) AS {map2_cls}, "
                    "SUM(ST_Area(geom)) AS garea "
                    "FROM {tbl} GROUP BY {map1_cls}, {map2_cls}"
                ") AS foo FULL JOIN ("
                    "SELECT f.flyr, s.slyr FROM ("
                        "SELECT CAST({map1_cls} AS text) AS flyr "
                        "FROM {tbl} GROUP BY {map1_cls}"
                    ") AS f, ("
                        "SELECT CAST({map2_cls} AS text) AS slyr "
                        "FROM {tbl} GROUP BY {map2_cls}"
                    ") AS s"
                ") AS jtbl "
                "ON foo.{map1_cls} = jtbl.flyr AND "
                "foo.{map2_cls} = jtbl.slyr "
                "ORDER BY 1,2"
            "') AS ct("
                "lulc_cls text, {crossCols}"
            ")"
        ).format(
            crossCols = ", ".join([
                "cls_{} numeric".format(c) for c in lulcCls]),
            tbl = union_tbl,
            map1_cls = __SHAPES_TO_COMPARE[uShp[0]],
            map2_cls = __SHAPES_TO_COMPARE[uShp[1]]
        ), api='psql')
        
        SYNTH_TBL[uShp] = {"TOTAL" : areaMapTbl, "MATRIX" : matrixTbl}
    
    # UNION ALL TOTAL TABLES
    total_table = tbls_to_tbl(
        conPARAM, [SYNTH_TBL[k]["TOTAL"] for k in SYNTH_TBL], 'total_table'
    )
    
    # Create table with % of agreement between each pair of maps
    mapsNames = query_to_df(conPARAM, (
        "SELECT lulc FROM ("
            "SELECT lulc_1 AS lulc FROM {tbl} GROUP BY lulc_1 "
            "UNION ALL "
            "SELECT lulc_2 AS lulc FROM {tbl} GROUP BY lulc_2"
        ") AS lu GROUP BY lulc ORDER BY lulc"
    ).format(tbl=total_table), db_api='psql').lulc.tolist()
    
    FLDS_TO_PIVOT = ["agree_percentage", "total_area"]
    
    Q = (
        "SELECT * FROM crosstab('"
            "SELECT CASE "
                "WHEN foo.lulc_1 IS NOT NULL THEN foo.lulc_1 ELSE jtbl.tmp1 "
            "END AS lulc_1, CASE "
                "WHEN foo.lulc_2 IS NOT NULL THEN foo.lulc_2 ELSE jtbl.tmp2 "
            "END AS lulc_2, CASE "
                "WHEN foo.{valCol} IS NOT NULL THEN foo.{valCol} ELSE 0 "
            "END AS agree_percentage FROM ("
                "SELECT lulc_1, lulc_2, {valCol} FROM {tbl} UNION ALL "
                "SELECT lulc_1, lulc_2, {valCol} FROM ("
                    "SELECT lulc_1 AS lulc_2, lulc_2 AS lulc_1, {valCol} "
                    "FROM {tbl}"
                ") AS tst"
            ") AS foo FULL JOIN ("
                "SELECT lulc_1 AS tmp1, lulc_2 AS tmp2 FROM ("
                    "SELECT lulc_1 AS lulc_1 FROM {tbl} GROUP BY lulc_1 "
                    "UNION ALL "
                    "SELECT lulc_2 AS lulc_1 FROM {tbl} GROUP BY lulc_2"
                ") AS tst_1, ("
                    "SELECT lulc_1 AS lulc_2 FROM {tbl} GROUP BY lulc_1 "
                    "UNION ALL "
                    "SELECT lulc_2 AS lulc_2 FROM {tbl} GROUP BY lulc_2"
                ") AS tst_2 WHERE lulc_1 = lulc_2 GROUP BY lulc_1, lulc_2"
            ") AS jtbl ON foo.lulc_1 = jtbl.tmp1 AND foo.lulc_2 = jtbl.tmp2 "
            "ORDER BY lulc_1, lulc_2"
        "') AS ct("
            "lulc_map text, {crossCols}"
        ")"
    )
    
    TOTAL_AGREE_TABLE = None
    TOTAL_AREA_TABLE  = None
    for f in FLDS_TO_PIVOT:
        if not TOTAL_AGREE_TABLE:
            TOTAL_AGREE_TABLE = ntbl_by_query(
                conPARAM, "agreement_table", Q.format(
                    tbl = total_table, valCol=f,
                    crossCols = ", ".join([
                        "{} numeric".format(map_) for map_ in mapsNames])
                ), api='psql'
            )
        
        else:
            TOTAL_AREA_TABLE = ntbl_by_query(
                conPARAM, "area_table", Q.format(
                    tbl = total_table, valCol=f,
                    crossCols = ", ".join([
                        "{} numeric".format(map_) for map_ in mapsNames])
                ), api='psql'
            )
    
    # Union Mapping
    UNION_MAPPING = pandas.DataFrame([[
        get_filename(k[0]), get_filename(k[1]),
        get_filename(UNION_SHAPE[k])] for k in UNION_SHAPE],
        columns=['shp_a', 'shp_b', 'union_shp']
    ) if GIS_SOFTWARE == "ARCGIS" else pandas.DataFrame([[
        k[0], k[1], get_filename(UNION_SHAPE[k])] for k in UNION_SHAPE],
        columns=['shp_a', 'shp_b', 'union_shp']
    )
    
    UNION_MAPPING = df_to_db(conPARAM, UNION_MAPPING, 'union_map', api='psql')
    
    # Export Results
    TABLES = [UNION_MAPPING, TOTAL_AGREE_TABLE, TOTAL_AREA_TABLE] + [
        SYNTH_TBL[x]["MATRIX"] for x in SYNTH_TBL
    ]
    
    SHEETS = ["union_map", "agreement_percentage", "area_with_data_km"] + [
        "{}_{}".format(
            get_filename(x[0])[:15], get_filename(x[1])[:15]
        ) for x in SYNTH_TBL
    ]
    
    db_to_xls(
        conPARAM, ["SELECT * FROM {}".format(x) for x in TABLES],
        REPORT, sheetsNames=SHEETS, dbAPI='psql'
    )
    
    return REPORT


def erase(inShp, erase_feat, out, splitMultiPart=None, notTbl=None,
          api='pygrass'):
    """
    Difference between two feature classes
    
    API's Available:
    * pygrass;
    * grass;
    * saga;
    * arcpy
    """
    
    if api == 'saga':
        """
        Using SAGA GIS
        
        It appears to be very slow
        """
        from gasp import exec_cmd
    
        cmd = (
            'saga_cmd shapes_polygons 15 -A {in_shp} -B {erase_shp} '
            '-RESULT {output} -SPLIT {sp}'
        ).format(
            in_shp=inShp, erase_shp=erase_feat,
            output=out,
            sp='0' if not splitMultiPart else '1'
        )
    
        outcmd = exec_cmd(cmd)
    
    elif api == 'pygrass':
        """
        Use pygrass
        """
        
        from grass.pygrass.modules import Module
        
        erase = Module(
            "v.overlay", ainput=inShp, atype="area",
            binput=erase_feat, btype="area", operator="not",
            output=out, overwrite=True, run_=False, quiet=True,
            flags='t' if notTbl else None
        )
    
        erase()
    
    elif api == 'grass':
        """
        Use GRASS GIS tool via command line
        """
        
        from gasp import exec_cmd
        
        rcmd = exec_cmd((
            "v.overlay ainput={} atype=area binput={} "
            "btype=area operator=not output={} {}"
            "--overwrite --quiet"
        ).format(inShp, erase_feat, out, "" if not notTbl else "-t "))
    
    elif api == 'arcpy':
        import arcpy
        
        arcpy.Erase_analysis(
            in_features=inShp, erase_features=erase_feat, 
            out_feature_class=out
        )
    
    else:
        raise ValueError('API {} is not available!'.format(api))
    
    return out
