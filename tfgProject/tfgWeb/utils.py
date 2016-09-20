import h5py
from PIL import Image
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfgProject.settings")
import numpy as np
import javabridge as jv
import bioformats as bf
from PIL import Image as PILImage
from xml import etree as et
from tfgWeb import config, models
from models import Galery
import gc
import json
from time import time

VM_ON = False
VM_KILLED = False
BF2NP_DTYPE = {
    0: np.int8,
    1: np.uint8,
    2: np.int16,
    3: np.uint16,
    4: np.int32,
    5: np.uint32,
    6: np.float32,
    7: np.double
}

#Auxiliares .lif

def check_VM():
    global VM_ON
    global VM_KILLED

    if (VM_ON):
        return True
    elif (VM_KILLED):
        raise RuntimeError("JVM was killed. Restart the program")
    else:
        start_VM()
        return True

def start_VM(max_heap_size='4G'):
    global VM_ON
    jv.start_vm(class_path=bf.JARS, max_heap_size=max_heap_size)
    VM_ON = True

def kill_VM():
    jv.kill_vm()
    global VM_KILLED
    VM_KILLED = True

def get_reader_lif(pathfile): #Obtains ImageReader
	return bf.ImageReader(pathfile)

def get_total_series_lif(reader): #Obtains the total number of series in the file
	return reader.getSeriesCount()

def get_series_scale_lif(reader, seriesID=0):  # Obtains pyisical size from each axis

    """
        Input:
            reader: ImageReader.rdr
            serieID: [optional] number (int) of the series
        Output:
            image5d: no-proportional 5D numpy array
    """

    check_VM()

    reader.setSeries(seriesID)

    shapeXYZ = [getattr(reader, "getSize" + s)() for s in 'XYZ']
    jmd = jv.JWrapper(reader.getMetadataStore())

    sizesXYZ = []
    sizesXYZ.append(np.round(jmd.getPixelsPhysicalSizeX(seriesID).value().floatValue(), 5))
    sizesXYZ.append(np.round(jmd.getPixelsPhysicalSizeY(seriesID).value().floatValue(), 5))
    sizesXYZ.append(np.round(jmd.getPixelsPhysicalSizeZ(seriesID).value().floatValue(), 5))

    return sizesXYZ, shapeXYZ

def get_sizes_lif(reader):
    size_x = reader.getSizeX()
    size_y = reader.getSizeY()
    size_z = reader.getSizeZ()
    size_c = reader.getSizeC()
    size_t = reader.getSizeT()
    return size_x, size_y, size_z, size_c, size_t

def get_name_lif(filename):

    names = []
    xml_string = bf.get_omexml_metadata(filename)
    xml_string = xml_string.encode('ascii', 'ignore')
    metadata_root = et.ElementTree.fromstring(xml_string)
    for child in metadata_root:
        if child.tag.endswith('Image'):
            names.append(child.attrib['Name'])

    return names

def get_rescaled_matrix(image5d, bf_reader, shape, sizesXYZ):  # Returns proportional image5d

    """
        Input:
            image5d: no-proportional 5D numpy array with the images in order XYZCT
            bf_reader: ImageReader from the file
            shape: size of each dimension
            sizesXYZ: list with the pixel physical sizes from each axis
        Output:
            image5d: no-proportional 5D numpy array
    """

    print "     Creating the z rescaled array... "

    # Adjust the z size of the array
    shape[0] = int(np.trunc(shape[0] * sizesXYZ[0])) # Change x dim size
    shape[2] = int(np.trunc(shape[2] * sizesXYZ[2]))  # Change z dim size

    aux_image5d = np.empty(shape, dtype=BF2NP_DTYPE[bf_reader.rdr.getPixelType()])

    for time in range(0, shape[4]):
        for pos_y in range(0, shape[1]):
            aux_image = Image.fromarray(image5d[:, pos_y, :, :, time].astype('uint8'))
            aux_image5d[:, pos_y, :, :, time] = aux_image.resize((shape[2], shape[0]), Image.LANCZOS)

    shape[1] = int(np.trunc(shape[1] * sizesXYZ[1])) # Change y dim size
    shape[3] = 4  #RGBA
    rescaled_image5d = np.empty(shape, dtype=BF2NP_DTYPE[bf_reader.rdr.getPixelType()])

    for time in range(0, shape[4]):
        for pos_x in range(0, shape[0]):
            aux_image = Image.fromarray(aux_image5d[pos_x, :, :, :, time].astype('uint8'))
            # Add alpha channel
            mask = aux_image.convert('L')
            aux_image.putalpha(mask)
            rescaled_image5d[pos_x, :, :, :, time] = aux_image.resize((shape[2], shape[1]), Image.LANCZOS)

    return rescaled_image5d

