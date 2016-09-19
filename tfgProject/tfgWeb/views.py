from django.shortcuts import render
from time import time as date
from tfgWeb import models
from tfgWeb import utils, config
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from tfgWeb.forms import UserForm, UserProfileForm, InfoForm, UploadForm, NameForm, DeleteForm, AtlasForm
import json

def index(request):

    context_dict = {}

    try:
        user = request.user
    except:
        user = None

    experiment_list = models.get_experiments(user)
    atlas_list = models.get_atlas()
    context_dict['experiment_list'] = experiment_list
    context_dict['atlas_list'] = atlas_list
    context_dict['atlas_experiment'] = atlas_list[0].experiment
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
    sizes = config.DEFAULT_SIZES
    if request.user.is_authenticated():
        views_list = list(config.VISTAS_AUTH.keys())
    else:
        views_list = list(config.VISTAS_ANON.keys())

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

            selected_view = info_form.cleaned_data['view']

            if selected_view=='ATLAS':
                context_dict['selected_view'] = 'ATLAS'
                context_dict['navigate'] = info_form.cleaned_data['navigate']
                context_dict['time'] = 0
                context_dict['pos_x'] = info_form.cleaned_data['pos_x']
                context_dict['pos_y'] = info_form.cleaned_data['pos_y']
                context_dict['pos_z'] = info_form.cleaned_data['pos_z']
                context_dict['canvas_size_x'] = sizes['X']
                context_dict['canvas_size_y'] = sizes['Y']
                context_dict['canvas_size_z'] = sizes['Z']
                pos_x_atlas = int(info_form.cleaned_data['pos_x_atlas'] * selected_atlas.x_size / float(sizes['X']))
                pos_y_atlas = int(info_form.cleaned_data['pos_y_atlas'] * selected_atlas.y_size / float(sizes['Y']))
                pos_z_atlas = int(info_form.cleaned_data['pos_z_atlas'] * selected_atlas.z_size / float(sizes['Z']))
                context_dict['pos_x_atlas'] = info_form.cleaned_data['pos_x_atlas']
                context_dict['pos_y_atlas'] = info_form.cleaned_data['pos_y_atlas']
                context_dict['pos_z_atlas'] = info_form.cleaned_data['pos_z_atlas']

                front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z_atlas, 0)
                side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x_atlas, 0)
                top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y_atlas, 0)

                context_dict['front_atlas'] = '/' + front_atlas
                context_dict['top_atlas'] = '/' + top_atlas
                context_dict['side_atlas'] = '/' + side_atlas

                context_dict['pos_x_start'] = info_form.cleaned_data['pos_x_start']
                context_dict['pos_y_start'] = info_form.cleaned_data['pos_y_start']
                context_dict['pos_z_start'] = info_form.cleaned_data['pos_z_start']
                context_dict['width'] = info_form.cleaned_data['width']
                context_dict['height'] = info_form.cleaned_data['height']
                context_dict['depth'] = info_form.cleaned_data['depth']

            elif selected_view == 'BRAIN':
                context_dict['selected_view'] = 'BRAIN'
                context_dict['navigate'] = info_form.cleaned_data['navigate']
                context_dict['pos_x_atlas'] = info_form.cleaned_data['pos_x_atlas']
                context_dict['pos_y_atlas'] = info_form.cleaned_data['pos_y_atlas']
                context_dict['pos_z_atlas'] = info_form.cleaned_data['pos_z_atlas']
                context_dict['canvas_size_x'] = int(selected_serie.x_size/2)
                context_dict['canvas_size_y'] = int(selected_serie.y_size/2)
                context_dict['canvas_size_z'] = int(selected_serie.z_size/2)
                context_dict['width'] =  info_form.cleaned_data['width']
                context_dict['height'] =  info_form.cleaned_data['height']
                context_dict['depth'] =  info_form.cleaned_data['depth']

                pos_x = info_form.cleaned_data['pos_x']
                pos_y = info_form.cleaned_data['pos_y']
                pos_z = info_form.cleaned_data['pos_z']
                if pos_x == -1 and pos_y== -1 and pos_z== -1:
                    pos_x = int(selected_serie.x_size / 2)
                    pos_y = int(selected_serie.y_size / 2)
                    pos_z = int(selected_serie.z_size / 2)
                    context_dict['pos_x'] = int(selected_serie.x_size / 4)
                    context_dict['pos_y'] = int(selected_serie.y_size / 4)
                    context_dict['pos_z'] = int(selected_serie.z_size / 4)
                else:
                    pos_x = pos_x * 2
                    pos_y = pos_y * 2
                    pos_z = pos_z * 2
                    context_dict['pos_x'] = info_form.cleaned_data['pos_x']
                    context_dict['pos_y'] = info_form.cleaned_data['pos_y']
                    context_dict['pos_z'] = info_form.cleaned_data['pos_z']


                var_time = info_form.cleaned_data['time']
                context_dict['time'] = var_time

                front_image = selected_serie.get_image(selected_experiment.front_axis, pos_z, var_time)
                side_image = selected_serie.get_image(selected_experiment.side_axis, pos_x, var_time)
                top_image = selected_serie.get_image(selected_experiment.top_axis, pos_y, var_time)

                context_dict['front_image'] = '/' + front_image
                context_dict['top_image'] = '/' + top_image
                context_dict['side_image'] = '/' + side_image
                context_dict['pos_x_start'] = 0
                context_dict['pos_y_start'] = 0
                context_dict['pos_z_start'] = 0

            elif selected_view == 'SYNC':
                if info_form.cleaned_data['navigate']==0:
                    if (selected_serie.width>-1 and selected_serie.height>-1 and selected_serie.depth>-1 and selected_serie.start_x>-1 and selected_serie.start_y>-1 and selected_serie.start_z>-1):
                        navigate = 1
                    else:
                        navigate = -1
                    context_dict['navigate'] = navigate
                else:
                    navigate = info_form.cleaned_data['navigate']
                    context_dict['navigate'] = navigate

                ##CALIBRAR##
                if navigate==-1:
                    #Experimento
                    width =  info_form.cleaned_data['width']
                    height =  info_form.cleaned_data['height']
                    depth =  info_form.cleaned_data['depth']

                    pos_x = info_form.cleaned_data['pos_x']
                    pos_y = info_form.cleaned_data['pos_y']
                    pos_z = info_form.cleaned_data['pos_z']

                    image_sizes = utils.get_image_sizes(sizes['X'], sizes['Y'], sizes['Z'], selected_serie)
                    if width == -1:
                        if selected_serie.width > -1:
                            context_dict['width'] = int(selected_serie.width * image_sizes['X'] / float(selected_serie.x_size))
                        else:
                            context_dict['width'] = image_sizes['X']
                        if pos_x == -1:
                            pos_x = int(image_sizes['X']/4)
                            context_dict['pos_x'] = pos_x
                        else:
                            context_dict['pos_x'] = pos_x
                            pos_x = pos_x * 2
                    else:
                        context_dict['width'] = width
                        context_dict['pos_x'] = pos_x
                        pos_x = int(pos_x * selected_serie.x_size / width)
                    if height == -1:
                        if selected_serie.height>-1:
                            context_dict['height'] = int(selected_serie.height* image_sizes['Y'] / float(selected_serie.y_size))
                        else:
                            context_dict['height'] = image_sizes['Y']
                        if pos_y == -1:
                            pos_y = int(image_sizes['Y']/4)
                            context_dict['pos_y'] = pos_y
                        else:
                            context_dict['pos_y'] = pos_y
                            pos_y = pos_y*2
                    else:
                        context_dict['height'] = height
                        context_dict['pos_y'] = pos_y
                        pos_y = int(pos_y * selected_serie.y_size / height)
                    if depth == -1:
                        if selected_serie.depth > -1:
                            context_dict['depth'] = int(selected_serie.depth * image_sizes['Z'] / float(selected_serie.z_size))
                        else:
                            context_dict['depth'] = image_sizes['Z']
                        if pos_z == -1:
                            pos_z = int(image_sizes['Z']/4)
                            context_dict['pos_z'] = pos_z
                        else:
                            context_dict['pos_z'] = pos_z
                            pos_z = pos_z * 2
                    else:
                        context_dict['depth']  = depth
                        context_dict['pos_z'] = pos_z
                        pos_z = int(pos_z * selected_serie.z_size / depth)

                    time = info_form.cleaned_data['time']
                    front_image = selected_serie.get_image(selected_experiment.front_axis, pos_z, time)
                    side_image = selected_serie.get_image(selected_experiment.side_axis, pos_x, time)
                    top_image = selected_serie.get_image(selected_experiment.top_axis, pos_y, time)
                    context_dict['front_image'] = '/' + front_image
                    context_dict['top_image'] = '/' + top_image
                    context_dict['side_image'] = '/' + side_image
                    context_dict['pos_x_start'] = info_form.cleaned_data['pos_x_start']
                    context_dict['pos_y_start'] = info_form.cleaned_data['pos_y_start']
                    context_dict['pos_z_start'] = info_form.cleaned_data['pos_z_start']
                    context_dict['time'] = time
                    #Atlas
                    context_dict['pos_x_atlas'] = info_form.cleaned_data['pos_x_atlas']
                    context_dict['pos_y_atlas'] = info_form.cleaned_data['pos_y_atlas']
                    context_dict['pos_z_atlas'] = info_form.cleaned_data['pos_z_atlas']
                    pos_x_atlas = int(info_form.cleaned_data['pos_x_atlas'] * selected_atlas.x_size / float(sizes['X']))
                    pos_y_atlas = int(info_form.cleaned_data['pos_y_atlas'] * selected_atlas.y_size / float(sizes['Y']))
                    pos_z_atlas = int(info_form.cleaned_data['pos_z_atlas'] * selected_atlas.z_size / float(sizes['Z']))
                    front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z_atlas, 0)
                    side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x_atlas, 0)
                    top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y_atlas, 0)
                    context_dict['front_atlas'] = '/' + front_atlas
                    context_dict['top_atlas'] = '/' + top_atlas
                    context_dict['side_atlas'] = '/' + side_atlas
                    context_dict['canvas_size_x'] = sizes['X']
                    context_dict['canvas_size_y'] = sizes['Y']
                    context_dict['canvas_size_z'] = sizes['Z']
                    context_dict['navigate'] = -1
                else: ###NAVEGAR###
                    if (info_form.cleaned_data['pos_x_start'] == -1 and info_form.cleaned_data['pos_y_start'] == -1 and info_form.cleaned_data['pos_z_atlas'] == -1):
                        if (selected_serie.start_x > 0 or selected_serie.start_y>0 or selected_serie.start_z > 0):
                            pos_x_start = selected_serie.start_x
                            pos_y_start = selected_serie.start_y
                            pos_z_start = selected_serie.start_z
                            context_dict['pos_x_start'] = pos_x_start
                            context_dict['pos_y_start'] = pos_y_start
                            context_dict['pos_z_start'] = pos_z_start
                        else:
                            pos_x_start = 0
                            pos_y_start = 0
                            pos_z_start = 0
                            context_dict['pos_x_start'] = pos_x_start
                            context_dict['pos_y_start'] = pos_y_start
                            context_dict['pos_z_start'] = pos_z_start
                    else:
                        pos_x_start = int(info_form.cleaned_data['pos_x_start'] * selected_atlas.x_size / float(sizes['X']))
                        pos_y_start = int(info_form.cleaned_data['pos_y_start'] * selected_atlas.y_size / float(sizes['Y']))
                        pos_z_start = int(info_form.cleaned_data['pos_z_start'] * selected_atlas.z_size / float(sizes['Z']))
                        context_dict['pos_x_start'] = info_form.cleaned_data['pos_x_start']
                        context_dict['pos_y_start'] = info_form.cleaned_data['pos_y_start']
                        context_dict['pos_z_start'] = info_form.cleaned_data['pos_z_start']

                    width = int(info_form.cleaned_data['width'] * selected_atlas.x_size / float(sizes['X']))
                    height = int(info_form.cleaned_data['height'] * selected_atlas.y_size / float(sizes['Y']))
                    depth = int(info_form.cleaned_data['depth'] * selected_atlas.z_size / float(sizes['Z']))
                    context_dict['width'] = info_form.cleaned_data['width']
                    context_dict['height'] = info_form.cleaned_data['height']
                    context_dict['depth'] = info_form.cleaned_data['depth']


                    if info_form.cleaned_data['save']==1:
                        selected_serie.set_size(width,height,depth)
                        selected_serie.set_position(pos_x_start,pos_y_start,pos_z_start)

                    # Atlas
                    context_dict['pos_x_atlas'] = info_form.cleaned_data['pos_x_atlas']
                    context_dict['pos_y_atlas'] = info_form.cleaned_data['pos_y_atlas']
                    context_dict['pos_z_atlas'] = info_form.cleaned_data['pos_z_atlas']
                    pos_x_atlas = int(info_form.cleaned_data['pos_x_atlas'] * selected_atlas.x_size / float(sizes['X']))
                    pos_y_atlas = int(info_form.cleaned_data['pos_y_atlas'] * selected_atlas.y_size / float(sizes['Y']))
                    pos_z_atlas = int(info_form.cleaned_data['pos_z_atlas'] * selected_atlas.z_size / float(sizes['Z']))
                    front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z_atlas, 0)
                    side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x_atlas, 0)
                    top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y_atlas, 0)
                    context_dict['front_atlas'] = '/' + front_atlas
                    context_dict['top_atlas'] = '/' + top_atlas
                    context_dict['side_atlas'] = '/' + side_atlas
                    context_dict['canvas_size_x'] = sizes['X']
                    context_dict['canvas_size_y'] = sizes['Y']
                    context_dict['canvas_size_z'] = sizes['Z']

                    #Experimento -> si imagen dentro de zona calibrada
                    if utils.hit_experiment(pos_x_atlas,pos_y_atlas,pos_z_atlas, selected_serie):
                        pos_x_img = int((pos_x_atlas - pos_x_start) * selected_serie.x_size / float(width))
                        pos_y_img = int((pos_y_atlas - pos_y_start) * selected_serie.y_size / float(height))
                        pos_z_img = int((pos_z_atlas - pos_z_start) * selected_serie.z_size / float(depth))
                        time = info_form.cleaned_data['time']
                        front_image = selected_serie.get_image(selected_experiment.front_axis, pos_z_img, time)
                        side_image = selected_serie.get_image(selected_experiment.side_axis, pos_x_img, time)
                        top_image = selected_serie.get_image(selected_experiment.top_axis, pos_y_img, time)
                        context_dict['front_image'] = '/' + front_image
                        context_dict['top_image'] = '/' + top_image
                        context_dict['side_image'] = '/' + side_image
                        context_dict['time'] = time
                        context_dict['pos_x'] = pos_x_img
                        context_dict['pos_y'] = pos_y_img
                        context_dict['pos_z'] = pos_z_img
                    else:
                        context_dict['time'] = info_form.cleaned_data['time']
                        context_dict['pos_x'] = 0
                        context_dict['pos_y'] = 0
                        context_dict['pos_z'] = 0

                    context_dict['selected_view'] = 'SYNC'
                    context_dict['navigate'] = 1


            context_dict['selected_view'] = selected_view
            context_dict['total_times'] = selected_serie.total_times - 1
            context_dict['upload_form'] = UploadForm()

    else:
        context_dict['navigate'] = 0
        context_dict['pos_x'] = -1
        context_dict['pos_y'] = -1
        context_dict['pos_z'] = -1
        context_dict['pos_x_atlas'] = 0
        context_dict['pos_y_atlas'] = 0
        context_dict['pos_z_atlas'] = 0
        context_dict['pos_x_start'] = -1
        context_dict['pos_y_start'] = -1
        context_dict['pos_z_start'] = -1
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

        pos_x = int(sizes[selected_atlas.experiment.side_axis] / 2)
        pos_y = int(sizes[selected_atlas.experiment.top_axis] / 2)
        pos_z = int(sizes[selected_atlas.experiment.front_axis] / 2)

        context_dict['front_atlas'] = '/' + selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z, 0)
        context_dict['side_atlas'] = '/' + selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x, 0)
        context_dict['top_atlas'] = '/' + selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y, 0)

        image_list = list(selected_experiment.get_galerys())
        context_dict['series'] = image_list

        sizes = config.DEFAULT_SIZES
        context_dict['canvas_size_x'] = sizes['X']
        context_dict['canvas_size_y'] = sizes['Y']
        context_dict['canvas_size_z'] = sizes['Z']
        context_dict['pos_x_atlas'] = int(sizes['X']/2)
        context_dict['pos_y_atlas'] = int(sizes['Y'] / 2)
        context_dict['pos_z_atlas'] = int(sizes['Z'] / 2)
        context_dict['navigate'] = 0;
        context_dict['pos_x'] = -1
        context_dict['pos_y'] = -1
        context_dict['pos_z'] = -1
        context_dict['width'] = -1
        context_dict['height'] = -1
        context_dict['depth'] = -1

        context_dict['selected_view'] = 'ATLAS'
        request.session['experiment'] = selected_experiment.id

    return render(request, 'tfgWeb/experiment.html', context=context_dict)

