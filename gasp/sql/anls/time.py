"""
Analyse time references in PGTABLES
"""


def ID_rows_with_temporal_proximity_by_entities(conParam, table, entity_field,
                                 day_field, hour_field, hour_decimal_field,
                                 time_tolerance, outXlsPath):
    """
    Retrieve rows from one pgtable with some temporal proximity
    
    Table structure should be
    entity |     day    | hour | hour_decimal
      0    | 2018-01-02 |  5   |   5,10
      0    | 2018-01-03 |  4   |   4,15
      0    | 2018-01-02 |  5   |   5,12
      0    | 2018-01-02 |  5   |   5,8
      1    | 2018-01-02 |  4   |   4,10
      1    | 2018-01-02 |  5   |   5,12
      1    | 2018-01-02 |  4   |   4,20
      1    | 2018-01-02 |  4   |   4,12
      1    | 2018-01-02 |  4   |   4,6
    
    For a time_tolerance of 5 minutes, the output table will have
    the rows with a temporal difference inside/bellow that time tolerance
    
    entity_field could be more than one field
    
    This method only identifies if one entity, for one day, has rows 
    very close of each others, in terms of time.
    
    Not a good strategy for large tables. For large tables, SQL based methods
    are needed
    """
    
    import pandas
    from gasp             import goToList
    from gasp.fm.sql      import query_to_df
    from gasp.sql.mng.fld import get_columns_type
    from gasp.to          import obj_to_tbl
    
    entity_field = goToList(entity_field)
    COLS = entity_field + [day_field, hour_field]
    COLS_TYPE = get_columns_type(conParam, table)
    
    # TIME TOLERANCE IN HOURS
    TIME_TOLERANCE = time_tolerance / 60.0
    
    def thereIsRowsSameTimeInt(row):
        whr = []
        for c in COLS:
            if COLS_TYPE[c] == str:
                whr.append("{}='{}'".format(c, row[c]))
            else:
                whr.append("{}={}".format(c, row[c]))
        
        hourRows = query_to_df(conParam,
            "SELECT {} FROM {} WHERE {}".format(
                hour_decimal_field, table,
                " AND ".join(whr)
            ), db_api='psql'
        )[hour_decimal_field].tolist()
        
        for i in range(len(hourRows)):
            for e in range(i+1, len(hourRows)):
                dif = abs(hourRows[i][0] - hourRows[e][0])
                
                if dif < TIME_TOLERANCE:
                    break
            
            if dif < TIME_TOLERANCE:
                break
        
        if dif < TIME_TOLERANCE:
            row['time_difference'] = 1
        else:
            row['time_difference'] = 0
        
        return row
    
    # Count entity occourrences for one day and hour
    countsByEntityTime = query_to_df(conParam, (
        "SELECT {scols}, conta FROM "
        "(SELECT {scols}, COUNT({ent}) AS conta FROM {tbl} "
        "GROUP BY {scols}) AS foo WHERE conta > 1"
    ).format(
        scols = ', '.join(COLS),
        ent = entity_field[0],
        tbl = table
    ), db_api='psql')
    
    # For each row in the last count, When count is > 1
    # Check time difference between rows for one day and hour
    countsByEntityTime = countsByEntityTime.apply(
        lambda x: thereIsRowsSameTimeInt(x), axis=1
    )
    
    obj_to_tbl(countsByEntityTime, outXlsPath)
    
    return outXlsPath


def del_rows_by_temporal_proximity(conpsql, table, entity_fields,
                                   day_field, hour_field, hour_decimal,
                                   minute_field, second_field,
                                   time_tolerance, outresult, exclusionRows=None):
    """
    Exclude rows from one pgtable within some temporal interval from the
    previous row.
    
    Table structure should be
    entity |     day    | hour | minute | seconds | hour_decimal
      0    | 2018-01-02 |  5   |   X    |    X    |     5,10
      0    | 2018-01-03 |  4   |   X    |    X    |     4,15
      0    | 2018-01-02 |  5   |   X    |    X    |     5,12
      0    | 2018-01-02 |  5   |   X    |    X    |     5,8
      1    | 2018-01-02 |  4   |   X    |    X    |     4,10
      1    | 2018-01-02 |  5   |   X    |    X    |     5,12
      1    | 2018-01-02 |  4   |   X    |    X    |     4,20
      1    | 2018-01-02 |  4   |   X    |    X    |     4,12
      1    | 2018-01-02 |  4   |   X    |    X    |     4,6
    """
    
    from gasp            import goToList
    from gasp.sql.mng.qw import ntbl_by_query
    
    entity_fields = goToList(entity_fields)
    
    if not entity_fields:
        raise ValueError("entity_fields value is not valid!")
    
    if exclusionRows:
        # Get Rows deleted in table
        
        sql = (
            "SELECT *, ({hourDec} - previous_hour) AS deltatime FROM ("
                "SELECT *, {lag_entity}, "
                "LAG({hourDec}) OVER(PARTITION BY "
                    "{entityCols}, {dayF} ORDER BY "
                    "{entityCols}, {dayF}, {hourF}, {minutesF}, {secondsF}"
                ") AS previous_hour "
                "FROM {mtable} ORDER BY {entityCols}, {dayF}, "
                "{hourF}, {minutesF}, {secondsF}"
            ") AS w_previous_tbl "
            "WHERE previous_hour IS NOT NULL AND "
            "({hourDec} - previous_hour) < {tol} / 60.0"
        ).format(
            hourDec=hour_decimal,
            lag_entity = ", ".join([
                "LAG({cl}) OVER(PARTITION BY {ent}, {d} ORDER BY {ent}, {d}, {h}, {m}, {s}) AS prev_{cl}".format(
                    cl=c, ent=", ".join(entity_fields),
                    d=day_field, h=hour_field, m=minute_field, s=second_field
                ) for c in entity_fields]),
            entityCols=", ".join(entity_fields), dayF=day_field,
            hourF=hour_field, minutesF=minute_field, secondsF=second_field,
            mtable=table, tol=str(time_tolerance)
        )
        
        ntbl_by_query(conpsql, exclusionRows, sql, api='psql')
    
    # Get rows outside the given time tolerance
    sql = (
        "SELECT *, ({hourDec} - previous_hour) AS deltatime FROM ("
            "SELECT *, {lag_entity}, "
            "LAG({hourDec}) OVER(PARTITION BY {entityCols}, {dayF} ORDER BY "
            "{entityCols}, {dayF}, {hourF}, {minutesF}, "
            "{secondsF}) AS previous_hour "
            "FROM {mtable} ORDER BY {entityCols}, {dayF}, {hourF}, "
            "{minutesF}, {secondsF}"
        ") AS w_previous_tbl "
        "WHERE ({hourDec} - previous_hour) IS NULL OR "
        "({hourDec} - previous_hour) > {tol} / 60.0"
    ).format(
        hourDec=hour_decimal,
        lag_entity=", ".join([
            "LAG({cl}) OVER(PARTITION BY {ent}, {d} ORDER BY {ent}, {d}, {h}, {m}, {s}) AS prev_{cl}".format(
                cl=c, ent=", ".join(entity_fields), d=day_field,
                h=hour_field, m=minute_field, s=second_field
        ) for c in entity_fields]),
        entityCols=", ".join(entity_fields), dayF=day_field, hourF=hour_field,
        minutesF=minute_field, secondsF=second_field,
        mtable=table, tol=str(time_tolerance)
    )
    
    ntbl_by_query(conpsql, outresult, sql, api='psql')
    
    return outresult

