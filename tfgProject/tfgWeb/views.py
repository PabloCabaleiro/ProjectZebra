from django.shortcuts import render
from tfgWeb import models
from tfgWeb import utils, config
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from tfgWeb.forms import UserForm, UserProfileForm, InfoForm, UploadForm, ZoneForm, ZoneInfoForm, AtlasForm

def choose_zone(request):

    context_dict = {}

    try:
        user = request.user
    except:
        user = None

    atlas_list = list(models.get_atlas())
    context_dict["atlas_list"] = atlas_list
    sizes = config.DEFAULT_SIZES

    if request.method == 'POST':
        zone_form = ZoneForm(request.POST)
        atlas_form = ZoneInfoForm(request.POST)

        if (zone_form.is_valid()):
            atlasID = int(zone_form.cleaned_data['atlas'])
            for atlas in atlas_list:
                if atlas.id == atlasID:
                    selected_atlas = atlas
                    break

            x_min = selected_atlas.x_size * zone_form.cleaned_data['min_x'] / float(sizes['X'])
            x_max =  selected_atlas.x_size * zone_form.cleaned_data['max_x'] / float(sizes['X'])
            y_min =  selected_atlas.y_size * zone_form.cleaned_data['min_y'] / float(sizes['Y'])
            y_max =  selected_atlas.y_size * zone_form.cleaned_data['max_y'] / float(sizes['Y'])
            z_min =  selected_atlas.z_size * zone_form.cleaned_data['min_z'] / float(sizes['Z'])
            z_max =  selected_atlas.z_size * zone_form.cleaned_data['max_z'] / float(sizes['Z'])
            name = zone_form.cleaned_data['name']
            name = zone_form.cleaned_data['name']

            zone = models.add_zone(name=name, owner=user, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, z_max=z_max, z_min=z_min)
            return HttpResponseRedirect('/atlas/?atlas='+str(atlasID)+'&zone='+str(zone.id))

        if (atlas_form.is_valid()):

            #Get selected atlas
            atlas_list = list(models.get_atlas())
            atlasID = int(atlas_form.cleaned_data['atlas'])
            for atlas in atlas_list:
                if atlas.id == atlasID:
                    selected_atlas = atlas
                    context_dict['selected_atlas'] = selected_atlas
                    break

            sizes = config.DEFAULT_SIZES
            context_dict['size_x'] = sizes['X']
            context_dict['size_y'] = sizes['Y']
            context_dict['size_z'] = sizes['Z']
            context_dict['atlas_size_x'] = selected_atlas.x_size
            context_dict['atlas_size_y'] = selected_atlas.y_size
            context_dict['atlas_size_z'] = selected_atlas.z_size

            context_dict['original_min_x'] = atlas_form.cleaned_data['min_x']
            context_dict['original_max_x'] = atlas_form.cleaned_data['max_x']
            context_dict['original_min_y'] = atlas_form.cleaned_data['min_y']
            context_dict['original_max_y'] = atlas_form.cleaned_data['max_y']
            context_dict['original_min_z'] = atlas_form.cleaned_data['min_z']
            context_dict['original_max_z'] = atlas_form.cleaned_data['max_z']
            context_dict['min_x'] = int(atlas_form.cleaned_data['min_x']*sizes['X']/float(selected_atlas.x_size))
            context_dict['max_x'] = int(atlas_form.cleaned_data['max_x']*sizes['X']/float(selected_atlas.x_size))
            context_dict['min_y'] = int(atlas_form.cleaned_data['min_y']*sizes['Y']/float(selected_atlas.y_size))
            context_dict['max_y'] = int(atlas_form.cleaned_data['max_y']*sizes['Y']/float(selected_atlas.y_size))
            context_dict['min_z'] = int(atlas_form.cleaned_data['min_z']*sizes['Z']/float(selected_atlas.z_size))
            context_dict['max_z'] = int(atlas_form.cleaned_data['max_z']*sizes['Z']/float(selected_atlas.z_size))
            pos_x = atlas_form.cleaned_data['pos_x']
            pos_y = atlas_form.cleaned_data['pos_y']
            pos_z = atlas_form.cleaned_data['pos_z']
            context_dict['pos_x'] = pos_x
            context_dict['pos_y'] = pos_y
            context_dict['pos_z'] = pos_z
            pos_x = int(selected_atlas.x_size * pos_x / float(sizes['X']))
            pos_y = int(selected_atlas.y_size * pos_y / float(sizes['Y']))
            pos_z = int(selected_atlas.z_size * pos_z / float(sizes['Z']))
            context_dict['original_pos_x'] = pos_x
            context_dict['original_pos_y'] = pos_y
            context_dict['original_pos_z'] = pos_z

            front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z, 0)
            side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x, 0)
            top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y, 0)

            context_dict['front_atlas'] = '/' + front_atlas
            context_dict['side_atlas'] = '/' + side_atlas
            context_dict['top_atlas'] = '/' + top_atlas

            return render(request, 'tfgWeb/zone.html', context=context_dict)

    else:
        sizes = config.DEFAULT_SIZES

        atlasID = int(request.GET.get('atlas'))
        selected_atlas= None
        for atlas in atlas_list:
            if atlas.id == atlasID:
                selected_atlas = atlas
                context_dict['selected_atlas'] = selected_atlas
                break

        pos_x = int(sizes['X']/2)
        pos_y = int(sizes['Y'] / 2)
        pos_z = int(sizes['Z'] / 2)
        context_dict['min_x'] = pos_x - int(sizes['X']/4)
        context_dict['max_x'] = pos_x + int(sizes['X']/4)
        context_dict['min_y'] = pos_y - int(sizes['Y']/4)
        context_dict['max_y'] = pos_y + int(sizes['Y']/4)
        context_dict['min_z'] = pos_z - int(sizes['Z']/4)
        context_dict['max_z'] = pos_z + int(sizes['Z']/4)
        context_dict['pos_x'] = pos_x
        context_dict['pos_y'] = pos_y
        context_dict['pos_z'] = pos_z
        pos_x = int(atlas_list[0].x_size * pos_x / float(sizes['X']))
        pos_y = int(atlas_list[0].y_size * pos_y / float(sizes['Y']))
        pos_z = int(atlas_list[0].z_size * pos_z / float(sizes['Z']))
        context_dict['original_pos_x'] = pos_x
        context_dict['original_pos_y'] = pos_y
        context_dict['original_pos_z'] = pos_z
        context_dict['original_min_x'] = pos_x - int(selected_atlas.x_size/4)
        context_dict['original_max_x'] = pos_x + int(selected_atlas.x_size/4)
        context_dict['original_min_y'] = pos_y - int(selected_atlas.y_size/4)
        context_dict['original_max_y'] = pos_y + int(selected_atlas.y_size/4)
        context_dict['original_min_z'] = pos_z - int(selected_atlas.z_size/4)
        context_dict['original_max_z'] = pos_z + int(selected_atlas.z_size/4)
        context_dict['size_x'] = sizes['X']
        context_dict['size_y'] = sizes['Y']
        context_dict['size_z'] = sizes['Z']
        context_dict['atlas_size_x'] = selected_atlas.x_size
        context_dict['atlas_size_y'] = selected_atlas.y_size
        context_dict['atlas_size_z'] = selected_atlas.z_size

        front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z, 0)
        side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x, 0)
        top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y, 0)
        context_dict['front_atlas'] = '/' + front_atlas
        context_dict['side_atlas'] = '/' + side_atlas
        context_dict['top_atlas'] = '/' + top_atlas

        return render(request, 'tfgWeb/zone.html', context=context_dict)

