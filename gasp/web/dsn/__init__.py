"""
Tools to work with Social Network Data
"""

def dsn_data_collection_by_multibuffer(inBuffers, workspace, conParam, datasource,
                                       keywords=None):
    """
    Extract Digital Social Network Data for each sub-buffer in buffer.
    A sub-buffer is a buffer with a radius equals to the main buffer radius /2
    and with a central point at North, South, East, West, Northeast, Northwest,
    Southwest and Southeast of the main buffer central point.
    
    inBuffers = {
        "lisbon"    : {
            'x'      : -89004.994779, # in meters
            'y'      : -102815.866054, # in meters
            'radius' : 10000,
            'epsg'   : 3763
        },
        "london     : {
            'x'      : -14210.551441, # in meters
            'y'      : 6711542.47559, # in meters
            'radius' : 10000,
            'epsg'   : 3857
        }
    }
    or
    inBuffers = {
        "lisbon" : {
            "path" : /path/to/file.shp,
            "epsg" : 3763
        }
    }
    
    keywords = ['flood', 'accident', 'fire apartment', 'graffiti', 'homeless']
    
    datasource = 'facebook' or datasource = 'flickr'
    TODO: Only works for Flickr and Facebook
    """
    
    import os
    from osgeo             import ogr
    from gasp              import goToList
    from gasp.sql.mng.db   import create_db
    from gasp.sql.mng.qw   import ntbl_by_query
    from gasp.to.sql       import shp_to_psql, geodf_to_psql
    from gasp.to.shp       import df_to_shp
    from gasp.to.shp       import psql_to_shp
    from gasp.anls.prox.bf import get_sub_buffers, dic_buffer_array_to_shp
    
    if datasource == 'flickr':
        from gasp.web.dsn.flickr import photos_location
    
    elif datasource == 'facebook':
        from gasp.web.dsn.fb.places import places_by_query
    
    keywords = goToList(keywords)
    keywords = ["None"] if not keywords else keywords
    
    # Create Database to Store Data
    create_db(conParam, conParam["DB"], overwrite=True)
    conParam["DATABASE"] = conParam["DB"]
    
    for city in inBuffers:
        # Get Smaller Buffers
        if "path" in inBuffers[city]:
            # Get X, Y and Radius
            from gasp.gdl.anls.prox.bfs import buffer_properties
            
            __bfprop = buffer_properties(
                inBuffers[city]["path"], inBuffers[city]["epsg"], isFile=True
            )
            
            inBuffers[city]["x"]      = __bfprop["X"]
            inBuffers[city]["y"]      = __bfprop["Y"]
            inBuffers[city]["radius"] = __bfprop["R"]
        
        inBuffers[city]["list_buffer"] = [{
            'X' : inBuffers[city]["x"], 'Y' : inBuffers[city]["y"],
            'RADIUS' : inBuffers[city]['radius'], 'cardeal' : 'major'
        }] + get_sub_buffers(
            inBuffers[city]["x"], inBuffers[city]["y"],
            inBuffers[city]["radius"]
        )
        
        # Smaller Buffers to File
        multiBuffer = os.path.join(workspace, 'buffers_{}.shp'.format(city))
        dic_buffer_array_to_shp(
            inBuffers[city]["list_buffer"], multiBuffer,
            inBuffers[city]['epsg'], fields={'cardeal' : ogr.OFTString}
        )
        
        # Retrive data for each keyword and buffer
        # Record these elements in one dataframe
        c       = None
        tblData = None
        for bf in inBuffers[city]["list_buffer"]:
            for k in keywords:
                if datasource == 'flickr':
                    tmpData = photos_location(
                        bf, inBuffers[city]["epsg"],
                        keyword=k if k != 'None' else None,
                        epsg_out=inBuffers[city]["epsg"],
                        onlySearchAreaContained=False
                    )
                
                elif datasource == 'facebook':
                    tmpData = places_by_query(
                        bf, inBuffers[city]["epsg"],
                        keyword=k if k != 'None' else None,
                        epsgOut=inBuffers[city]["epsg"],
                        onlySearchAreaContained=False
                    )
                
                if type(tmpData) == int:
                    print "NoData finded for buffer '{}' and keyword '{}'".format(
                        bf['cardeal'], k
                    )
                    
                    continue
                
                tmpData["keyword"]   = k
                tmpData["buffer_or"] = bf["cardeal"]
                
                if not c:
                    tblData = tmpData
                    c = 1
                else:
                    tblData = tblData.append(tmpData, ignore_index=True)
        
        inBuffers[city]["data"] = tblData
        
        # Get data columns names
        cols = inBuffers[city]["data"].columns.values
        dataColumns = [
            c for c in cols if c != 'geom' and c != 'keyword' \
            and c != 'buffer_or' and c != 'geometry'
        ]
        
        # Send data to PostgreSQL
        if 'geometry' in cols:
            cgeom = 'geometry'
        
        else:
            cgeom = 'geom'
        
        inBuffers[city]["table"] = 'tbldata_{}'.format(city)
        
        geodf_to_psql(
            conParam, inBuffers[city]["data"],
            inBuffers[city]["table"],
            inBuffers[city]["epsg"], 'POINT', colGeom=cgeom
        )
        
        # Send Buffers data to PostgreSQL
        inBuffers[city]["pg_buffer"] = shp_to_psql(
            conParam, multiBuffer, inBuffers[city]["epsg"],
            pgTable='buffers_{}'.format(city),
            api="shp2pgsql"
        )
        
        inBuffers[city]["filter_table"] = ntbl_by_query(
            conParam, "filter_{}".format(inBuffers[city]["table"]), (
                "SELECT srcdata.*, "
                "array_agg(buffersg.cardeal ORDER BY buffersg.cardeal) "
                "AS intersect_buffer FROM ("
                    "SELECT {cols}, keyword, geom, "
                    "array_agg(buffer_or ORDER BY buffer_or) AS extracted_buffer "
                    "FROM {pgtable} "
                    "GROUP BY {cols}, keyword, geom"
                ") AS srcdata, ("
                    "SELECT cardeal, geom AS bfg FROM {bftable}"
                ") AS buffersg "
                "WHERE ST_Intersects(srcdata.geom, buffersg.bfg) IS TRUE "
                "GROUP BY {cols}, keyword, geom, extracted_buffer"
            ).format(
                cols    = ", ".join(dataColumns),
                pgtable = inBuffers[city]["table"],
                bftable = inBuffers[city]["pg_buffer"]
            ), api='psql'
        )
        
        inBuffers[city]["outside_table"] = ntbl_by_query(
            conParam, "outside_{}".format(inBuffers[city]["table"]), (
                "SELECT * FROM ("
                "SELECT srcdata.*, "
                "array_agg(buffersg.cardeal ORDER BY buffersg.cardeal) "
                "AS not_intersect_buffer FROM ("
                    "SELECT {cols}, keyword, geom, "
                    "array_agg(buffer_or ORDER BY buffer_or) AS extracted_buffer "
                    "FROM {pgtable} "
                    "GROUP BY {cols}, keyword, geom"
                ") AS srcdata, ("
                    "SELECT cardeal, geom AS bfg FROM {bftable}"
                ") AS buffersg "
                "WHERE ST_Intersects(srcdata.geom, buffersg.bfg) IS NOT TRUE "
                "GROUP BY {cols}, keyword, geom, extracted_buffer"
                ") AS foo WHERE array_length(not_intersect_buffer, 1) = 9"
            ).format(
                cols    = ", ".join(dataColumns),
                pgtable = inBuffers[city]["table"],
                bftable = inBuffers[city]["pg_buffer"]
            ), api='psql'
        )
        
        # Union these two tables
        inBuffers[city]["table"] = ntbl_by_query(
            conParam, "data_{}".format(city), (
                "SELECT * FROM {intbl} UNION ALL "
                "SELECT {cols}, keyword, geom, extracted_buffer, "
                "CASE WHEN array_length(not_intersect_buffer, 1) = 9 "
                "THEN '{array_symbol}' ELSE not_intersect_buffer END AS "
                "intersect_buffer FROM {outbl}"
            ).format(
                intbl        = inBuffers[city]["filter_table"],
                outbl        = inBuffers[city]["outside_table"],
                cols         = ", ".join(dataColumns),
                array_symbol = '{' + '}'
            ), api='psql'
        )
        
        """
        Get Buffers table with info related:
        -> pnt_obtidos = nr pontos obtidos usando esse buffer
        -> pnt_obtidos_fora = nt pontos obtidos fora desse buffer, mas 
        obtidos com ele
        -> pnt_intersect = nt pontos que se intersectam com o buffer
        -> pnt_intersect_non_obtain = nr pontos que se intersectam mas nao 
        foram obtidos como buffer
        """
        inBuffers[city]["pg_buffer"] = ntbl_by_query(
            conParam, "dt_{}".format(inBuffers[city]["pg_buffer"]), (
                "SELECT main.*, get_obtidos.pnt_obtidos, "
                "obtidos_fora.pnt_obtidos_fora, intersecting.pnt_intersect, "
                "int_not_obtained.pnt_intersect_non_obtain "
                "FROM {bf_table} AS main "
                "LEFT JOIN ("
                    "SELECT gid, cardeal, COUNT(gid) AS pnt_obtidos "
                    "FROM {bf_table} AS bf "
                    "INNER JOIN {dt_table} AS dt "
                    "ON bf.cardeal = ANY(dt.extracted_buffer) "
                    "GROUP BY gid, cardeal"
                ") AS get_obtidos ON main.gid = get_obtidos.gid "
                "LEFT JOIN ("
                    "SELECT gid, cardeal, COUNT(gid) AS pnt_obtidos_fora "
                    "FROM {bf_table} AS bf "
                    "INNER JOIN {dt_table} AS dt "
                    "ON bf.cardeal = ANY(dt.extracted_buffer) "
                    "WHERE ST_Intersects(bf.geom, dt.geom) IS NOT TRUE "
                    "GROUP BY gid, cardeal"
                ") AS obtidos_fora ON main.gid = obtidos_fora.gid "
                "LEFT JOIN ("
                    "SELECT gid, cardeal, COUNT(gid) AS pnt_intersect "
                    "FROM {bf_table} AS bf "
                    "INNER JOIN {dt_table} AS dt "
                    "ON bf.cardeal = ANY(dt.intersect_buffer) "
                    "GROUP BY gid, cardeal"
                ") AS intersecting ON main.gid = intersecting.gid "
                "LEFT JOIN ("
                    "SELECT gid, cardeal, COUNT(gid) AS pnt_intersect_non_obtain "
                    "FROM {bf_table} AS bf "
                    "INNER JOIN {dt_table} AS dt "
                    "ON bf.cardeal = ANY(dt.intersect_buffer) "
                    "WHERE NOT (bf.cardeal = ANY(dt.extracted_buffer)) "
                    "GROUP BY gid, cardeal"
                ") AS int_not_obtained "
                "ON main.gid = int_not_obtained.gid "
                "ORDER BY main.gid"
            ).format(
                bf_table = inBuffers[city]["pg_buffer"],
                dt_table = inBuffers[city]["table"]
            ), api='psql'
        )
        
        """
        Get Points table with info related:
        -> nobtido = n vezes um ponto foi obtido
        -> obtido_e_intersect = n vezes um ponto foi obtido usando um buffer 
        com o qual se intersecta
        -> obtido_sem_intersect = n vezes um ponto foi obtido usando um buffer
        com o qual nao se intersecta
        -> nintersect = n vezes que um ponto se intersecta com um buffer
        -> intersect_sem_obtido = n vezes que um ponto nao foi obtido apesar
        de se intersectar com o buffer
        """
        inBuffers[city]["table"] = ntbl_by_query(
            conParam, "info_{}".format(city), (
                "SELECT {cols}, dt.keyword, dt.geom, "
                "CAST(dt.extracted_buffer AS text) AS extracted_buffer, "
                "CAST(dt.intersect_buffer AS text) AS intersect_buffer, "
                "array_length(extracted_buffer, 1) AS nobtido, "
                "SUM(CASE WHEN ST_Intersects(bf.geom, dt.geom) IS TRUE "
                    "THEN 1 ELSE 0 END) AS obtido_e_intersect, "
                "(array_length(extracted_buffer, 1) - SUM("
                    "CASE WHEN ST_Intersects(bf.geom, dt.geom) IS TRUE "
                    "THEN 1 ELSE 0 END)) AS obtido_sem_intersect, "
                "array_length(intersect_buffer, 1) AS nintersect, "
                "(array_length(intersect_buffer, 1) - SUM("
                    "CASE WHEN ST_Intersects(bf.geom, dt.geom) IS TRUE "
                    "THEN 1 ELSE 0 END)) AS intersect_sem_obtido "
                "FROM {dt_table} AS dt "
                "INNER JOIN {bf_table} AS bf "
                "ON bf.cardeal = ANY(dt.extracted_buffer) "
                "GROUP BY {cols}, dt.keyword, dt.geom, "
                "dt.extracted_buffer, dt.intersect_buffer"
            ).format(
                dt_table = inBuffers[city]["table"],
                bf_table = inBuffers[city]["pg_buffer"],
                cols     = ", ".join(["dt.{}".format(x) for x in dataColumns])
            ), api='psql'
        )
        
        # Export Results
        psql_to_shp(
            conParam, 
            inBuffers[city]["table"],
            os.path.join(workspace, "{}.shp".format(inBuffers[city]["table"])),
            api='pandas', epsg=inBuffers[city]["epsg"],
            geom_col='geom'
        )
        
        psql_to_shp(
            conParam, 
            inBuffers[city]["pg_buffer"],
            os.path.join(workspace, "{}.shp".format(inBuffers[city]["pg_buffer"])),
            api='pandas', epsg=inBuffers[city]["epsg"],
            geom_col="geom"
        )
    
    return inBuffers


