import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','tfgProject.settings')
import django
django.setup()
import numpy as np
import javabridge as jv
import bioformats as bf
from PIL import Image as PILImage
from tfgWeb.models import Serie, Image
from xml import etree as et
from tfgWeb import utils
from django.contrib.auth.models import User

VM_ON = False
VM_KILLED = False
filename = "/home/pablo/bioformats/twist_sytox_zo_4d.lif"

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

def add_series(name, size_x, size_y, size_z, size_c, total_time, admin):
    serie = Serie.objects.get_or_create(name=name, x_size=size_x, y_size=size_y, z_size=size_z,c_size=size_c, total_times=total_time, owner = admin)[0]
    serie.save()
    return serie

def add_admin():
    try:
        user = User.objects.create_user('default', 'admin@admin.com', 'defaultpass2')
        user.save()
        return user
    except:
        user = User.objects.get_by_natural_key(utils.ADMIN_NAME)
        return user

def add_image(serie,image,pos_z,time):
    im = Image.objects.get_or_create(serie=serie,image=image,pos_z=pos_z,time=time)[0]
    im.save()
    return im

#Reading Series

def read_series(bf_reader, serieID=0, name="", RGBA=True):  # Reads a series

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
    serie = add_series(name, size_x, size_y, size_z, size_c+1, total_times, admin)

    # Getting the order and the initial shape of the array
    # order = reader.getDimensionOrder() #Obtains the 5D matrix: X,Y,Z, Channel and Time in order
    order = 'XYZCT'
    shape = [getattr(reader, "getSize" + s)() for s in order]  # Contains the 5D matrix sizes in order

    if RGBA:
        shape[3] += 1

    aux_image = np.empty([shape[0], shape[1], shape[3]])

    for time in range(0, shape[4]):
        for pos_z in range(0, shape[2]):
            aux_image[:, :, [0, 1, 2]] = bf_reader.read(series=serieID, c=None, z=pos_z, t=time, rescale=False)
            if RGBA:
                aux_image_alpha = np.array(PILImage.fromarray(aux_image[:,:,[0,1,2]].astype('uint8')).convert('L'))
                low_values_indices = aux_image_alpha > 5
                aux_image_alpha[low_values_indices] = 255
                aux_image[:, :, 3] = aux_image_alpha

            path = 'static/images/' + name + '-' + str(pos_z) + '-' + str(time) + '.png'
            image = PILImage.fromarray(aux_image.astype('uint8'))
            image.save(path)
            add_image(serie, path, pos_z, time)

def populate(filename):

    # Checking VM
    check_VM()

    bf_reader = get_reader(filename)
    total_series = get_total_series(bf_reader.rdr)
    names = get_name(filename)

    for serieID in range(0, total_series):
        print 'Loading serie: ' + names[serieID]
        read_series(bf_reader=bf_reader, serieID=serieID, name=names[serieID], RGBA=True)

    kill_VM()

# Start execution here!
if __name__ == '__main__':
    print("Starting population script...")
    populate(filename)