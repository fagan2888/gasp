"""
Split table methods
"""

def split_table_by_range(conP, table, row_number):
    """
    Split tables in several
    """
    
    from gasp.sql.mng.fld import cols_name
    from gasp.sql.mng.tbl import row_num
    from gasp.sql.mng.qw  import ntbl_by_query
    
    rowsN = row_num(conP, table, api='psql')
    
    nrTables = int(rowsN / float(row_number)) + 1
    
    COLS = cols_name(conP, table)
    
    offset = 0
    for i in range(nrTables):
        ntbl_by_query(
            conP, '{}_{}'.format(table, str(i)),
            "SELECT * FROM {} ORDER BY {} OFFSET {} LIMIT {} ;".format(
                table, ', '.join(COLS), str(offset), str(row_number) 
            ), api='psql'
        )
        
        offset += row_number


def split_table_entity_number(conP, table, entity_field, entity_number):
    """
    Split tables in several using as reference a number of entities per table
    
    If a table has 1 000 000 entities and the entity_number is 250 000,
    this method will create four tables, each one with 250 000 entities.
    250 000 entities, not rows. Don't forget that the main table may have
    more than one reference to the same entity.
    """
    
    import pandas
    from gasp.fm.sql      import query_to_df
    from gasp.sql.mng.fld import get_columns_type
    from gasp.sql.mng.qw  import ntbl_by_query
    
    # Select entities in table
    entities = query_to_df(conP, "SELECT {c} FROM {t} GROUP BY {c}".format(
        c=entity_field, t=table
    ), db_api='psql')
    
    # Split entities into groups acoording entity_number
    entityGroup = []
    
    lower = 0
    high = entity_number
    while lower <= len(entities.index):
        if high > len(entities.index):
            high = len(entities.index)
        
        entityGroup.append(entities.iloc[lower : high])
        
        lower += entity_number
        high  += entity_number
    
    # For each dataframe, create a new table
    COLS_TYPE = get_columns_type(conP, table)
    
    c = 0
    for df in entityGroup:
        if COLS_TYPE[entity_field] != str:
            df[entity_field] = '{}='.format(entity_field) + df[entity_field].astype(str)
        else:
            df[entity_field] = '{}=\''.format(entity_field) + df[entity_field].astype(str) + '\''
        
        whr = ' OR '.join(df[entity_field])
        
        ntbl_by_query(conP, '{}_{}'.format(table, str(c)), (
            "SELECT * FROM {} WHERE {}"
        ).format(table, whr), api='psql')
        
        c += 1


def split_table_by_col_distinct(conParam, pgtable, column):
    """
    Create a new table for each value in one column
    """
    
    from gasp.fm.sql      import query_to_df
    from gasp.sql.mng.fld import get_columns_type
    from gasp.sql.mng.qw  import ntbl_by_query
    
    fields_types = get_columns_type(conParam, pgtable)
    
    # Get unique values
    VALUES = query_to_df(
        conParam,
        "SELECT {col} FROM {t} GROUP BY {col}".format(
            col=interest_column, t=pgtable
        ), db_api='psql'
    )[interest_column].tolist()
    
    whr = '{}=\'{}\'' if fields_types[interest_column] == str else '{}={}'
    
    for row in VALUES:
        ntbl_by_query(
            conParam, '{}_{}'.format(pgtable, str(row[0])),
            "SELECT * FROM {} WHERE {}".format(
                pgtable, whr.format(interest_column, str(row[0]))
        ), api='psql')