def atlas(request):

    context_dict = {}

    atlas_list = list(models.get_atlas())
    context_dict["atlas_list"] = atlas_list
    zones_list = list(models.get_zones())
    context_dict["zones_list"] = zones_list
    if request.user.is_authenticated:
        views_list = list(config.VISTAS_AUTH.keys())
    else:
        views_list = list(config.VISTAS_ANON.keys())
    context_dict['views_list'] = views_list

    if request.method == 'POST':

        atlas_form = AtlasForm(request.POST)

        if (atlas_form.is_valid()):

            # Get selected atlas
            atlas_list = list(models.get_atlas())
            atlasID = int(atlas_form.cleaned_data['atlas'])
            for atlas in atlas_list:
                if atlas.id == atlasID:
                    selected_atlas = atlas
                    context_dict['selected_atlas'] = selected_atlas
                    break

            zoneID = int(atlas_form.cleaned_data['zone'])
            selected_zone = None
            for zone in zones_list:
                if zone.id == zoneID:
                    selected_zone = zone
                    context_dict['selected_zone'] = selected_zone
                    break

            selected_view = atlas_form.cleaned_data['vista']
            if selected_view == 'BRAIN' or selected_view == 'SYNC':
                return HttpResponseRedirect('/experiment/?atlas=' + str(selected_atlas.id) + '&vista=' + selected_view + '&experiment=' + str(request.session['experiment']))

            sizes = config.DEFAULT_SIZES
            if (selected_zone != None):
                context_dict['min_x'] = int(sizes['X'] * selected_zone.min_x/float(selected_atlas.x_size))
                context_dict['max_x'] = int(sizes['X'] * selected_zone.max_x/float(selected_atlas.x_size))
                context_dict['min_y'] = int(sizes['Y'] * selected_zone.min_y/float(selected_atlas.y_size))
                context_dict['max_y'] = int(sizes['Y'] * selected_zone.max_y/float(selected_atlas.y_size))
                context_dict['min_z'] = int(sizes['Z'] * selected_zone.min_z/float(selected_atlas.z_size))
                context_dict['max_z'] = int(sizes['Z'] * selected_zone.max_z/float(selected_atlas.z_size))

            context_dict['size_x'] = sizes['X']
            context_dict['size_y'] = sizes['Y']
            context_dict['size_z'] = sizes['Z']
            pos_x = int(float(selected_atlas.x_size *  atlas_form.cleaned_data['pos_x'])/sizes['X'])
            pos_y = int(float(selected_atlas.y_size * atlas_form.cleaned_data['pos_y'])/sizes['Y'])
            pos_z = int(float(selected_atlas.z_size * atlas_form.cleaned_data['pos_z'])/sizes['Z'])

            #Comprueba si la posicion esta dentro de la zona. Si no, la cambia.
            if (selected_zone != None):
                if (pos_x<selected_zone.max_x and pos_x>selected_zone.min_x):
                    context_dict['pos_x'] = int(sizes['X'] * pos_x / float(selected_atlas.x_size))
                else:
                    context_dict['pos_x'] = int(sizes['X'] * ((selected_zone.min_x + selected_zone.max_x) / 2) / float(selected_atlas.x_size))
                if (pos_y < selected_zone.max_y and pos_y > selected_zone.min_y):
                    context_dict['pos_y'] = int(sizes['Y'] * pos_y / float(selected_atlas.y_size))
                else:
                    context_dict['pos_y'] = int(sizes['Y'] * ((selected_zone.min_y + selected_zone.max_y) / 2) / float(selected_atlas.y_size))
                if (pos_z < selected_zone.max_z and pos_z > selected_zone.min_z):
                    context_dict['pos_z'] = int(sizes['Z'] * pos_z / float(selected_atlas.z_size))
                else:
                    context_dict['pos_z'] = int(sizes['Z'] *((selected_zone.min_z + selected_zone.max_z) / 2)/ float(selected_atlas.z_size))
            else:
                context_dict['pos_x'] = int(sizes['X'] * pos_x/float(selected_atlas.x_size))
                context_dict['pos_y'] = int(sizes['Y'] * pos_y/float(selected_atlas.y_size))
                context_dict['pos_z'] = int(sizes['Z'] * pos_z/float(selected_atlas.z_size))

            context_dict['original_pos_x'] = pos_x
            context_dict['original_pos_y'] = pos_y
            context_dict['original_pos_z'] = pos_z

            front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z, 0)
            side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x, 0)
            top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y, 0)

            context_dict['front_atlas'] = '/' + front_atlas
            context_dict['side_atlas'] = '/' + side_atlas
            context_dict['top_atlas'] = '/' + top_atlas

            return render(request, 'tfgWeb/atlas.html', context=context_dict)

    else:
        sizes = config.DEFAULT_SIZES
        atlasID = int(request.GET.get('atlas'))

        selected_atlas= None
        for atlas in atlas_list:
            if atlas.id == atlasID:
                selected_atlas = atlas
                context_dict['selected_atlas'] = selected_atlas
                break

        zone = request.GET.get('zone')
        if zone != None:
            zoneID = int(zone)
            for zone in zones_list:
                if zone.id == zoneID:
                    selected_zone = zone
                    context_dict['selected_zone'] = selected_zone
                    break
            context_dict['min_x'] = int(sizes['X'] * selected_zone.min_x / float(selected_atlas.x_size))
            context_dict['max_x'] = int(sizes['X'] * selected_zone.max_x / float(selected_atlas.x_size))
            context_dict['min_y'] = int(sizes['Y'] * selected_zone.min_y / float(selected_atlas.y_size))
            context_dict['max_y'] = int(sizes['Y'] * selected_zone.max_y / float(selected_atlas.y_size))
            context_dict['min_z'] = int(sizes['Z'] * selected_zone.min_z / float(selected_atlas.z_size))
            context_dict['max_z'] = int(sizes['Z'] * selected_zone.max_z / float(selected_atlas.z_size))
            context_dict['selected_view'] = 'ATLAS'
            context_dict['pos_x'] = int(((context_dict['min_x']) + context_dict['max_x']) / 2.)
            context_dict['pos_y'] = int(((context_dict['min_y']) + context_dict['max_y']) / 2.)
            context_dict['pos_z'] = int(((context_dict['min_z']) + context_dict['max_z']) / 2.)
            context_dict['original_pos_x'] = int((selected_zone.min_x + selected_zone.max_x) / 2.)
            context_dict['original_pos_y'] = int((selected_zone.min_y + selected_zone.max_y) / 2.)
            context_dict['original_pos_z'] = int((selected_zone.min_z + selected_zone.max_z) / 2.)

        experiment = request.GET.get('experiment')
        if experiment != None:
            experimentID = int(experiment)
            request.session['experiment'] = experimentID

        pos_x = int(atlas_list[0].x_size / 2)
        pos_y = int(atlas_list[0].y_size / 2)
        pos_z = int(atlas_list[0].z_size / 2)
        context_dict['pos_x'] = int(sizes['X'] / 2)
        context_dict['pos_y'] = int(sizes['Y'] / 2)
        context_dict['pos_z'] = int(sizes['Z'] / 2)
        context_dict['original_pos_x'] = pos_x
        context_dict['original_pos_y'] = pos_y
        context_dict['original_pos_z'] = pos_z
        context_dict['size_x'] = sizes['X']
        context_dict['size_y'] = sizes['Y']
        context_dict['size_z'] = sizes['Z']

        front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z, 0)
        side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x, 0)
        top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y, 0)
        context_dict['front_atlas'] = '/' + front_atlas
        context_dict['side_atlas'] = '/' + side_atlas
        context_dict['top_atlas'] = '/' + top_atlas

        return render(request, 'tfgWeb/atlas.html', context=context_dict)