def info(request):
    context_dict = {}
    try:
        selected_experiment = models.get_experiment(request.GET.get('experiment'))
    except:
        raise ValueError('Cannot find the experiment')

    if request.method == 'POST':
        name_form = NameForm(request.POST)
        delete_form = DeleteForm(request.POST)
        if (name_form.is_valid()):
            name = name_form.cleaned_data['name']
            selected_experiment.change_name(name)
        elif (delete_form.is_valid()):
            if not selected_experiment.is_atlas:
                selected_experiment.delete_experiment()
                return HttpResponseRedirect(reverse('index'))

    context_dict['experiment'] = selected_experiment
    aux = json.loads(selected_experiment.info)
    context_dict['metadata_list'] = aux
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

def upload_experiment(request):

    context_dict = {}
    context_dict['upload_form'] = UploadForm()

    if request.POST:
        upload_form = UploadForm(request.POST, request.FILES)

        if (upload_form.is_valid()):

            path = request.FILES['file'].temporary_file_path()
            top_axis = upload_form.cleaned_data['top_axis']
            front_axis = upload_form.cleaned_data['front_axis']
            side_axis = upload_form.cleaned_data['side_axis']
            name = upload_form.cleaned_data['name']

            context_dict['upload_form'] = upload_form

            file = request.FILES['file']
            parts = file.name.split('.')

            if (len(parts) == 1):
                context_dict['message'] = 'File type not allowed'
                return render(request, 'tfgWeb/upload_experiment.html', context=context_dict)
            elif (parts[len(parts) - 1] == 'lif'):
                utils.save_lif(path, request.user, top_axis, side_axis, front_axis,name=name)
            elif (parts[len(parts) - 1] == 'h5'):
                utils.save_h5(path, request.user, top_axis, side_axis, front_axis,name=name)
            else:
                context_dict['message'] = 'File type not allowed'
                return render(request, 'tfgWeb/upload_experiment.html', context=context_dict)

            return render(request, 'tfgWeb/index.html', context=context_dict)
        else:
            context_dict['message'] = 'The values are not valid'
            return render(request, 'tfgWeb/upload_experiment.html', context=context_dict)

    return render(request, 'tfgWeb/upload_experiment.html', context=context_dict)

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

