import os
import re
import datetime

from django.apps import apps

from django.contrib.gis.gdal import DataSource, OGRGeometry, OGRGeomType
from django.contrib.gis.gdal.error import GDALException


def remove_z(wkt):
    ''' Remove Z dimension from WKT. '''
    z_search = r'([-\d\.]+) ([-\d\.]+) ([-\d\.]+)'
    return re.sub(z_search, r'\1 \2', wkt)

def gather_all_attributes(field_list, feat):
    ''' Go through each of the attributes in the shapefile, create a JSON object of them all, then put in a single kitchen-sink attribute on the matching Django instance. '''

    data = {}
    for field in field_list:
        data[field] = feat.get(field)
        if type(data[field]) in [datetime.date, datetime.datetime]:
            try:
                data[field] = data[field].strftime('%Y-%m-%d')
            except:
                data[field] = data[field].isoformat()

    return data

def build_mapping(config, required_attrs:list):
    ''' Construct a layermapping-ready mapping from the CSV'''
    mapping = {}
    for attr in required_attrs:
    # for attr in ["pin_primary", "pin_secondary", "street_address", "city",
    #              "state", "zip_code", "county_name", "county_fips", "plat_name",
    #              "block", "lot", "join_description", "phys_description",
    #              "township", "range", "section"]:
        if config[attr] != '':
            mapping.update({attr: config[attr]})
    return mapping

def save_multipoly_instances(workflow, model, shp_path, shp_mapping, required_attrs):
    objs = []
    obj_count = 0

    orig_filename = os.path.basename(shp_path)
    ds = DataSource(shp_path)
    layer = ds[0]
    mapping = build_mapping(shp_mapping, required_attrs)

    for feat in layer:
        try:

            # Freaky 3D geometries -- this seems harder than it should be.
            if layer.geom_type == 'POLYGON25D':
                safe_geom = OGRGeometry(
                    remove_z(feat.geom.wkt), layer.srs)
            else:
                safe_geom = feat.geom

            # force to multi
            # print(layer.srs)
            multipoly = OGRGeometry(OGRGeomType('MultiPolygon'), layer.srs)
            multipoly.add(safe_geom)

            # Translate to 4326, even if it probably already is.
            multipoly_4326 = multipoly.transform(4326, clone=True)
            # multipoly_utm = multipoly.transform(26915, clone=True)

            all_attributes = gather_all_attributes(layer.fields, feat)

            kwargs = {}
            for k, v in mapping.items():
                # Check for static values
                if type(v) is tuple:
                    kwargs[k] = v[1]
                else:
                    kwargs[k] = all_attributes[v]
            # kwargs = {k: all_attributes[v] for k, v in mapping.items()}

            kwargs.update({
                'workflow_id': workflow.id,
                'feature_id': feat.fid,
                'orig_data': all_attributes,
                'orig_filename': orig_filename,
                'geom_4326': multipoly_4326.wkt,
                # 'geom_utm': multipoly_utm.wkt,
            })

            objs.append(model(**kwargs))
            obj_count += 1

            if obj_count % 10000 == 0:
                model.objects.bulk_create(objs)
                print(f'Saved {obj_count} {model._meta.model_name} records...')
                objs = []

        except GDALException as e:
            pass

    model.objects.bulk_create(objs)
    print(f'Saved {obj_count} {model._meta.model_name} records.')