def index(request):

    context_dict = {}

    try:
        user = request.user
    except:
        user = None

    experiment_list = models.get_experiments(user)
    context_dict['experiment_list'] = experiment_list
    context_dict['orders'] = config.ORDERS.keys()
    context_dict['upload_form'] = UploadForm()

    if request.method == 'POST':

        upload_form = UploadForm(request.POST, request.FILES)

        if (upload_form.is_valid()):

            path = request.FILES['file'].temporary_file_path()
            order = upload_form.cleaned_data['serie']

            context_dict['upload_form'] = upload_form

            file = request.FILES['file']
            parts = file.name.split('.')

            if (len(parts) == 1):
                raise ValueError("Type not allowed")
            elif (parts[len(parts) - 1] == 'lif'):
                utils.save_lif(path, request.user, order)
            elif (parts[len(parts) - 1] == 'h5'):
                utils.save_h5(path, request.user, order)

            context_dict['upload_form'] = UploadForm()
        else:
            context_dict['upload_form'] = UploadForm()

    return render(request, 'tfgWeb/index.html', context=context_dict)

def experiment(request):

    context_dict = {}

    try:
        selected_experiment = models.get_experiment(request.GET.get('experiment'))
    except:
        experiment_id = request.session['experiment']
        selected_experiment = models.get_experiment(experiment_id)

    series_list = list(selected_experiment.get_galerys())
    atlas_list = list(models.get_atlas())
    if request.user.is_authenticated:
        views_list = list(config.VISTAS_AUTH.keys())
    else:
        views_list = list(config.VISTAS_ANON.keys())
    zones_list = list(models.get_zones())
    context_dict['zones_list'] = zones_list
    context_dict['views_list'] = views_list
    context_dict['series'] = series_list
    context_dict['atlas_list'] = atlas_list

    if request.method == 'POST':

        info_form = InfoForm(request.POST)

        if (info_form.is_valid()):

            serieID = int(info_form.cleaned_data['serie'])
            for serie in series_list:
                if serie.id == serieID:
                    selected_serie = serie
                    context_dict['selected_serie'] = selected_serie
                    break

            atlasID = int(info_form.cleaned_data['atlas'])
            for atlas in atlas_list:
                if atlas.id == atlasID:
                    selected_atlas = atlas
                    context_dict['selected_atlas'] = selected_atlas
                    break


            context_dict['zones_list'] = zones_list
            zoneID = int(info_form.cleaned_data['zone'])
            for zone in zones_list:
                if zone.id == zoneID:
                    selected_zone = zone
                    context_dict['selected_zone'] = selected_zone
                    break

            pos_x_atlas = 0
            pos_y_atlas = 0
            pos_z_atlas = 0

            width =  info_form.cleaned_data['width']
            height =  info_form.cleaned_data['height']
            depth =  info_form.cleaned_data['depth']

            pos_x = info_form.cleaned_data['pos_x']*selected_serie.x_size/width
            pos_y = info_form.cleaned_data['pos_y']*selected_serie.y_size/height
            pos_z = info_form.cleaned_data['pos_z']*selected_serie.z_size/depth


            selected_view = info_form.cleaned_data['vista']

            zoneID = info_form.cleaned_data['zone']
            selected_zone = None
            for zone in zones_list:
                if zone.id == int(zoneID):
                    selected_zone = zone
                    context_dict['selected_zone'] = zone

            if selected_view=='ATLAS':
                return HttpResponseRedirect('/atlas?atlas='+ str(selected_atlas.id) + '&experiment=' + str(request.session['experiment']))
            elif selected_view == 'SYNC' and selected_zone != None:
                pos_x_atlas = selected_zone.min_x + int((selected_zone.max_x - selected_zone.min_x) * pos_x / float(selected_serie.x_size))
                pos_y_atlas = selected_zone.min_y + int((selected_zone.max_y - selected_zone.min_y) * pos_y / float(selected_serie.y_size))
                pos_z_atlas = selected_zone.min_z + int((selected_zone.max_z - selected_zone.min_z) * pos_z / float(selected_serie.z_size))

            sizes = config.DEFAULT_SIZES
            context_dict['atlas_size_x'] = sizes['X']
            context_dict['atlas_size_y'] = sizes['Y']
            context_dict['atlas_size_z'] = sizes['Z']
            context_dict['width'] = width
            context_dict['height'] = height
            context_dict['depth'] = depth
            context_dict['selected_view'] = selected_view
            time = info_form.cleaned_data['time']

            front_image = selected_serie.get_image(selected_experiment.front_axis, pos_z, time)
            side_image = selected_serie.get_image(selected_experiment.side_axis, pos_x, time)
            top_image = selected_serie.get_image(selected_experiment.top_axis, pos_y, time)

            context_dict['front_image'] = '/' + front_image
            context_dict['top_image'] = '/' + top_image
            context_dict['side_image'] = '/' + side_image

            front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z_atlas, 0)
            side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x_atlas, 0)
            top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y_atlas, 0)

            context_dict['front_atlas'] = '/' + front_atlas
            context_dict['top_atlas'] = '/' + top_atlas
            context_dict['side_atlas'] = '/' + side_atlas

            context_dict['pos_x'] = pos_x*width/selected_serie.x_size
            context_dict['pos_y'] = pos_y*height/selected_serie.y_size
            context_dict['pos_z'] = pos_z*depth/selected_serie.z_size
            context_dict['pos_x_start'] = info_form.cleaned_data['pos_x_start']
            context_dict['pos_y_start'] = info_form.cleaned_data['pos_y_start']
            context_dict['pos_z_start'] = info_form.cleaned_data['pos_z_start']
            context_dict['pos_x_atlas'] = pos_x_atlas
            context_dict['pos_y_atlas'] = pos_y_atlas
            context_dict['pos_z_atlas'] = pos_z_atlas
            context_dict['time'] = time
            context_dict['total_times'] = selected_serie.total_times - 1
            context_dict['upload_form'] = UploadForm()

    else:

        context_dict['pos_x'] = 0
        context_dict['pos_y'] = 0
        context_dict['pos_z'] = 0
        context_dict['pos_x_atlas'] = 0
        context_dict['pos_y_atlas'] = 0
        context_dict['pos_z_atlas'] = 0
        context_dict['pos_x_start'] = 0
        context_dict['pos_y_start'] = 0
        context_dict['pos_z_start'] = 0
        context_dict['time'] = 0

        atlas_list = list(models.get_atlas())
        atlasID = request.GET.get('atlas')
        if atlasID != None:
            atlasID = int(atlasID)
            for atlas in atlas_list:
                if atlas.id == atlasID:
                    selected_atlas = atlas
                    context_dict['selected_atlas'] = selected_atlas
                    break
        else:
            selected_atlas = atlas_list[0]

        context_dict['total_times'] = series_list[0].total_times - 1
        context_dict['selected_serie'] = series_list[0]

        context_dict['front_image'] = '/' + series_list[0].get_image(series_list[0].experiment.front_axis, 0, 0)
        context_dict['top_image'] = '/' + series_list[0].get_image(series_list[0].experiment.top_axis, 0, 0)
        context_dict['side_image'] = '/' + series_list[0].get_image(series_list[0].experiment.side_axis, 0, 0)

        context_dict['front_atlas'] = '/' + atlas_list[0].get_image(selected_atlas.experiment.front_axis, 0, 0)
        context_dict['side_atlas'] = '/' + atlas_list[0].get_image(selected_atlas.experiment.side_axis, 0, 0)
        context_dict['top_atlas'] = '/' + atlas_list[0].get_image(selected_atlas.experiment.top_axis, 0, 0)

        sizes = config.DEFAULT_SIZES
        context_dict['atlas_size_x'] = sizes['X']
        context_dict['atlas_size_y'] = sizes['Y']
        context_dict['atlas_size_z'] = sizes['Z']
        image_sizes = utils.get_image_sizes(sizes['X'],sizes['Y'],sizes['Z'],series_list[0].x_size,series_list[0].y_size,series_list[0].z_size)
        context_dict['width'] = image_sizes['X']
        context_dict['height'] = image_sizes['Y']
        context_dict['depth'] = image_sizes['Z']
        view = request.GET.get('vista')
        if view != None:
            context_dict['selected_view'] = view
        else:
            context_dict['selected_view'] = 'BRAIN'

        context_dict['upload_form'] = UploadForm()
        request.session['experiment'] = selected_experiment.id
        context_dict['zones_list'] = zones_list

    return render(request, 'tfgWeb/experiment.html', context=context_dict)

def info(request):
    context_dict = {}

    try:
        selected_experiment = request.GET.get('experiment')
        context_dict['info'] = selected_experiment.get_info()
    except:
        raise ValueError('Cannot find the experiment')

    return render(request, 'tfgWeb/info.html', context=context_dict)

def register(request):

    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.username = user
            profile.save()
            registered = True

        else:
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    return render(request,'tfgWeb/register.html',{'user_form': user_form,'profile_form': profile_form,'registered': registered})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")
    else:
        return render(request, 'tfgWeb/login.html', {})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))