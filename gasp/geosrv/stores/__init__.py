"""
Tools for Geoserver datastores management
"""


def shape_to_store(shape, store_name, workspace, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }, protocol='http'):
    """
    Create a new datastore
    """

    import os
    import requests

    from gasp.oss import list_files

    url = (
        '{pro}://{host}:{port}/geoserver/rest/workspaces/{work}/datastores/'
        '{store}/file.shp'
        ).format(
            host=conf['HOST'], port=conf['PORT'], work=workspace,
            store=store_name, pro=protocol
        )

    if os.path.splitext(shape)[1] != '.zip':
        from gasp import zip_files

        shapefiles = list_files(
            os.path.dirname(shape),
            filename=os.path.splitext(os.path.basename(shape))[0]
        )

        shape = os.path.splitext(shape)[0] + '.zip'
        zip_files(shapefiles, shape)

    with open(shape, 'rb') as f:
        r = requests.put(
            url,
            data=f,
            headers={'content-type': 'application/zip'},
            auth=(conf['USER'], conf['PASSWORD'])
        )

        return r


def import_datafolder(path_folder, store_name, workspace, conf={
        'USER':'admin', 'PASSWORD': 'geoserver',
        'HOST':'localhost', 'PORT': '8888'
    }, protocol='http'):
    """
    Import all shapefiles in a directory to a GeoServer Store
    """

    import requests

    url = (
        '{pro}://{host}:{port}/geoserver/rest/workspaces/{work}/datastores/'
        '{store}/external.shp?configure=all'
        ).format(
            host=conf['HOST'], port=conf['PORT'], work=workspace,
            store=store_name, pro=protocol
        )

    r = requests.put(
        url,
        data='file://' + path_folder,
        headers={'content-type': 'text/plain'},
        auth=(conf['USER'], conf['PASSWORD'])
    )

    return r


def list_stores(workspace, conf={
        'USER': 'admin', 'PASSWORD': 'geoserver',
        'HOST': 'localhost', 'PORT': '8888'
    }, protocol='http'):
    """
    List all stores in a Workspace
    """
    
    import requests
    import json
    
    url = '{pro}://{host}:{port}/geoserver/rest/workspaces/{work}/datastores'.format(
        host=conf['HOST'], port=conf['PORT'], work=workspace, pro=protocol
    )
    
    r = requests.get(
        url, headers={'Accept': 'application/json'},
        auth=(conf['USER'], conf['PASSWORD'])
    )
    
    ds = r.json()
    if 'dataStore' in ds['dataStores']:
        return [__ds['name'] for __ds in ds['dataStores']['dataStore']]
    else:
        return []


def del_store(workspace, name, conf={
        'USER': 'admin', 'PASSWORD': 'geoserver',
        'HOST': 'localhost', 'PORT': '8888'
    }, protocol='http'):
    """
    Delete an existing Geoserver datastore
    """
    
    import requests
    import json
    
    url = (
        '{pro}://{host}:{port}/geoserver/rest/workspaces/{work}/'
        'datastores/{ds}?recurse=true'
    ).format(
        host=conf['HOST'], port=conf['PORT'], work=workspace, ds=name,
        pro=protocol
    )
    
    r = requests.delete(url, auth=(conf['USER'], conf['PASSWORD']))
    
    return r


def add_raster_store(raster, store_name, workspace, conf={
        'USER': 'admin', 'PASSWORD': 'geoserver',
        'HOST': 'localhost', 'PORT': '8888'
    }, protocol='http'):
    """
    Create a new store with a raster layer
    """
    
    import os
    import requests
    
    from gasp.oss.ops import del_file
    from gasp.Xml     import write_xml_tree
    
    url = (
        '{pro}://{host}:{port}/geoserver/rest/workspaces/{work}/'
        'coveragestores?configure=all'
    ).format(
        host=conf['HOST'], port=conf['PORT'],
        work=workspace, pro=protocol
    )
    
    # Create obj with data to be written in the xml
    xmlTree = {
        "coverageStore" : {
            "name"   : store_name,
            "workspace": workspace,
            "enabled": "true",
            "type"   : "GeoTIFF",
            "url"    : raster
        }
    }
    
    treeOrder = {
        "coverageStore" : ["name", "workspace", "enabled", "type", "url"]
    }
    
    # Write XML
    xml_file = write_xml_tree(
        xmlTree,
        os.path.join(os.path.dirname(raster), 'new_store.xml'),
        nodes_order=treeOrder
    )
    
    # Send request
    with open(xml_file, 'rb') as f:
        r = requests.post(
            url,
            data=f,
            headers={'content-type': 'text/xml'},
            auth=(conf['USER'], conf['PASSWORD'])
        )
    
    del_file(xml_file)
        
    return r
