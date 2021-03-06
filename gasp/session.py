"""
Start GIS Sessions
"""


import os
import subprocess
import sys
from gasp         import exec_cmd
from gasp.oss.ops import del_folder

def start_grass_linux_newLocation(gisdb, location, srs,
                                  grassBin=None, overwrite=True):
    """
    Method to open GRASS GIS on Linux Systems
    Creates a new location
    
    Parameters:
    * gisdb - abs path to grass workspace
    * location - name for the grass location
    * srs - epsg or file to define spatial reference system of the location that 
    will be created
    """
    
    location_path = os.path.join(gisdb, location)
    
    # Delete location if exists
    if os.path.exists(location_path):
        if overwrite:
            del_folder(location_path)
        
        else:
            raise ValueError(
                'GRASS GIS 7 Location already exists'
            )
    
    grassbin = grassBin if grassBin else 'grass76'
    startcmd = grassbin + ' --config path'
    
    outcmd = exec_cmd(startcmd)
    
    gisbase = outcmd.strip('\n')
    # Set GISBASE environment variable
    os.environ['GISBASE'] = gisbase
    # the following not needed with trunk
    os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
    # add path to GRASS addons
    home = os.path.expanduser("~")
    os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')    
    # define GRASS-Python environment
    gpydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(gpydir)
    
    if type(srs) == int:
        startcmd = '{} -c epsg:{} -e {}'
    
    elif type(srs) == str or type(srs) == unicode:
        startcmd = '{} -c {} -e {}'
    
    outcmd = exec_cmd(startcmd.format(
        grassbin, str(srs), location_path
    ))
    
    # Set GISDBASE environment variable
    os.environ['GISDBASE'] = gisdb
    
    # See if there is location
    if not os.path.exists(location_path):
        raise ValueError('NoError, but location is not created')
    
    return gisbase


def start_grass_linux_existLocation(gisdb, grassBin=None):
    """
    Method to start a GRASS GIS Session on Linux Systems
    Use a existing location
    """
    
    grassbin = grassBin if grassBin else 'grass76'
    startcmd = grassbin + ' --config path'
    
    outcmd = exec_cmd(startcmd)
    
    gisbase = outcmd.strip('\n')
    # Set GISBASE environment variable
    os.environ['GISBASE'] = gisbase
    # the following not needed with trunk
    os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
    # add path to GRASS addons
    home = os.path.expanduser("~")
    os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')
    # define GRASS-Python environment
    gpydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(gpydir)
    
    # Set GISDBASE environment variable
    os.environ['GISDBASE'] = gisdb
    
    return gisbase


def start_grass_win_newLocation(gisdb, location, srs, grassBin, overwrite=True):
    """
    Method to open GRASS GIS on MS Windows Systems
    Creates a new location
    
    Parameters:
    * gisdb - abs path to grass workspace
    * location - name for the grass location
    * srs - epsg or file to define spatial reference system of the location that 
    will be created
    
    
    To work, Path to GRASS GIS must be in the PATH Environment 
    Variable
    """
    
    # define database location
    location_path = os.path.join(gisdb, location)
    
    # Delete location if exists
    if os.path.exists(location_path):
        if overwrite:
            del_folder(location_path)
        
        else:
            raise ValueError(
                'GRASS GIS 7 Location already exists'
            )
    
    # the path to grass can't have white spaces
    grassbin = grassBin if grassBin else 'grass76'
    startcmd = grassbin + ' --config path'
    outcmd = exec_cmd(startcmd)
    
    # Set GISBASE environment variable
    gisbase = outcmd.strip().split('\r\n')[0]
    os.environ['GRASS_SH'] = os.path.join(gisbase, 'msys', 'bin', 'sh.exe')
    os.environ['GISBASE'] = gisbase
    # define GRASS-Python environment
    gpydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(gpydir)
    
    # Define Command
    if type(srs) == int:
        startcmd = '{} -c epsg:{} -e {}'
    
    elif type(srs) == str:
        startcmd = '{} -c {} -e {}'
    
    # open grass
    outcmd = exec_cmd(
        startcmd.format(grassbin, str(srs), location_path
    ))
    
    # Set GISDBASE environment variable
    os.environ['GISDBASE'] = gisdb
    
    # See if there is location
    if not os.path.exists(location_path):
        raise ValueError('NoError, but location is not created')
    
    return gisbase


def start_grass_win_exisLocation(gisdb, grassBin=None):
    """
    Method to open GRASS GIS on MS Windows Systems
    Use an existing Location
    """
    
    grassbin = grassBin if grassBin else 'grass76'
    startcmd = grassBin + ' --config path'
    outcmd   = exec_cmd(startcmd)
    
    # Set GISBASE environment variable
    gisbase = outcmd.strip().split('\r\n')[0]
    os.environ['GRASS_SH'] = os.path.join(gisbase, 'msys', 'bin', 'sh.exe')
    os.environ['GISBASE'] = gisbase
    # define GRASS-Python environment
    gpydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(gpydir)
    
    # Set GISDBASE environment variable
    os.environ['GISDBASE'] = gisdb
    
    return gisbase


def run_grass(workspace, grassBIN='grass76', location=None, srs=None):
    """
    Generic method that could be used to put GRASS GIS running in any Os
    
    To work on MSWindows, Path to GRASS Must be in the PATH Environment 
    Variables
    """
    
    from gasp.oss import os_name
    
    __os = os_name()
    
    if location and srs:
        base = start_grass_linux_newLocation(
            workspace, location, srs, grassBin=grassBIN
        ) if __os == 'Linux' else start_grass_win_newLocation(
            workspace, location, srs, grassBin=grassBIN
        ) if __os == 'Windows' else None
    
    else:
        base = start_grass_linux_existLocation(
            workspace, grassBin=grassBIN
        ) if __os == 'Linux' else start_grass_win_exisLocation(
            workspace, grassBin=grassBIN
        )
    
    if not base:
        raise ValueError((
            'Could not identify operating system'
        ))
    
    return base

