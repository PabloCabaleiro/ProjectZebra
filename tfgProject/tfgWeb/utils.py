import h5py
from PIL import Image
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfgProject.settings")
import numpy as np
import javabridge as jv
import bioformats as bf
from PIL import Image as PILImage
from xml import etree as et
from tfgWeb import config
from models import Galery
import gc

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
    size_t = reader.getSizeT()
    return size_x, size_y, size_z, size_t

def get_name_lif(filename):

    names = []
    xml_string = bf.get_omexml_metadata(filename)
    xml_string = xml_string.encode('ascii', 'ignore')
    metadata_root = et.ElementTree.fromstring(xml_string)
    for child in metadata_root:
        if child.tag.endswith('Image'):
            names.append(child.attrib['Name'])

    return names

def get_z_rescaled_matrix(image5d, bf_reader, shape, sizesXYZ):  # Returns proportional image5d

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
    shape[2] = int(np.trunc(shape[2] * sizesXYZ[2] / sizesXYZ[0]))  # Change z dim size

    rescaled_image5d = np.empty(shape, dtype=BF2NP_DTYPE[bf_reader.rdr.getPixelType()])

    for time in range(0, shape[4]):
        for pos_y in range(0, shape[1]):
            aux_image = Image.fromarray(image5d[:, pos_y, :, :, time].astype('uint8'))
            rescaled_image5d[:, pos_y, :, :, time] = aux_image.resize((shape[2], shape[0]), Image.LANCZOS)

    return rescaled_image5d

def rescale_matrix(matrix, resolution):

    print "     -Rescalando matriz con resolucion " + str(resolution)

    if (not resolution == 1):
        shape = np.shape(matrix)
        aux_shape = [np.round(shape[0] / resolution), np.round(shape[1] / resolution),shape[2], shape[3]+1,shape[4]]
        rescaled_shape = [np.round(shape[0]/resolution),np.round(shape[1]/resolution),np.round(shape[2]/resolution),shape[3]+1,shape[4]]

        aux_matrix = np.empty(aux_shape)
        rescaled_matrix = np.empty(rescaled_shape)

        for time in range(0,aux_shape[4]):
            for z in range(0,aux_shape[2]):
                image = PILImage.fromarray(matrix[:,:,z,:,time].astype('uint8'))
                image = image.resize((aux_shape[0], aux_shape[1]), Image.LANCZOS)
                image = image.convert('RGBA')
                aux_matrix[:,:,z,:,time] = np.array(image)
                image.close()
            for x in range(0,rescaled_shape[0]):
                image =PILImage.fromarray(aux_matrix[x,:,:,:,time].astype('uint8'))
                image = image.resize((rescaled_shape[2],rescaled_shape[1]), Image.LANCZOS)
                image = image.convert('RGBA')
                rescaled_matrix[x,:,:,:,time] = np.array(image)
                image.close()

        return rescaled_matrix
    else:
        return matrix

def get_matrix(bf_reader, shape, serieID=0):

    try:
        image5d = np.empty(shape, dtype=BF2NP_DTYPE[bf_reader.rdr.getPixelType()])
    except:
        raise MemoryError("The matrix is too big. Try with H5 format for larger files")

    for time in range(0, shape[4]):
        for pos_z in range(0, shape[2]):
            image5d[:, :, pos_z, :, time] = bf_reader.read(series=serieID, c=None, z=pos_z, t=time,
                                                                   rescale=False)
    sizesXYZ, shapeXYZ = get_series_scale_lif(bf_reader.rdr, serieID)

    final_image5d = get_z_rescaled_matrix(image5d, bf_reader, shape, sizesXYZ)

    return final_image5d

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

