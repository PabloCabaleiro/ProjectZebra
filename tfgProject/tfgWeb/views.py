from django.shortcuts import render
from tfgWeb.models import Serie, Image
from tfgWeb import utils
import numpy as np
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from tfgWeb.forms import UserForm, UserProfileForm
from django.contrib.auth.models import User
from PIL import Image as PILImage

def index(request):

    context_dict = {}

    pos_x = 500
    pos_y = 500
    pos_z = 30
    time = 0

    context_dict['pos_x'] = pos_x
    context_dict['pos_y'] = pos_y
    context_dict['pos_z'] = pos_z
    context_dict['time'] = time
    try:
        user = request.user
    except:
        user = None
    try:
        series_list = Serie.objects.filter(Q(owner=user) | Q(owner=User.objects.get_by_natural_key(utils.ADMIN_NAME)))
        context_dict['series'] = list(series_list)

        serie = series_list[0]  #Pillamos serie arbitraria
        matrix5d = get_matrix(serie.id)
        context_dict['serie_selected'] = serie

        front_image = utils.get_front_image(image5d=matrix5d,pos_y=pos_y,time=time, user=user.username)
        top_image = utils.get_top_image(image5d=matrix5d, pos_z=pos_z, time=time, user=user.username)
        side_image = utils.get_side_image(image5d=matrix5d, pos_x=pos_x, time=time, user=user.username)

        context_dict['front_image'] = '/' + front_image
        context_dict['top_image'] = '/' + top_image
        context_dict['side_image'] = '/' + side_image

    except Exception as e:
        print e.message
        context_dict['series'] = None
        context_dict['front_image'] = None
        context_dict['top_image'] = None
        context_dict['side_image'] = None
        context_dict['serie_name'] = None
        context_dict['pos_x'] = None
        context_dict['pos_y'] = None
        context_dict['pos_z'] = None
        context_dict['time'] = None

    return render(request, 'tfgWeb/index.html', context=context_dict)


def get_matrix(serieID):

    try:
        serie = Serie.objects.get(id=serieID)
        shape = [serie.x_size,serie.y_size,serie.z_size,serie.c_size,serie.total_times]
        matrix5d = np.empty(shape)

        for time in range(0, serie.total_times):
            image_list = list(Image.objects.filter(Q(serie=serie) & Q(time=time)))
            for z in range(0, serie.z_size):
                matrix5d[:,:,z,:,time] = np.array(PILImage.open(image_list[z].image.name))


    except Exception as e:
        print e.message
        matrix5d = None

    return matrix5d

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