def get_name_experiment(filename):
    parts = filename.split('/')
    size = len(parts)
    name = parts[size-1].split(('.'))[0]
    return name

def get_matrix(bf_reader, shape, serieID=0):

    #tiempo_inicial = time()

    try:
        image5d = np.empty(shape, dtype=BF2NP_DTYPE[bf_reader.rdr.getPixelType()])
    except:
        raise MemoryError("The matrix is too big. Try with H5 format for larger files")

    for t in range(0, shape[4]):
        for pos_z in range(0, shape[2]):
            image5d[:, :, pos_z, :, t] = bf_reader.read(series=serieID, c=None, z=pos_z, t=t,
                                                                   rescale=False)

    #print 'Original sizes in the file: ', shape
    sizesXYZ, shapeXYZ = get_series_scale_lif(bf_reader.rdr, serieID)

    #print 'Physical sizes: ', sizesXYZ

    final_image5d = get_rescaled_matrix(image5d, bf_reader, shape, sizesXYZ)

    print 'Final sizes: ', np.shape(final_image5d)

    #tiempo_final = time()
    #tiempo_ejecucion = tiempo_final - tiempo_inicial
    #print 'Time used to create the matrix (seconds): ', tiempo_ejecucion


    return final_image5d

#Aux for views

def get_image_sizes(atlas_size_x, atlas_size_y, atlas_size_z, galery, scale_factor=1):

    #Axis in the galery
    front = galery.experiment.front_axis
    side = galery.experiment.side_axis

    #Transform to the axis on the view -> front: z. top: y, side: x.
    if front == 'X':
        depth = int(galery.x_size/scale_factor)
        if side == 'Y':
            width = int(galery.y_size/scale_factor)
            height = int(galery.z_size/scale_factor)
        else:
            width = int(galery.z_size / scale_factor)
            height = int(galery.y_size / scale_factor)
    elif front == 'Y':
        depth = int(galery.y_size / scale_factor)
        if side == 'X':
            width = int(galery.x_size / scale_factor)
            height = int(galery.z_size / scale_factor)
        else:
            width = int(galery.z_size / scale_factor)
            height = int(galery.x_size / scale_factor)
    else:
        depth = int(galery.z_size / scale_factor)
        if side == 'X':
            width = int(galery.x_size / scale_factor)
            height = int(galery.y_size / scale_factor)
        else:
            width = int(galery.y_size / scale_factor)
            height = int(galery.x_size / scale_factor)

    if (width<atlas_size_x and height<atlas_size_y and depth<atlas_size_z):
        image_sizes = {}
        image_sizes['X']=width
        image_sizes['Y']=height
        image_sizes['Z']=depth
        return image_sizes
    else:
        return get_image_sizes(atlas_size_x,atlas_size_y,atlas_size_z,galery,scale_factor+1)

def hit_experiment(pos_x,pos_y,pos_z, galery):
    x = False
    y = False
    z = False
    if (pos_x>=galery.start_x and pos_x<= galery.start_x+galery.width):
        x = True
    if (pos_y>=galery.start_y and pos_y<= galery.start_y+galery.height):
        y = True
    if (pos_z>=galery.start_z and pos_z<= galery.start_z+galery.depth):
        z = True

    return x and y and z


#Getting images from matrix

def get_top_image(image5d, pos_z=0, time=0, user='default'):
    image = Image.fromarray(np.uint8(image5d[:, :, pos_z, :, time]))
    user_path = config.IMAGES_PATH + user + '/'
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    file_path = user_path + config.TOP_PATH + config.TYPE
    image.save(file_path,"PNG")
    return file_path