def dsnsearch_by_cell(GRID_PNT, EPSG, RADIUS, DATA_SOURCE, conpgsql, OUTPUT_TABLE):
    """
    Search for data in DSN and other platforms by cell
    """
    
    import time
    from gasp.fm                import tbl_to_obj
    from gasp.sql.mng.db        import create_db
    from gasp.web.dsn.fb.places import places_by_query
    from gasp.mng.prj           import project
    from gasp.mng.gen           import merge_df
    from gasp.to.sql            import geodf_to_psql
    from gasp.to.shp            import psql_to_shp
    from gasp.sql.mng.qw        import ntbl_by_query
    from gasp.to.shp            import psql_to_shp
    
    # Open GRID SHP
    GRID_DF = tbl_to_obj(GRID_PNT)
    GRID_DF = project(
        GRID_DF, None, 4326, gisApi='pandas') if EPSG != 4326 else GRID_DF
    
    GRID_DF["lng"]     = GRID_DF.geometry.x.astype(float)
    GRID_DF["lat"]     = GRID_DF.geometry.y.astype(float)
    GRID_DF["grid_id"] = GRID_DF.index
    
    # GET DATA
    RESULTS = []
    def get_data(row, datasrc):
        if datasrc == 'facebook':
            d = places_by_query(
                {'x' : row.lng, 'y' : row.lat, 'r' : RADIUS}, 4326,
                keyword=None, epsgOut=EPSG, _limit='100',
                onlySearchAreaContained=None
            )
        
        else:
            raise ValueError('{} as datasource is not a valid value'.format(datasrc))
        
        if type(d) == int:
            return
        
        d['grid_id'] = row.grid_id
        
        RESULTS.append(d)
        
        time.sleep(5)
    
    GRID_DF.apply(lambda x: get_data(x, DATA_SOURCE), axis=1)
    
    RT = merge_df(RESULTS)
    
    # Create DB
    create_db(conpgsql, conpgsql["DB"], overwrite=True)
    conpgsql["DATABASE"] = conpgsql["DB"]
    
    # Send Data to PostgreSQL
    geodf_to_psql(
        conpgsql, RESULTS_TABLE, "{}_data".format(DATA_SOURCE),
        EPSG, "POINT",
        colGeom='geometry' if 'geometry' in RT.columns.values else 'geom'
    )
    
    COLS = [
        x for x in RT.columns.values if x != "geometry" and \
        x != 'geom' and x != "grid_id"
    ] + ["geom"]
    
    GRP_BY_TBL = ntbl_by_query(conpgsql, "{}_grpby".format(DATA_SOURCE), (
        "SELECT {cols}, CAST(array_agg(grid_id) AS text) AS grid_id "
        "FROM {dtsrc}_data GROUP BY {cols}"
    ).format(cols=", ".join(COLS), dtsrc=DATA_SOURCE), api='psql')
    
    psql_to_shp(
        conpgsql, GRP_BY_TBL, OUTPUT_TABLE,
        api="pandas", epsg=EPSG, geom_col="geom"
    )
    
    return OUTPUT_TABLE

