import django
import os
import gc
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfgProject.settings")
django.setup()
import numpy as np
import javabridge as jv
import bioformats as bf
from PIL import Image as PILImage
from tfgWeb.models import Serie, Image, Atlas, AtlasImage
from xml import etree as et
from tfgWeb import utils, config
from django.contrib.auth.models import User
import h5py

VM_ON = False
VM_KILLED = False
filename = "/home/pablo/bioformats/twist_sytox_zo_4d.lif"
atlasname =  "/home/pablo/bioformats/ViBE-Z_48hpf_v1.h5"

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

#Admin JVM

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

#AUXILIARES

def get_reader(pathfile): #Obtains ImageReader
	return bf.ImageReader(pathfile)

def get_total_series(reader): #Obtains the total number of series in the file
	return reader.getSeriesCount()

def get_series_scale(reader, seriesID=0):  # Obtains pyisical size from each axis

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

def get_sizes(reader):
    size_x = reader.getSizeX()
    size_y = reader.getSizeY()
    size_z = reader.getSizeZ()
    size_c = reader.getSizeC()
    size_t = reader.getSizeT()
    return size_x, size_y, size_z, size_c, size_t

def get_name(filename):

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

    print "Creating the z rescaled array... "

    # Adjust the z size of the array
    shape[2] = int(np.trunc(shape[2] * sizesXYZ[2] / sizesXYZ[0]))  # Change z dim size

    rescaled_image5d = np.empty(shape, dtype=BF2NP_DTYPE[bf_reader.rdr.getPixelType()])

    for time in range(0, shape[4]):
        for pos_y in range(0, shape[1]):
            aux_image = Image.fromarray(image5d[:, pos_y, :, :, time].astype('uint8'))
            rescaled_image5d[:, pos_y, :, :, time] = aux_image.resize((shape[2], shape[0]), Image.LANCZOS)

    return rescaled_image5d

#Adding to BD

def add_series(name, size_x, size_y, size_z, total_time, admin):
    serie = Serie.objects.get_or_create(name=name, x_size=size_x, y_size=size_y, z_size=size_z, total_times=total_time, owner = admin)[0]
    serie.save()
    return serie

def add_atlas(name, size_x, size_y, size_z):
    atlas = Atlas.objects.get_or_create(name=name, x_size=size_x, y_size=size_y, z_size=size_z)[0]
    atlas.save()
    return atlas

def add_admin():
    try:
        user = User.objects.create_user(config.ADMIN_NAME, 'admin@admin.com', 'defaultpass2')
        user.save()
        return user
    except:
        user = User.objects.get_by_natural_key(config.ADMIN_NAME)
        return user

def add_image(serie,image,pos_z,time):
    im = Image.objects.get_or_create(serie=serie,image=image,pos_z=pos_z,time=time)[0]
    im.save()
    return im

def add_atlas_image(atlas,image,pos_z):
    im = AtlasImage.objects.get_or_create(atlas=atlas,image=image,pos_z=pos_z)[0]
    im.save()
    return im

#Reading Series
def read_series(bf_reader, serieID=0, name=""):  # Reads a series

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

    #Adding default admin
    admin = add_admin()

    # Checking values
    reader = bf_reader.rdr
    total_series = get_total_series(reader)
    if (serieID < 0 or serieID >= total_series):
        raise ValueError("Series number no valid")
    reader.setSeries(serieID)

    size_x, size_y, size_z, size_c, total_times = get_sizes(reader=reader)
    serie = add_series(name, size_x, size_y, size_z, total_times, admin)

    # Getting the order and the initial shape of the array
    # order = reader.getDimensionOrder() #Obtains the 5D matrix: X,Y,Z, Channel and Time in order
    order = 'XYZCT'
    shape = [getattr(reader, "getSize" + s)() for s in order]  # Contains the 5D matrix sizes in order

    resolutions = config.RESOLUTIONS.items()
    print " -Getting matrix"
    matrix = utils.get_matrix(bf_reader,shape,serieID)

    for resolution in resolutions:
        muestra = serie.add_muestra(resolution[0],resolution[1])
        print " -Almacenado muestra " + str(muestra.__str__())
        rescaled_matrix = utils.rescale_matrix(matrix,resolution[1])
        rescaled_shape = np.shape(rescaled_matrix)

        for time in range(0, shape[4]):
            for pos_z in range(0, rescaled_shape[2]):
                image = PILImage.fromarray(rescaled_matrix[:,:,pos_z,:,time].astype('uint8'))
                path = config.IMAGES_PATH + str(admin.id) + '/' + name + '/' + muestra.name + '/'
                if not os.path.exists(path):
                    os.makedirs(path)
                image_path = path + str(pos_z) + '-' + str(time) + config.TYPE
                print '         -' + image_path
                image.save(image_path)
                image.close()

                muestra.add_image(image_path, pos_z, time)

    gc.collect()