def atlas(request):
    context_dict = {}

    atlas_list = list(models.get_atlas())
    context_dict["atlas_list"] = atlas_list
    sizes = config.DEFAULT_SIZES


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

            pos_x = atlas_form.cleaned_data['pos_x']
            pos_y = atlas_form.cleaned_data['pos_y']
            pos_z = atlas_form.cleaned_data['pos_z']
            context_dict['pos_x'] = pos_x
            context_dict['pos_y'] = pos_y
            context_dict['pos_z'] = pos_z
            context_dict['size_x'] = sizes['X']
            context_dict['size_y'] = sizes['Y']
            context_dict['size_z'] = sizes['Z']

            pos_x = int(pos_x * selected_atlas.x_size / float(sizes['X']))
            pos_y = int(pos_y * selected_atlas.y_size / float(sizes['Y']))
            pos_z = int(pos_z * selected_atlas.z_size / float(sizes['Z']))

            front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z, 0)
            side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x, 0)
            top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y, 0)

            context_dict['front_atlas'] = '/' + front_atlas
            context_dict['top_atlas'] = '/' + top_atlas
            context_dict['side_atlas'] = '/' + side_atlas

    else:
        atlasID = request.GET.get('atlas')
        for atlas in atlas_list:
            if atlas.id == int(atlasID):
                selected_atlas = atlas
                context_dict['selected_atlas'] = selected_atlas
                break
        context_dict['pos_x'] = int(sizes['X']/2.)
        context_dict['pos_y'] = int(sizes['X']/2.)
        context_dict['pos_z'] = int(sizes['X']/2.)
        context_dict['size_x'] = sizes['X']
        context_dict['size_y'] = sizes['Y']
        context_dict['size_z'] = sizes['Z']
        pos_x = int(selected_atlas.x_size/2.)
        pos_y = int(selected_atlas.y_size / 2.)
        pos_z = int(selected_atlas.z_size / 2.)

        front_atlas = selected_atlas.get_image(selected_atlas.experiment.front_axis, pos_z, 0)
        side_atlas = selected_atlas.get_image(selected_atlas.experiment.side_axis, pos_x, 0)
        top_atlas = selected_atlas.get_image(selected_atlas.experiment.top_axis, pos_y, 0)

        context_dict['front_atlas'] = '/' + front_atlas
        context_dict['top_atlas'] = '/' + top_atlas
        context_dict['side_atlas'] = '/' + side_atlas

    return render(request, 'tfgWeb/atlas.html', context=context_dict)


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))