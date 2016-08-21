import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_URL = 'static/'
STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [STATIC_DIR, ]
IMAGES_PATH = STATIC_URL + 'tfgWeb_images/'
ATLAS_PATH = STATIC_URL + 'tfgWeb_atlas/'
FRONT_PATH = 'front_image'
SIDE_PATH = 'side_image'
TOP_PATH = 'top_image'
TYPE = '.png'

ADMIN_NAME = 'default'

AXIS = {
    'X': 0,
    'Y': 1,
    'Z': 2,
}

VIEWS = {
    'FRONT': 'Z',
    'SIDE': 'X',
    'TOP': 'Y',
}

ORDERS = {
    'XYZ': 'FRONT-X, TOP-Y, SIDE-Z',
    'ZYX': 'FRONT-Z, TOP-Y, SIDE-X',
    'ZXY': 'FRONT-Z, TOP-X, SIDE-Y',
    'XZY': 'FRONT-X, TOP-Z, SIDE-Y',
    'YXZ': 'FRONT-Y, TOP-X, SIDE-Z',
    'YZX': 'FRONT-Y, TOP-Z, SIDE-X',
}

DEFAULT_SIZES = {
    'X': 333,
    'Y': 333,
    'Z': 533,
}

VISTAS_ANON = {
    'BRAIN': 'Brain',
    'ATLAS':'Atlas',
}

VISTAS_AUTH = {
    'BRAIN': 'Brain',
    'ATLAS':'Atlas',
    'SYNC':'Sincronize',
}