#Saving Atlas
def save_h5(filename):

    with h5py.File(filename, 'r') as hf:
        groups_list = hf.keys()
        for group_key in groups_list:
            dataset_list = hf[group_key]
            for dataset_key in dataset_list:

                dataset = hf['/' + group_key + '/' + dataset_key]
                atlas = dataset[:, :, :]
                shape = np.shape(atlas)
                print shape

                atlas_model = add_atlas(dataset_key, shape[0], shape[1], shape[2])

                resolutions = config.RESOLUTIONS.items()

                for resolution in resolutions:
                    print '     -Rescalando matriz con resolucion ' + str(resolution[1])
                    muestra = atlas_model.add_muestra(resolution[0],resolution[1])

                    if (resolution[1]==1):
                        rescaled_atlas = atlas
                        rescaled_shape = shape
                    else:
                        rescaled_shape = [np.round(shape[0] / resolution[1]), np.round(shape[1] / resolution[1]),
                                              np.round(shape[2] / resolution[1]), 4]
                        if (shape[0]>shape[2]):
                            aux_shape = [np.round(shape[0] / resolution[1]), np.round(shape[1] / resolution[1]),
                                         shape[2], 4]
                            aux_atlas = np.empty(aux_shape)
                            rescaled_atlas = np.empty(rescaled_shape)
                            for z in range(0, shape[2]):
                                image = PILImage.fromarray(atlas[:, :, z,:].astype('uint8'))
                                image = image.resize((rescaled_shape[1],rescaled_shape[0]), PILImage.LANCZOS)
                                aux_atlas[:,:,z,:] = image
                            for x in range(0,rescaled_shape[0]):
                                image = PILImage.fromarray(aux_atlas[x, :, :,:].astype('uint8'))
                                image = image.resize((rescaled_shape[2], rescaled_shape[1]), PILImage.LANCZOS)
                                rescaled_atlas[x,:,:,:] = image.convert('RGBA')
                        else:
                            aux_shape = [shape[0], np.round(shape[1] / resolution[1]), np.round(shape[2]/resolution[1]),4]
                            aux_atlas = np.empty(aux_shape)
                            rescaled_atlas = np.empty(rescaled_shape)
                            for x in range(0, shape[0]):
                                image = PILImage.fromarray(atlas[x, :, :].astype('uint8'))
                                image = image.resize((rescaled_shape[2], rescaled_shape[1]), PILImage.LANCZOS)
                                aux_atlas[x, :, :, :] = image.convert('RGBA')
                            for z in range(0,rescaled_shape[2]):
                                image = PILImage.fromarray(aux_atlas[:, :, z, :].astype('uint8'))
                                image = image.resize((rescaled_shape[1], rescaled_shape[0]), PILImage.LANCZOS)
                                rescaled_atlas[:, :, z, :] = image.convert('RGBA')

                    for z in range(0, rescaled_shape[2]):
                        if resolution[1]==1:
                            image = PILImage.fromarray(rescaled_atlas[:, :, z].astype('uint8')).convert('RGBA')
                        else:
                            image = PILImage.fromarray(rescaled_atlas[:, :, z,:].astype('uint8')).convert('RGBA')

                        path = config.ATLAS_PATH + dataset_key + '/' + resolution[0] +'/'
                        if not os.path.exists(path):
                            os.makedirs(path)
                        image_path = path + str(z) + config.TYPE
                        image.save(image_path)
                        print '         -' + image_path
                        muestra.add_image(image_path,z)
                        image.close()
    gc.collect()

#Populate function
def populate(filename):


    # Checking VM
    check_VM()

    bf_reader = get_reader(filename)
    total_series = get_total_series(bf_reader.rdr)
    names = get_name(filename)

    for serieID in range(0, total_series):
        print 'Loading serie: ' + names[serieID]
        read_series(bf_reader=bf_reader, serieID=serieID, name=names[serieID])

    kill_VM()

    print "Loading atlas..."
    save_h5(atlasname)

    print "Populate finished succesfully!"

# Start execution here!
if __name__ == '__main__':
    print("Starting population script...")
    populate(filename)