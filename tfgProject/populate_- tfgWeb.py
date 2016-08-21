import django
import os
import gc
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfgProject.settings")
django.setup()
import numpy as np
import javabridge as jv
import bioformats as bf
from PIL import Image as PILImage
from tfgWeb.models import Galery, Image, Experiment
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

def get_name_experiment(filename):
    parts = filename.split('/')
    size = len(parts)
    name = parts[size-1].split(('.'))[0]
    return name

#Adding to BD

def add_experiment(name, info, user, is_atlas, front_axis, top_axis, side_axis):
    experiment = Experiment.objects.get_or_create(owner=user, name=name, info= info, is_atlas=is_atlas, front_axis=front_axis, side_axis=side_axis, top_axis=top_axis)[0]
    return experiment

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

#Reading Series
def read_series(experiment, bf_reader, serieID=0, name=""):  # Reads a series

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

    # Getting the order and the initial shape of the array
    # order = reader.getDimensionOrder() #Obtains the 5D matrix: X,Y,Z, Channel and Time in order
    order = 'XYZCT'
    shape = [getattr(reader, "getSize" + s)() for s in order]  # Contains the 5D matrix sizes in order

    axis_list = config.AXIS.items()
    print " -Getting matrix"
    matrix = utils.get_matrix(bf_reader,shape,serieID)
    final_shape = np.shape(matrix)

    serie = experiment.add_series(name, total_times, final_shape[0], final_shape[1], final_shape[2])
    rescaled_shape = np.shape(matrix)

    for axis in axis_list:
        print " -Almacenando axis " + axis[0]
        axis_model = serie.add_axis(axis[0])

        for time in range(0, shape[4]):
            for pos in range(0, rescaled_shape[axis[1]]):
                if axis[0]==experiment.top_axis:
                    image = PILImage.fromarray(matrix[:, pos, :, :, time].astype('uint8')).convert('RGBA')
                elif axis[0]==experiment.side_axis:
                    image = PILImage.fromarray(np.swapaxes(PILImage.fromarray(matrix[pos, :, :, :, time].astype('uint8')),0,1).astype('uint8')).convert('RGBA') #Girar TOP IMAGE
                elif axis[0]==experiment.front_axis:
                    image = PILImage.fromarray(matrix[:, :, pos, :, time].astype('uint8')).convert('RGBA')

                #Add alpha channel
                aux_image = image.convert('L')
                image.putalpha(aux_image)

                path = config.IMAGES_PATH + str(admin.id) + '/' + experiment.name + '/' + name + '/' + axis[0] + '/'

                if not os.path.exists(path):
                    os.makedirs(path)
                image_path = path + str(pos) + '-' + str(time) + config.TYPE
                print '     -' + image_path
                image.save(image_path)
                image.close()

                axis_model.add_image(image_path, pos, time)

    gc.collect()

#Saving Atlas
def save_h5(filename):

    admin = add_admin()
    name = get_name_experiment(filename)
    experiment = add_experiment(user=admin,info=None,name=name, is_atlas=True, front_axis='Z', top_axis='Y', side_axis='X')

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
                    print " -Almacenando axis " + axis[0]

                    for pos in range(0, shape[axis[1]]):
                        if axis[0] == experiment.top_axis:
                            image = PILImage.fromarray(atlas[:, pos, :].astype('uint8'))
                        elif axis[0] == experiment.side_axis:
                            image = PILImage.fromarray(atlas[pos, :, :].astype('uint8'))
                        elif axis[0] == experiment.front_axis:
                            image = PILImage.fromarray(atlas[:, :, pos].astype('uint8'))

                        if axis[0]==experiment.top_axis:
                            image = image.rotate(180)

                        path = config.ATLAS_PATH + dataset_key + '/' + axis[0] + '/'
                        if not os.path.exists(path):
                            os.makedirs(path)
                        image_path = path + str(pos) + config.TYPE
                        image.save(image_path)
                        print '     -' + image_path
                        axis_model.add_image(image_path,pos,0)
                        image.close()
    gc.collect()

#Populate function
def populate(filename, atlasname):

    # Checking VM
    check_VM()

    bf_reader = get_reader(filename)
    total_series = get_total_series(bf_reader.rdr)
    names = get_name(filename)

    name = get_name_experiment(filename)
    admin = add_admin()
    experiment = add_experiment(name=name,info=None,user=admin, is_atlas=False, top_axis='X', side_axis='Y', front_axis='Z')

    for serieID in range(0, total_series):
        print 'Loading serie: ' + names[serieID]
        read_series(experiment=experiment, bf_reader=bf_reader, serieID=serieID, name=names[serieID])

    kill_VM()

    print "Loading atlas..."
    save_h5(atlasname)

    print "Populate finished succesfully!"

# Start execution here!
if __name__ == '__main__':
    print("Starting population script...")
    populate(filename,atlasname)