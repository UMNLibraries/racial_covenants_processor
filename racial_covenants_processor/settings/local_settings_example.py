DEBUG = True
DEBUG_TOOLBAR_ON = True

INTERNAL_IPS = [
    "127.0.0.1",
]

PUBLIC_URL_ROOT = "https://deed-machine.mappingprejudice.umn.edu/"

# GDAL_LIBRARY_PATH = '/opt/homebrew/opt/gdal/lib/libgdal.dylib'
# GEOS_LIBRARY_PATH = '/opt/homebrew/opt/geos/lib/libgeos_c.dylib'


if DEBUG_TOOLBAR_ON:
    MIDDLEWARE = [
        "racial_covenants_processor.middleware.HealthCheckMiddleware",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]

    INSTALLED_APPS = [
        "apps.deed",
        "apps.zoon",
        "apps.parcel",
        "apps.plat",
        # 'apps.deedstat',
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.gis",
        "django.contrib.humanize",
        "haystack",
        # 'compressor',
        "rangefilter",
        "storages",
        "localflavor",
        "rest_framework",
        "rest_framework_gis",
        "django_filters",
        # 'django_extensions',
        "debug_toolbar",
    ]

ZOONIVERSE_QUESTION_LOOKUP = {
    "DC Washington DC": {
        "panoptes_folder": "dc-washington-dc",
        "zoon_workflow_id": 27339,
        "zoon_workflow_version": "1.23",
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/(?P<batch_id>[a-z_\d]+)/.+/(?P<doc_num>\d{6,20})(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        # 'merge_fields': {
        #     'doc_num': {'fields': ['doc_date_year', 'doc_date_month', 'doc_date_day', 'daily_doc_num'], 'separator': '', 'replace_nulls': False}
        # },  # Build field from components in regex
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Washington DC",
                "local_shp": "/Users/mcorey/Documents/Deed projects/dc/modern_gis/mp-dc-parcels-modified/mp-dc-parcels-modified.shp",
                "mapping": {
                    "pin_primary": "SSL",
                    "pin_secondary": ("static", None),
                    "street_address": "addr_full",
                    "city": (
                        "static",
                        "District of Columbia",
                    ),  # modified to filter out "city of "
                    "state": ("static", "DC"),  # set static value for all features
                    "zip_code": ("static", None),
                    "county_name": ("static", "District of Columbia"),
                    "county_fips": ("static", "11000"),
                    "plat_name": ("static", "DC"),
                    "block": "block",
                    "lot": "LOT",
                    "join_description": "SSL",
                    "phys_description": "SSL",
                    "township": ("static", None),
                    "range": ("static", None),
                    "section": ("static", None),
                },
            }
        ],
        # 'subdivision_shps': [{
        #     'id': 'subdivision_main',
        #     'description': 'Main Subdivision shapefile for Washington County',
        #     # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
        #     # If your zip includes a bunch of shapefiles, which one do you actually want?
        #     # 'file_prefix': 'plan_attributedparcelpoly',
        #     'local_shp': '/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-washington-county/WC_Plats_051724/WC_Plats_051724.shp',
        #     'mapping': {
        #         'feature_id': 'PLAT_ID',
        #         'name': 'PLAT_NAME',
        #         'doc_num': ('static', None),
        #         'recorded_date': 'RECORDED',
        #     }
        # }],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "MA South Essex County": {
        "panoptes_folder": "ma-south-essex-county",
        "zoon_workflow_id": 18123,
        "zoon_workflow_version": "7.43",
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T18"],
            # 'doc_num': '???',
            # 'bool_handwritten': 'T14',
            "bool_covenant": "T0",
            "covenant_text": "T2",
            # 'addition': 'T6',
            # 'lot': 'T4',
            # 'block': 'T5',
            "city": "T10",
            "seller": "T11",
            # 'buyer': 'T9',
            # 'match_type': 'T3',
            # 'misc_info': 'T1',
            "deed_date": {
                "root_q": "T18",
                "year": "T15",
                "month": "T16",
                "day": "T17",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "MN Anoka County": {
        "panoptes_folder": "mn-anoka-county",
        "zoon_workflow_id": 25091,
        "zoon_workflow_version": "1.18",
        # 'deed_image_glob_root': 'D:/deed_images/mn/anoka',
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/(?P<batch_id>\d+)/(?P<doc_alt_id>\d+)(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        "deed_supplemental_info": [
            {
                "data_csv": "/Users/mcorey/Documents/Deed projects/mn/anoka/supplemental data/anoka_supplemental_20230804.csv",
                "join_fields_deed": ["orig_file_lookup"],
                "join_fields_supp": ["orig_file_lookup"],
                "mapping": {"doc_num": "doc_num_expanded", "doc_type": "doc_type"},
            }
        ],
        "subdivision_shps": [
            {
                "id": "subdivision_main",
                "description": "Main Subdivision shapefile for Anoka County",
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-anoka-county/Plat_Boundaries_REPAIRED/Plat_Boundaries_REPAIRED.shp",
                "mapping": {
                    "feature_id": "MAP_NUMBER",
                    "name": "PLAT",
                    "doc_num": "DOC_NUMBER",
                    "recorded_date": ("static", None),
                },
            }
        ],
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Anoka County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-anoka-county/mn_anoka_parcels_modified_valid/mn_anoka_parcels_modified_valid.shp",
                "mapping": {
                    "pin_primary": "PIN",
                    "pin_secondary": ("static", None),
                    "street_address": "LOC_ADDR",
                    "city": "ACT_CITY",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "LOC_ZIP",
                    "county_name": ("static", "Anoka"),
                    "county_fips": ("static", "27003"),
                    "plat_name": "PLAT",
                    "block": "block_man",
                    "lot": "lot_man",
                    "join_description": "Full Legal",
                    "phys_description": "Full Legal",
                    "township": "TOWNSHIP",
                    "range": "RANGE",
                    "section": "SECTION",
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "MN Cass County": {  # Manual covenants only
        # 'panoptes_folder': 'mn-cass-county',
        # 'zoon_workflow_id': None,
        # 'zoon_workflow_version': '',
        # 'deed_image_glob_root': 'D:/deed_images/mn/cass',
        # 'deed_image_regex': r'',
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Cass County",
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-cass-county/parcels_mn_cass__from_statewide__reprocessed/parcels_mn_cass__from_statewide__reprocessed.shp",
                "mapping": {
                    "pin_primary": "county_pin",
                    "pin_secondary": "state_pin",
                    "street_address": "addr_mp",
                    "city": "postcomm",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "zip",
                    "county_name": ("static", "Cass"),
                    "county_fips": ("static", "27021"),
                    "plat_name": "plat_name",
                    "block": "blk_regex",
                    "lot": "lot_regex",
                    "join_description": "abb_legal",
                    "phys_description": "abb_legal",
                    "township": "township",
                    "range": "range_",
                    "section": "section",
                },
            }
        ],
    },
    "MN Crow Wing County": {  # Manual covenants only
        # 'panoptes_folder': 'mn-crow-wing-county',
        # 'zoon_workflow_id': None,
        # 'zoon_workflow_version': '',
        # 'deed_image_glob_root': 'D:/deed_images/mn/crow-wing',
        # 'deed_image_regex': r'',
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Crow Wing County",
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-crow-wing-county/parcels_mn_crow_wing__from_statewide__reprocessed/parcels_mn_crow_wing__from_statewide__reprocessed.shp",
                "mapping": {
                    "pin_primary": "county_pin",
                    "pin_secondary": "state_pin",
                    "street_address": "addr_mp",
                    "city": "postcomm",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "zip",
                    "county_name": ("static", "Crow Wing"),
                    "county_fips": ("static", "27035"),
                    "plat_name": "plat_name",
                    "block": "blk_regex",
                    "lot": "lot_regex",
                    "join_description": "abb_legal",
                    "phys_description": "abb_legal",
                    "township": "township",
                    "range": "range_",
                    "section": "section",
                },
            }
        ],
    },
    "MN Dakota County": {
        "panoptes_folder": "mn-dakota-county",
        "zoon_workflow_id": 23473,
        "zoon_workflow_version": "3.90",
        "deed_image_glob_root": "D:/deed_images/mn/dakota",
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/(?P<batch_id>[^/]+)/(?P<doc_type>[^/]+)/doc_(?P<doc_alt_id>[A-z\-\d]+)_book_(?P<book_id>[A-z\d]+)_page_(?P<page_num>[A-Z\d]+)(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        "deed_supplemental_info": [
            {
                "data_csv": "/Users/mcorey/Documents/Deed projects/mn/dakota/dakota_doc_num_creation_20230119.csv",
                "join_fields_deed": ["s3_lookup"],
                "join_fields_supp": ["s3_lookup"],
                "mapping": {"doc_num": "doc_num"},
            }
        ],
        "subdivision_shps": [
            {
                "id": "subdivision_main",
                "description": "Main Subdivision shapefile for Dakota County",
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-dakota-county/shp_plan_propertysubdivisions/PROPERTYINFO_Subdivisions.shp",
                "mapping": {
                    "feature_id": "PLATID",
                    "name": "PLATNAME",
                    "doc_num": "PLATBOOKPA",
                    "recorded_date": "RECORDEDDA",
                },
            }
        ],
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Dakota County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-dakota-county/DAK_Parcel_Data_ENHANCED/DAK_Parcel_Data_ENHANCED.shp",
                "mapping": {
                    "pin_primary": "TAXPIN",
                    "pin_secondary": ("static", None),
                    "street_address": "SITEADDRES",
                    "city": "MUNICIPALI",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": ("static", None),
                    "county_name": ("static", "Dakota"),
                    "county_fips": ("static", "27037"),
                    "plat_name": "Plat",
                    "block": "blk_parsed",
                    "lot": "lot_parsed",
                    "join_description": "LotBlk",
                    "phys_description": "Legal",
                    "township": (
                        "static",
                        None,
                    ),  # These can be parsed, just not doing it right now
                    "range": ("static", None),
                    "section": ("static", None),
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            # 'doc_num': '???',
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "MN Olmsted County": {
        "panoptes_folder": "mn-olmsted-county",
        "zoon_workflow_id": 26130,
        "zoon_workflow_version": "1.27",
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/OlmstedCounty(?P<doc_type>[A-Za-z]+)/(?P<batch_id>[A-Za-z]+)/?(?P<book_id>[A-Za-z\-\d]+)?/(?P<doc_num>[A-Z\d\.]+)(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Olmsted County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-olmsted-county/mn-olmsted-county-parcel/mn-olmsted-county-parcel-modified.shp",
                "mapping": {
                    "pin_primary": "PARID",
                    "pin_secondary": "PIN",
                    "street_address": "address_mp",  # modified by concatting
                    "city": "SiteCity",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "SiteZip5",
                    "county_name": ("static", "Olmsted"),
                    "county_fips": ("static", "27109"),
                    "plat_name": "PlatName",
                    "block": "Block",
                    "lot": "Lot",
                    "join_description": ("static", None),
                    "phys_description": ("static", None),
                    "township": ("static", None),
                    "range": ("static", None),
                    "section": ("static", None),
                },
            }
        ],
        "subdivision_shps": [
            {
                "id": "subdivision_main",
                "description": "Main Subdivision shapefile for Olmsted County",
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-olmsted-county/mn-olmsted-subdivision-modified/mn-olmsted-subdivision-modified.shp",
                "mapping": {
                    "feature_id": "PLATNO",
                    "name": "PLATNAME",
                    "doc_num": "FILENAME",
                    "recorded_date": "platdt_mp",
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "MN Ramsey County": {  # This is the new Ramsey County version
        "panoptes_folder": "mn-ramsey-county",
        "zoon_workflow_id": 29289,
        "zoon_workflow_version": "1.1",  # FAKE
        # 'zoon_workflow_id': XXXXX,
        # 'zoon_workflow_version': 'X.XX',
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/(?P<batch_id>[A-za-z \d]+)/(?P<doc_alt_id>\d+)(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        # 'term_exceptions': {' white': ['whitefish']},
        "plat_regex": r"(?P<gov_id>[\dA-z]+).pdf",
        "plat_raw_glob": "/Users/mcorey/Documents/Deed projects/mn/ramsey",
        # For cases where the filename won't help you much
        "plat_manifest": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/ramsey-county_raw_plat_manifest.csv",
        "deed_supplemental_info": [
            {
                "data_csv": "/Users/mcorey/Documents/Deed projects/mn/ramsey/ramsey_recorder_supplemental_info/Abstract_20191106_header.csv",
                "join_fields_deed": ["doc_alt_id"],
                "join_fields_supp": ["itemnum"],
                "mapping": {"doc_num": "mp_doc_num", "doc_type": "landtype"},
            },
            {
                "data_csv": "/Users/mcorey/Documents/Deed projects/mn/ramsey/ramsey_recorder_supplemental_info/Torrens_20191106_header.csv",
                "join_field_deed": ["doc_alt_id"],
                "join_field_supp": ["itemnum"],
                "mapping": {"doc_num": "mp_doc_num", "doc_type": "landtype"},
            },
        ],
        "deed_manual_exceptions": [
            {
                "data_csv": "/Users/mcorey/Documents/Deed projects/mn/ramsey/mn_ramsey_notebooks/data/mp-mn-ramsey-already-classified-docs-to-exempt-20250701.csv",
                "field": "s3_lookup",
            }
        ],
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Ramsey County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-ramsey-county/mn_ramsey_parcels_repaired_4326/mn_ramsey_parcels_repaired_4326.shp",
                "mapping": {
                    "pin_primary": "ParcelID",
                    "pin_secondary": ("static", None),
                    "street_address": "SiteAddres",
                    "city": "SiteCityNa",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "SiteZIP5",
                    "county_name": ("static", "Ramsey"),
                    "county_fips": ("static", "27123"),
                    "plat_name": "PlatName",
                    "block": "Block",
                    "lot": "Lot",
                    "join_description": "TaxDescrip",
                    "phys_description": "TaxDescrip",
                    "township": "Township",
                    "range": "Range",
                    "section": "Section",
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "MN Sherburne County": {
        "panoptes_folder": "mn-sherburne-county",
        "zoon_workflow_id": 27591,
        "zoon_workflow_version": "1.1",
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/(?:(?P<batch_id>(?<=mn-sherburne-county/)[A-Za-z\d _]+)/)?(?:.+/)?(?P<doc_type>[A-Za-z]+)(?: Book )?(?P<book_id>(?<=Book )[A-Z\d]+)?[A-z -]+(?P<doc_num>(?<!_page_)(?<!_SPLITPAGE_)\d+)?(?:_page_)?(?P<page_num>(?<=_page_)\d+)?(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        # 'plat_regex': r'(?P<gov_id>[\dA-z]+).pdf',
        # 'plat_raw_glob': '/Users/mcorey/Documents/Deed projects/mn/ramsey',
        # For cases where the filename won't help you much
        # 'plat_manifest': '/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/ramsey-county_raw_plat_manifest.csv',
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Sherburne County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                "file_prefix": "plan_attributedparcelpoly",
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-sherburne-county/mn_sherburne_county_parcels_modified_plus_phys/mn_sherburne_county_parcels_modified_plus_phys.shp",
                "mapping": {
                    "pin_primary": "PIN",
                    "pin_secondary": "OBJECTID",
                    "street_address": "mp_st_add",
                    "city": "CITY_MAIL",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "ZIP",
                    "county_name": ("static", "Sherburne"),
                    "county_fips": ("static", "27141"),
                    "plat_name": "PLAT_NAME",
                    "block": "BLOCK",
                    "lot": "LOT",
                    "join_description": "mp_prp_dsc",
                    "phys_description": "mp_prp_dsc",
                    "township": "TOWNSHIP",
                    "range": "RANGE",
                    "section": "SECTION_",
                },
            }
        ],
        "subdivision_shps": [
            {
                "id": "subdivision_main",
                "description": "Main Subdivision shapefile for Sherburne County",
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-sherburne-county/mn_sherburne_county_subdivisions/mn_sherburne_county_subdivisions.shp",
                "mapping": {
                    "feature_id": "PLAT_ID",
                    "name": "LEGAL_NAME",
                    "doc_num": "DOC_NUM",
                    "recorded_date": "DATE_REC",
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "MN Washington County": {
        "panoptes_folder": "mn-washington-county",
        "zoon_workflow_id": 26200,
        "zoon_workflow_version": "1.1",
        # 'deed_image_glob_root': 'D:/deed_images/mn/washington',
        # 'deed_image_glob_root': '/Users/mcorey/Documents/Deed projects/wi/milwaukee/test_deed_images/Milwaukee_Raw',
        # 'deed_image_glob_remainder': '**/*.tif',
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/(?P<batch_id>(?<=mn-washington-county/)[A-Za-z _\-\d]+)/\d{4}/(?P<doc_date_year>\d{4})_(?P<doc_date_month>\d{2})_(?P<doc_date_day>\d{2})_(?P<doc_type>[A-Z])_(?P<doc_num>.+)_(?P<book_id>(?:NONE_NONE)|(?:[A-Z]+_[A-Z\d]+))_(?P<page_num>(?:NONE)|\d+)_(?P<doc_alt_id>\d+)(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        "merge_fields": {
            "doc_num": {
                "fields": ["doc_type", "doc_num"],
                "separator": "",
                "replace_nulls": False,
            }
        },  # Build field from components in regex
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Washington County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-washington-county/mn_washington_parcel__reprocessed/mn_washington_parcel__reprocessed.shp",
                "mapping": {
                    "pin_primary": "PIN",
                    "pin_secondary": "TAXPIN",
                    "street_address": "address_mp",  # modified by concatting
                    "city": "city_mp",  # modified to filter out "city of "
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "ZIP",
                    "county_name": ("static", "Washington"),
                    "county_fips": ("static", "27163"),
                    "plat_name": "plat_final",
                    "block": "blk_final",
                    "lot": "lot_final",
                    "join_description": "TAXDESCRIP",
                    "phys_description": "TAXDESCRIP",
                    "township": ("static", None),
                    "range": ("static", None),
                    "section": ("static", None),
                },
            }
        ],
        "subdivision_shps": [
            {
                "id": "subdivision_main",
                "description": "Main Subdivision shapefile for Washington County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/mn-washington-county/WC_Plats_051724/WC_Plats_051724.shp",
                "mapping": {
                    "feature_id": "PLAT_ID",
                    "name": "PLAT_NAME",
                    "doc_num": ("static", None),
                    "recorded_date": "RECORDED",
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "NC Forsyth County": {
        "panoptes_folder": "nc-forsyth-county",
        "zoon_workflow_id": 27669,
        "zoon_workflow_version": "10.26",
        "deed_image_regex": r"/(?P<workflow_slug>[A-z\-]+)/(?P<doc_type>[a-z_\d]+)/(?:t/)?(?P<book_id>[a-z\d]+)/\d+(?P<page_num>(?:(?<=\d{2})\d{4}(?=[\._\-]))|(?:(?<=\d{4})\d{4}(?=[\._\-])))(?:.*?_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?",
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Forsyth County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/nc-forsyth-county/nc-forsyth-county-parcels/Parcels.shp",
                "mapping": {
                    "pin_primary": "TAXPIN",
                    "pin_secondary": "BLKCNTRL",
                    "street_address": "PROPERTYAD",
                    "city": ("static", None),
                    "state": ("static", "NC"),  # set static value for all features
                    "zip_code": ("static", None),
                    "county_name": ("static", "Forsyth"),
                    "county_fips": ("static", "37067"),
                    "plat_name": ("static", "No plat"),
                    "block": "PINBLK",
                    "lot": "PINLOT",
                    "join_description": ("static", None),
                    "phys_description": ("static", None),
                    "township": ("static", None),
                    "range": ("static", None),
                    "section": ("static", None),
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T15", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "map_book": "T16",
            "map_book_page": "T17",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "WI Milwaukee County": {
        "panoptes_folder": "wi-milwaukee-county",  # relative to data/aggregation folder
        "zoon_workflow_id": 22139,
        "zoon_workflow_version": "69.262",
        # 'deed_image_raw_glob': 'D:/Milwaukee_Books/Images/**/*.tif',
        "deed_image_glob_root": "/Users/mcorey/Documents/Deed projects/wi/milwaukee/test_deed_images/Milwaukee_Raw",
        "deed_image_glob_remainder": "**/*.tif",
        # 'deed_image_raw_glob': '/Users/mcorey/Documents/Deed projects/wi/milwaukee/test_deed_images/Milwaukee_Raw/**/*.tif',
        "deed_image_regex": r"\/(?P<workflow_slug>[A-z\-]+)\/(?P<doc_date_year>\d{4})(?P<doc_date_month>\d{2})(?P<doc_date_day>\d{2})\/(?P<doc_num>[A-Z\d]+)_(?P<doc_type>[A-Z]+)_(?P<page_num>\d+)",
        # 'term_exceptions': {' white': ['whitefish']}
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T7", "T13"],
            "bool_handwritten": "T14",
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T6",
            "lot": "T4",
            "block": "T5",
            "seller": "T8",
            "buyer": "T9",
            "match_type": "T3",
            "misc_info": "T1",
            "deed_date": {
                "root_q": "T13",
                "year": "T12",
                "month": "T11",
                "day": "T10",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Milwaukee County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/wi-milwaukee-county/milwaukee_county_parcels__reprocessed/milwaukee_county_parcels__reprocessed.shp",
                "mapping": {
                    "pin_primary": "PARCEL_KEY",
                    "pin_secondary": "TAXKEY",
                    "street_address": "ADDRESS",
                    "city": "MUNINAME",
                    "state": ("static", "WI"),  # set static value for all features
                    "zip_code": ("static", None),
                    "county_name": ("static", "Milwaukee"),
                    "county_fips": ("static", "55079"),
                    "plat_name": "addition",
                    "block": "block",
                    "lot": "lot",
                    "join_description": "LEGALDESCR",
                    "phys_description": "LEGALDESCR",
                    "township": ("static", None),
                    "range": ("static", None),
                    "section": ("static", None),
                },
            }
        ],
        "subdivision_shps": [
            {
                "id": "subdivision_main",
                "description": "Main Subdivision shapefile for Milwaukee County",
                # 'download_url': 'https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip',
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                # 'file_prefix': 'plan_attributedparcelpoly',
                "local_shp": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/shp/wi-milwaukee-county/Subdivision/Subdivision.shp",
                "mapping": {
                    "feature_id": "ObjectID",
                    "name": "Name",
                    "doc_num": "DocNo",
                    "recorded_date": "DateRec",
                },
            }
        ],
    },
    "Ramsey County (deprecated)": {  # Legacy Ramsey County
        "panoptes_folder": "mn_ramsey",  # relative to data/aggregation folder
        "zoon_workflow_id": 13143,
        "config_yaml": "Extractor_config_workflow_13143_V4.10.yaml",
        "deed_image_regex": r"\/(?P<workflow_slug>[A-z\-]+)\/(?P<doc_alt_id>\d+)(?:_page_(?P<page_num>\d+))?(?P<bool_match>_match)?",
        "deed_image_raw_glob": "/Volumes/MappingPrejudice/MappingPrejudice/MP_Ramsey_County_Deeds/Raw_Deed_Imgs/**/*.tif",
        "plat_regex": r"(?P<gov_id>[\dA-z]+).pdf",
        "plat_raw_glob": "/Users/mcorey/Documents/Deed projects/mn/ramsey",
        # For cases where the filename won't help you much
        "plat_manifest": "/Users/mcorey/Documents/code/racial_covenants_processor/racial_covenants_processor/data/ramsey-county_raw_plat_manifest.csv",
        "deed_supplemental_info": [
            {
                "data_csv": "/Users/mcorey/Documents/Deed projects/mn/ramsey/ramsey_recorder_supplemental_info/Abstract_20191106_header.csv",
                "join_fields_deed": ["doc_alt_id"],
                "join_fields_supp": ["itemnum"],
                "mapping": {"doc_num": "docnum", "doc_type": "landtype"},
            },
            {
                "data_csv": "/Users/mcorey/Documents/Deed projects/mn/ramsey/ramsey_recorder_supplemental_info/Torrens_20191106_header.csv",
                "join_fields_deed": ["doc_alt_id"],
                "join_fields_supp": ["itemnum"],
                "mapping": {"doc_num": "docnum", "doc_type": "landtype"},
            },
        ],
        "parcel_shps": [
            {
                "id": "parcel_main",
                "description": "Main parcel shapefile for Ramsey County",
                "download_url": "https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_co_ramsey/plan_parcel_data/shp_plan_parcel_data.zip",
                # If your zip includes a bunch of shapefiles, which one do you actually want?
                "file_prefix": "plan_attributedparcelpoly",
                "mapping": {
                    "pin_primary": "ParcelID",
                    # 'pin_secondary': 'ParcelID',
                    "street_address": "SiteAddres",
                    "city": "SiteCityNa",
                    "state": ("static", "MN"),  # set static value for all features
                    "zip_code": "SiteZIP5",
                    "county_name": ("static", "Ramsey"),
                    "county_fips": ("static", "27123"),
                    "plat_name": "PlatName",
                    "block": "Block",
                    "lot": "Lot",
                    "join_description": "TaxDescrip",
                    "phys_description": "TaxDescrip",
                    "township": "Township",
                    "range": "Range",
                    "section": "Section",
                },
            }
        ],
        "zooniverse_config": {
            "num_to_retire": 5,
            "combo_task_ids": ["T18"],  # Untested
            "bool_covenant": "T0",
            "covenant_text": "T2",
            "addition": "T9",
            "lot": "T5",
            "block": "T7",
            "seller": None,
            "buyer": None,
            "match_type": None,
            "deed_date": {
                "root_q": "T18",
                "year": "T15",
                "month": "T16",
                "day": "T17",
            },
            "month_lookup": {
                "1 - January": 1,
                "2 - February": 2,
                "3 - March": 3,
                "4 - April": 4,
                "5 - May": 5,
                "6 - June": 6,
                "7 - July": 7,
                "8 - August": 8,
                "9 - September": 9,
                "10 - October": 10,
                "11 - November": 11,
                "12 - December": 12,
            },
        },
    },
    "Test workflow": {
        "zoon_workflow_id": 1234,
        "zoon_workflow_version": "1",
    },
}

# aws settings
AWS_ACCESS_KEY_ID = "XXXX"
AWS_SECRET_ACCESS_KEY = "XXXX"
AWS_STORAGE_BUCKET_NAME = "covenants-deed-images"
AWS_S3_REGION_NAME = "us-east-2"  # change to your region
AWS_S3_SIGNATURE_VERSION = "s3v4"
# AWS_DEFAULT_ACL = 'public-read'
AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
# s3 static settings
AWS_LOCATION = "racial-covenants-processor/static"
# AWS_LOCATION = 'static'
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"

# STATICFILES_STORAGE = 'racial_covenants_processor.storage_backends.StaticStorage'  # Deprecated
# DEFAULT_FILE_STORAGE = 'racial_covenants_processor.storage_backends.PublicMediaStorage'  # Deprecated
# STORAGES = {
#     "default": {
#         "BACKEND": "racial_covenants_processor.storage_backends.PublicMediaStorage",
#         # "OPTIONS": {
#         # ...your_options_here
#         # },
#     },
#     "staticfiles": {
#         "BACKEND": "racial_covenants_processor.storage_backends.StaticStorage",
#     }
# }

# s3 public media settings
PUBLIC_MEDIA_LOCATION = "media"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"

# s3 private media settings
PRIVATE_MEDIA_LOCATION = "private"
PRIVATE_FILE_STORAGE = "racial_covenants_processor.storage_backends.PrivateMediaStorage"
REPROCESSING_STATE_MACHINE = (
    "arn:aws:states:us-east-2:813228900636:stateMachine:DeedPageProcessorFAKEOCR"
)
OCR_CLEANUP_STATE_MACHINE = (
    "arn:aws:states:us-east-2:813228900636:stateMachine:DeedPageProcessor"
)
TERMSEARCHUPDATE_STATE_MACHINE = (
    "arn:aws:states:us-east-2:813228900636:stateMachine:TermSearchUpdate"
)
TERMSEARCHTEST_LAMBDA = "arn:aws:lambda:us-east-2:813228900636:function:mp-covenants-term-search--CovenantsTermSearchFuzzy-vEeLOY95b9vQ"

UPDATE_STATS_LAMBDA = "arn:aws:lambda:us-east-2:813228900636:function:covenants-update-stats-CovenantsUpdateStatsFunctio-LMg5mVLT4GNq"
IMGHIGHLIGHT_LAMBDA = "arn:aws:lambda:us-east-2:813228900636:function:covenants-highlight-text-CovenantsHighlightTextFun-b4L4ashaSJuV"


# localsqlalchemy settings
SQL_ALCHEMY_DB_CONNECTION_URL = "postgresql+psycopg2://racial_covenants_processor:racial_covenants_processor@localhost:5432/racial_covenants_processor"

# Disable cache on dev
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.dummy.DummyCache",
#     }
# }

ZOONIVERSE_PROJECT_SLUG = "mappingprejudice/mapping-prejudice"
ZOONIVERSE_USERNAME = "XXXX"
ZOONIVERSE_PASSWORD = "XXXX"

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": "http://127.0.0.1:8983/solr/deedmachine",
        # 'URL': 'http://localhost:8988/solr/deedmachine',  # Production, with ssh tunnel
        # 'URL': 'http://ec2-3-15-172-23.us-east-2.compute.amazonaws.com:8983/solr/deedmachine',
        "ADMIN_URL": "http://127.0.0.1:8983/solr/admin/cores",
        # 'ADMIN_URL': 'http://localhost:8988/solr/admin/cores'  # Production, with ssh tunnel
    },
}