def get_front_image(image5d, pos_y=0, time=0, user='default', resize = True):

    image =  Image.fromarray(np.swapaxes(np.uint8(image5d[:, pos_y, :, :, time]), 0, 1))
    shape = np.shape(image5d[:, pos_y, :, :, time])
    if resize:
        image.resize((shape[0], int(shape[1]/config.RESIZE_VALUE)), Image.LANCZOS)

    user_path = config.IMAGES_PATH + user + '/'
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    file_path = user_path + config.FRONT_PATH + config.TYPE
    image.save(file_path,"PNG")
    return file_path

def get_side_image(image5d, pos_x=0, time=0, user='default'):
    image = Image.fromarray(image5d[pos_x, :, :, :, time].astype('uint8'))
    user_path = config.IMAGES_PATH + user + '/'
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    file_path = user_path + config.SIDE_PATH + config.TYPE
    image.save(file_path,"PNG")
    return file_path

#Reading Series .lif

def read_series(experiment, user, bf_reader, serieID=0, name=""):  # Reads a series

    """
        Input:
            bf_reader: ImageReader from the file.
            serieID: [optional] number (int) of the series
            proportional: [optional] true if you want the proportional image depending on the physical pixel size
            scaled: [optional] rate of the scale you want to apply on the images
        Output:
            image5d: 5D numpy array with the images in order: XYZCT
    """

    # Checking VM
    check_VM()

    # Checking values
    reader = bf_reader.rdr
    total_series = get_total_series_lif(reader)
    if (serieID < 0 or serieID >= total_series):
        raise ValueError("Series number no valid")
    reader.setSeries(serieID)

    size_x, size_y, size_z, size_c, total_times = get_sizes_lif(reader=reader)

    # Getting the order and the initial shape of the array
    # order = reader.getDimensionOrder() #Obtains the 5D matrix: X,Y,Z, Channel and Time in order
    aux_order = 'XYZCT'
    shape = [getattr(reader, "getSize" + s)() for s in aux_order]  # Contains the 5D matrix sizes in order

    axis_list = config.AXIS.items()
    print " -Getting matrix"
    matrix = get_matrix(bf_reader, shape, serieID)
    final_shape = np.shape(matrix)
    serie = experiment.add_series(name, total_times, final_shape[0], final_shape[1], final_shape[2])

    for axis in axis_list:
        print " -Almacenando axis " + axis[0]
        axis_model = serie.add_axis(axis[0])

        for time in range(0, shape[4]):
            for pos in range(0, final_shape[axis[1]]):
                if axis[0] == 'Y':
                    image = PILImage.fromarray(matrix[:, pos, :, :, time].astype('uint8')).convert('RGBA')
                elif axis[0] == 'X':
                    image = PILImage.fromarray(
                        np.swapaxes(PILImage.fromarray(matrix[pos, :, :, :, time].astype('uint8')), 0, 1).astype(
                            'uint8')).convert('RGBA')  # Girar TOP IMAGE
                elif axis[0] == 'Z':
                    image = PILImage.fromarray(matrix[:, :, pos, :, time].astype('uint8')).convert('RGBA')

                if axis[0] == experiment.top_axis:
                    image = image.rotate(270)
                if axis[0] == experiment.front_axis:
                    image = image.rotate(270)

                path = config.IMAGES_PATH + str(user.id) + '/' + str(experiment.id) + '/' + name + '/' + axis[0] + '/'

                if not os.path.exists(path):
                    os.makedirs(path)
                image_path = path + str(pos) + '-' + str(time) + config.TYPE
                print '     -' + image_path
                image.save(image_path)
                image.close()

                axis_model.add_image(image_path, pos, time)

    gc.collect()

def save_lif(filename, user, top_axis, side_axis, front_axis, is_atlas=False, name = None):

    # Checking VM
    check_VM()

    bf_reader = get_reader_lif(filename)
    total_series = get_total_series_lif(bf_reader.rdr)
    names = get_name_lif(filename)
    if name is None:
        name = get_name_experiment(filename)
    metadata = get_metadata_lif(filename)
    experiment = models.add_experiment(name=name, info=metadata, user=user, is_atlas=is_atlas, top_axis=top_axis, side_axis=side_axis,
                                front_axis=front_axis)

    for serieID in range(0, total_series):
        read_series(experiment=experiment, bf_reader=bf_reader, user=user, serieID=serieID, name=names[serieID])

    kill_VM()