def read_series(bf_reader, user, serieID=0, name=""):  # Reads a series

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
    serie = add_series(name, size_x, size_y, size_z, total_times, user=user)

    # Getting the order and the initial shape of the array
    # order = reader.getDimensionOrder() #Obtains the 5D matrix: X,Y,Z, Channel and Time in order
    order = 'XYZCT'
    shape = [getattr(reader, "getSize" + s)() for s in order]  # Contains the 5D matrix sizes in order

    resolutions = config.RESOLUTIONS.items()
    axis_list = config.AXIS.items()
    print " -Getting matrix"
    matrix = get_matrix(bf_reader,shape,serieID)

    for resolution in resolutions:

        muestra = serie.add_sample(resolution[0],resolution[1])
        print " -Almacenado muestra " + str(muestra.__str__())

        if resolution[1] != 1:
            rescaled_matrix = rescale_matrix(matrix, resolution[1])
        else:
            rescaled_matrix = matrix

        rescaled_shape = np.shape(rescaled_matrix)

        for axis in axis_list:
            print axis, axis[0], axis[1]
            print "     -Almacenando axis " + axis[0]
            size = axis[1]
            axis_model = muestra.add_axis(axis[0])

            for time in range(0, shape[4]):
                for pos in range(0, rescaled_shape[size]):
                    if axis[1]==0:
                        image = PILImage.fromarray(rescaled_matrix[pos, :, :, :, time].astype('uint8'))
                    elif axis[1]==1:
                        image = PILImage.fromarray(rescaled_matrix[:, pos, :, :, time].astype('uint8'))
                    elif axis[1]==2:
                        image = PILImage.fromarray(rescaled_matrix[:, :, pos, :, time].astype('uint8'))

                    path = config.IMAGES_PATH + str(user.id) + '/' + name + '/' + muestra.name + '/'  + axis[0] + '/'

                    if not os.path.exists(path):
                        os.makedirs(path)
                    image_path = path + str(pos) + '-' + str(time) + config.TYPE
                    print '         -' + image_path
                    image.save(image_path)
                    image.close()

                    axis_model.add_image(image_path, pos, time)

    gc.collect()

def save_lif(filename, user):

    # Checking VM
    check_VM()

    bf_reader = get_reader_lif(filename)
    total_series = get_total_series_lif(bf_reader.rdr)
    names = get_name_lif(filename)

    for serieID in range(0, total_series):
        print 'Loading serie: ' + names[serieID]
        read_series(bf_reader=bf_reader, user=user, serieID=serieID, name=names[serieID])

    kill_VM()

#Reading Series h5

def save_h5(filename, user):

    with h5py.File(filename, 'r') as hf:
        groups_list = hf.keys()
        for group_key in groups_list:
            dataset_list = hf[group_key]
            for dataset_key in dataset_list:

                dataset = hf['/' + group_key + '/' + dataset_key]
                atlas = dataset[:, :, :]
                shape = np.shape(atlas)

                atlas_model = add_series(name=dataset_key, size_x=shape[0], size_y=shape[1], size_z=shape[2], total_time=0, user=user)

                resolutions = config.RESOLUTIONS.items()
                axis_list = config.AXIS.items()

                for resolution in resolutions:
                    print '     -Rescalando matriz con resolucion ' + str(resolution[1])
                    muestra = atlas_model.add_sample(resolution[0], resolution[1])

                    if (resolution[1] == 1):
                        rescaled_shape = shape
                    else:
                        rescaled_shape = (np.round(shape[0] / resolution[1]), np.round(shape[1] / resolution[1]),
                                          np.round(shape[2] / resolution[1]))

                        atlas.resize(rescaled_shape)

                    for axis in axis_list:
                        axis_model = muestra.add_axis(name=axis[1])

                        for pos in range(0, rescaled_shape[axis[1]]):
                            if axis[1] == 0:
                                image = PILImage.fromarray(atlas[pos, :, :].astype('uint8')).convert('RGBA')
                            elif axis[1] == 1:
                                image = PILImage.fromarray(atlas[:, pos, :].astype('uint8')).convert('RGBA')
                            elif axis[1] == 2:
                                image = PILImage.fromarray(atlas[:, :, pos].astype('uint8')).convert('RGBA')

                            path = config.ATLAS_PATH + dataset_key + '/' + resolution[0] + '/' + axis[0] + '/'
                            if not os.path.exists(path):
                                os.makedirs(path)
                            image_path = path + str(pos) + config.TYPE
                            image.save(image_path)
                            print '         -' + image_path
                            axis_model.add_image(image_path, pos, 0)
                            image.close()
    gc.collect()

#Adding to BD

def add_series(name, size_x, size_y, size_z, total_time, user):
    serie = Galery.objects.get_or_create(name=name, x_size=size_x, y_size=size_y, z_size=size_z, total_times=total_time, owner = user, is_atlas=False)[0]
    serie.save()
    return serie