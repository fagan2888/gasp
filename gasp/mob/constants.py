"""
LULC Constants
"""

def dgt_cos2007n2(c):
    return {
        1 : {
            'cls'    : ['1.1', '1.2', '1.3', '1.4'],
            'weight' : ((15 * 60.0) * c) / 1000.0
        },
        2 : {
            'cls'    : ['2.1', '2.2', '2.3', '2.4'],
            'weight' : ((30 * 60.0) * c) / 1000.0
        },
        3 : {
            'cls'    :['3.1', '3.2'],
            'weight' : ((25 * 60.0) * c) / 1000.0
        },
        4 : {
            'cls'    : ['3.3'],
            'weight' : ((20 * 60.0) * c) / 1000.0
        },
        5 : {
            'cls'    : ['4.1', '4.2'],
            'weight' : ((38 * 60.0) * c) / 1000.0
        },
        99 : {
            'cls'    : ['5.1', '5.2'],
            'weight' : 0
        }
    }

def dgt_cos2007n5(c):
    return {
        1 : {
            'cls' : ['1.1.1.01.1', '1.1.1.02.1', '1.1.1.03.1', '1.1.2.01.1',
                     '1.1.2.02.1', '1.2.1.01.1', '1.2.1.02.1', '1.2.1.03.1',
                     '1.2.1.04.1', '1.2.1.05.1', '1.2.1.06.1', '1.2.1.07.1',
                     '1.2.2.01.1', '1.2.2.02.1', '1.2.3.01.1', '1.2.3.02.1',
                     '1.2.3.03.1', '1.2.4.01.1', '1.2.4.02.1', '1.3.1.01.1',
                     '1.3.1.02.1', '1.3.2.01.1', '1.3.2.02.1', '1.3.3.01.1',
                     '1.3.3.02.1', '1.4.1.01.1', '1.4.1.02.1', '1.4.2.01.1',
                     '1.4.2.01.2', '1.4.2.02.1', '1.4.2.02.2', '1.4.2.03.1'],
            'weight' : ((15 * 60.0) * c) / 1000.0
        },
        2 : {
            'cls' : [
                '2.1.1.01.1', '2.1.1.02.1', '2.1.2.01.1', '2.1.3.01.1',
                '2.2.1.01.1', '2.2.1.02.1', '2.2.1.03.1', '2.2.2.01.1',
                '2.2.2.01.2', '2.2.2.01.3', '2.2.2.01.4', '2.2.2.01.5',
                '2.2.2.01.6', '2.2.2.02.1', '2.2.2.02.2', '2.2.2.02.3',
                '2.2.2.02.4', '2.2.2.02.5', '2.2.2.02.6', '2.2.2.03.1',
                '2.2.2.03.2', '2.2.2.03.3', '2.2.2.03.4', '2.2.2.03.5',
                '2.2.2.03.6', '2.2.3.01.1', '2.2.3.02.1', '2.2.3.03.1',
                '2.3.1.01.1', '2.4.1.01.1', '2.4.1.01.2', '2.4.1.01.3',
                '2.4.1.02.1', '2.4.1.02.2', '2.4.1.02.3', '2.4.1.03.1',
                '2.4.1.03.2', '2.4.1.03.3', '2.4.2.01.1', '2.4.3.01.1',
                '2.4.4.01.1', '2.4.4.01.2', '2.4.4.01.3', '2.4.4.01.4',
                '2.4.4.01.5', '2.4.4.01.6', '2.4.4.02.1', '2.4.4.02.2',
                '2.4.4.02.3', '2.4.4.02.4', '2.4.4.02.5', '2.4.4.02.6',
                '2.4.4.03.1', '2.4.4.03.2', '2.4.4.03.3', '2.4.4.03.4',
                '2.4.4.03.5', '2.4.4.03.6', '2.4.4.04.1', '2.4.4.04.2',
                '2.4.4.04.3', '2.4.4.04.4', '2.4.4.04.5', '2.4.4.04.6'],
            'weight' : ((30 * 60.0) * cellsize) / 1000.0
        },
        3 : {
            'cls' : ['3.1.1.01.1', '3.1.1.01.2', '3.1.1.01.3', '3.1.1.01.4',
                     '3.1.1.01.5', '3.1.1.01.6', '3.1.1.01.7', '3.1.1.02.1',
                     '3.1.1.02.2', '3.1.1.02.3', '3.1.1.02.4', '3.1.1.02.5',
                     '3.1.1.02.6', '3.1.1.02.7', '3.1.2.01.1', '3.1.2.01.2',
                     '3.1.2.01.3', '3.1.2.02.1', '3.1.2.02.2', '3.1.2.02.3',
                     '3.1.3.01.1', '3.1.3.01.2', '3.1.3.01.3', '3.1.3.01.4',
                     '3.1.3.01.5', '3.1.3.01.6', '3.1.3.01.7', '3.1.3.01.8',
                     '3.1.3.02.1', '3.1.3.02.2', '3.1.3.02.3', '3.1.3.02.4',
                     '3.2.1.01.1', '3.2.2.01.1', '3.2.2.02.1', '3.2.3.01.1',
                     '3.2.3.02.1', '3.2.4.01.1', '3.2.4.01.2', '3.2.4.01.3',
                     '3.2.4.01.4', '3.2.4.01.5', '3.2.4.01.6', '3.2.4.01.7',
                     '3.2.4.02.1', '3.2.4.02.2', '3.2.4.02.3', '3.2.4.02.4',
                     '3.2.4.02.5', '3.2.4.02.6', '3.2.4.02.7', '3.2.4.03.1',
                     '3.2.4.03.2', '3.2.4.03.3', '3.2.4.04.1', '3.2.4.04.2',
                     '3.2.4.04.3', '3.2.4.05.1', '3.2.4.05.2', '3.2.4.05.3',
                     '3.2.4.05.4', '3.2.4.05.5', '3.2.4.05.6', '3.2.4.05.7',
                     '3.2.4.05.8', '3.2.4.06.1', '3.2.4.06.2', '3.2.4.06.3',
                     '3.2.4.06.4', '3.2.4.07.1', '3.2.4.08.1', '3.2.4.08.2',
                     '3.2.4.09.1', '3.2.4.10.1'],
            'weight' : ((25 * 60.0) * cellsize) / 1000.0
        },
        4 : {
            'cls' : ['3.3.1.01.1', '3.3.1.02.1', '3.3.2.01.1', '3.3.3.01.1',
                    '3.3.4.01.1'],
            'weight' : ((20 * 60.0) * cellsize) / 1000.0
        },
        5 : {
            'cls' : [
                '4.1.1.01.1', '4.1.2.01.1', '4.2.1.01.1', '4.2.2.01.1',
                '4.2.2.02.1', '4.2.3.01.1'],
            'weight' : ((38 * 60.0) * cellsize) / 1000.0
        },
        99 : {
            'cls' : ['5.1.1.01.1', '5.1.1.02.1', '5.1.2.01.1', '5.1.2.01.2',
                     '5.1.2.02.1', '5.1.2.03.1', '5.1.2.03.2', '5.1.2.03.3',
                     '5.2.1.01.1', '5.2.2.01.1', '5.2.3.01.1'],
            'weight' : 0
        }
    }


def lulc_weight(lulc_name, cellsize):
    d = {
        'DGT_COS2007N2': dgt_cos2007n2(cellsize),
        'DGT_COS2007N5': dgt_cos2007n5(cellsize),
        'DGT_COS2010N5': dgt_cos2007n5(cellsize)
    }
    
    return d[lulc_name]


"""
SLOPE Constants
"""

def get_slope_categories():
    return {
        1 : {'base' :   0, 'top' :  10, 'rdv' :   1, 'cos' :   1},
        2 : {'base' :  10, 'top' :  30, 'rdv' :   1, 'cos' : 1.5},
        3 : {'base' :  30, 'top' :  50, 'rdv' : 1.5, 'cos' :   2},
        4 : {'base' :  50, 'top' :  70, 'rdv' : 1.5, 'cos' :   3},
        5 : {'base' :  70, 'top' : 100, 'rdv' :   2, 'cos' :   4},
        6 : {'base' : 100, 'top' : 500, 'rdv' :   2, 'cos' :   5}        
    }

