from django.shortcuts import render
from tfgWeb.models import Serie, Image, Atlas, AtlasImage, Muestra
from tfgWeb import utils, config
import numpy as np
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from tfgWeb.forms import UserForm, UserProfileForm
from django.contrib.auth.models import User
from tfgWeb.forms import InfoForm, UploadForm

def index(request):

    context_dict = {}

    try:
        user = request.user
    except:
        user = None
    try:
        if user.is_anonymous():
            series_list = Serie.objects.filter(Q(owner=User.objects.get_by_natural_key(config.ADMIN_NAME)))
        else:
            series_list = Serie.objects.filter(Q(owner=user) | Q(owner=User.objects.get_by_natural_key(config.ADMIN_NAME)))
        atlas_list = Atlas.objects.filter()
        muestras_list = config.RESOLUTIONS.keys()

        context_dict['series'] = list(series_list)
        context_dict['atlas_list'] = list(atlas_list)
        context_dict['muestras'] = muestras_list

        if request.method == 'POST':

            info_form = InfoForm(request.POST)
            upload_form = UploadForm(request.POST, request.FILES)

            if (info_form.is_valid()):

                serieID = int(info_form.cleaned_data['serie'])
                for serie in list(series_list):
                    if serie.id == serieID:
                        selected_serie = serie
                        break

                atlasID = int(info_form.cleaned_data['atlas'])
                for atlas in list(atlas_list):
                    if atlas.id == atlasID:
                        selected_atlas = atlas
                        break

                pos_x = info_form.cleaned_data['pos_x']
                pos_y = info_form.cleaned_data['pos_y']
                pos_z = info_form.cleaned_data['pos_z']
                time = info_form.cleaned_data['time']

                selected_muestra = info_form.cleaned_data['muestra']
                muestra = selected_serie.get_muestra(selected_muestra)
                matrix = muestra.get_matrix(time)

                """if not request.session.get('serie_name')==selected_serie.name:
                    matrix5d = get_matrix(serieID)
                    request.session['matrix'] = matrix5d
                    request.session['serie_name'] = selected_serie.name
                    print request.session.get('serie_name')
                else:
                    matrix5d = request.session['matrix']"""


                context_dict['pos_x'] = pos_x
                context_dict['pos_y'] = pos_y
                context_dict['pos_z'] = pos_z
                context_dict['time'] = time
                selected_serie.total_times -= 1
                context_dict['selected_serie'] = selected_serie
                context_dict['selected_atlas'] = selected_atlas
                context_dict['selected_muestra'] = selected_muestra

                shape = np.shape(matrix)
                context_dict['size_x'] = np.round(shape[0]/3)
                context_dict['size_y'] = np.round(shape[1]/3)
                context_dict['size_z'] = np.round(shape[2]/3)

                front_image = utils.get_front_image(image5d=matrix,pos_y=pos_y,time=time, user=user.username)
                top_image = utils.get_top_image(image5d=matrix, pos_z=pos_z, time=time, user=user.username)
                side_image = utils.get_side_image(image5d=matrix, pos_x=pos_x, time=time, user=user.username)

                context_dict['front_image'] = '/' + front_image
                context_dict['top_image'] = '/' + top_image
                context_dict['side_image'] = '/' + side_image

            if (upload_form.is_valid()):
                path = request.FILES['file'].temporary_file_path()
                context_dict['upload_form'] = upload_form

                file = request.FILES['file']
                parts = file.name.split('.')
                if (len(parts)==1):
                    raise ValueError("Type not allowed")
                elif (parts[len(parts)-1]=='lif'):
                    utils.save_lif(path, request.user)
                elif (parts[len(parts) - 1] == 'h5'):
                    utils.save_h5(path, request.user)
            else:
                print upload_form.errors
                context_dict['upload_form'] = UploadForm()
        else:
            context_dict['front_image'] = None
            context_dict['top_image'] = None
            context_dict['side_image'] = None
            context_dict['pos_x'] = 0
            context_dict['pos_y'] = 0
            context_dict['pos_z'] = 0
            context_dict['time'] = 0
            if series_list:
                series_list[0].total_times -= 1
                context_dict['selected_serie'] = series_list[0]
            context_dict['upload_form'] = UploadForm()

    except Exception as e:
        print e.message
        context_dict['series'] = None
        context_dict['front_image'] = None
        context_dict['top_image'] = None
        context_dict['side_image'] = None
        context_dict['selected_serie'] = None

    return render(request, 'tfgWeb/index.html', context=context_dict)

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