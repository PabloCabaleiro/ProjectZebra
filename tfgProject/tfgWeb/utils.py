import numpy as np
from PIL import Image
import os


FRONT_PATH = 'front_image'
SIDE_PATH = 'side_image'
TOP_PATH = 'top_image'
TYPE = '.png'
IMAGES_PATH = 'static/images/'
ADMIN_NAME = 'default'

def get_top_image(image5d, pos_z=0, time=0, user='default'):
    image = Image.fromarray(np.uint8(image5d[:, :, pos_z, :, time]))
    user_path = IMAGES_PATH + user + '/'
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    file_path = user_path + TOP_PATH + TYPE
    image.save(file_path,"PNG")
    return file_path

def get_front_image(image5d, pos_y=0, time=0, user='default'):
    print np.shape(image5d)
    image =  Image.fromarray(np.swapaxes(np.uint8(image5d[:, pos_y, :, :, time]), 0, 1))
    user_path = IMAGES_PATH + user + '/'
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    file_path = user_path + FRONT_PATH + TYPE
    image.save(file_path,"PNG")
    return file_path

def get_side_image(image5d, pos_x=0, time=0, user='default'):
    image = Image.fromarray(image5d[pos_x, :, :, :, time].astype('uint8'))
    user_path = IMAGES_PATH + user + '/'
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    file_path = user_path + SIDE_PATH + TYPE
    image.save(file_path,"PNG")
    return file_path