def get_metadata_lif(filename):

    check_VM()

    xml_string = bf.get_omexml_metadata(filename).encode("utf-8")

    metadata = []
    size_tags = ['Size' + c for c in 'XYZCT']
    res_tags = ['PhysicalSize' + c for c in 'XYZ']
    metadata_root = et.ElementTree.fromstring(xml_string)
    for child in metadata_root:
        if child.tag.endswith('Image'):
            aux_dict = {}
            aux_dict['Name'] = child.attrib['Name']
            for grandchild in child:

                if grandchild.tag.endswith('AcquisitionDate'):
                    aux_dict['AcquisitionDate'] = grandchild.text
                elif grandchild.tag.endswith('InstrumentRef'):
                    instrumentID = grandchild.attrib['ID']
                    for aux_child in metadata_root:
                        if aux_child.tag.endswith('Instrument'):
                            if aux_child.attrib['ID'] == instrumentID:
                                for aux_grandchild in aux_child:
                                    if aux_grandchild.tag.endswith('Microscope'):
                                        aux_dict['Instrument'] = aux_grandchild.attrib['Model']
                if grandchild.tag.endswith('Pixels'):
                    att = grandchild.attrib
                    for tag in size_tags:
                        aux_dict[tag] = int(att[tag])
                    for tag in res_tags:
                        aux_dict[tag] = float(att[tag])
            metadata.append(aux_dict)

    return json.dumps(metadata)

#Reading Series h5

def save_h5(filename, user, top_axis, side_axis, front_axis, is_atlas=False, name=None):

    if name is None:
        name = get_name_experiment(filename)
    metadata = str(get_h5_metadata(filename))
    experiment = models.add_experiment(user=user, info=metadata, name=name, is_atlas=is_atlas, top_axis=top_axis, side_axis=side_axis,
                                front_axis=front_axis)

    with h5py.File(filename, 'r') as hf:
        groups_list = hf.keys()
        for group_key in groups_list:
            dataset_list = hf[group_key]
            for dataset_key in dataset_list:

                dataset = hf['/' + group_key + '/' + dataset_key]
                atlas = dataset[:, :, :]
                shape = np.shape(atlas)

                atlas_model = experiment.add_atlas(name=dataset_key, size_x=shape[0], size_y=shape[1], size_z=shape[2])

                axis_list = config.AXIS.items()

                for axis in axis_list:
                    axis_model = atlas_model.add_axis(name=axis[0])
                    for pos in range(0, shape[axis[1]]):
                        if axis[0] == 'Y':
                            image = PILImage.fromarray(atlas[:, pos, :].astype('uint8'))
                        elif axis[0] == 'X':
                            image = PILImage.fromarray(atlas[pos, :, :].astype('uint8'))
                        elif axis[0] == 'Z':
                            image = PILImage.fromarray(atlas[:, :, pos].astype('uint8'))

                        if axis[0]==experiment.top_axis:
                            image = image.rotate(180)

                        if is_atlas:
                            path = config.ATLAS_PATH + dataset_key + '/' + axis[0] + '/'
                        else:
                            path = config.IMAGES_PATH + '/' + str(user.id) +'/'+str(experiment.id)+'/' + dataset_key + '/' + axis[0] + '/'

                        if not os.path.exists(path):
                            os.makedirs(path)
                        image_path = path + str(pos) + config.TYPE
                        image.save(image_path)
                        axis_model.add_image(image_path,pos,0)
                        image.close()
    gc.collect()

def get_h5_metadata(filename):

    data_list = []
    with h5py.File(filename, 'r') as hf:
        groups_list = hf.keys()
        for group_key in groups_list:
            group = hf[group_key]
            metadata = group.items()
            for data in metadata:
                aux_dict ={}
                aux_dict['Name'] = data[0]
                aux_dict['SizeX'] = data[1].shape[0]
                aux_dict['SizeY'] = data[1].shape[1]
                aux_dict['SizeZ'] = data[1].shape[2]
                aux_dict['Description'] = str(data[1])
                data_list.append(aux_dict)

    return json.dumps(data_list)

#Adding to BD

def add_series(name, size_x, size_y, size_z, total_time, user):
    serie = Galery.objects.get_or_create(name=name, x_size=size_x, y_size=size_y, z_size=size_z, total_times=total_time, owner = user, is_atlas=False)[0]
    serie.save()
    return serie