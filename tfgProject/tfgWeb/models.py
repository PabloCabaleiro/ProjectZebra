from __future__ import unicode_literals
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfgProject.settings")
from tfgWeb import config
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class Experiment(models.Model):
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(AUTH_USER_MODEL, null=True)
    is_atlas = models.BooleanField(default=False)
    info = models.CharField(max_length=512, null=True)

    def __str__(self):
        return self.name

    def get_galery(self, name):
        return Galery.objects.get(Q(experiment=self) & Q(name=name))

    def get_galerys(self):
        return Galery.objects.filter(Q(experiment=self))

    def add_atlas(self, name, size_x, size_y, size_z):
        return Galery.objects.get_or_create(experiment=self, name= name, total_times=1, x_size=size_x, y_size= size_y, z_size=size_z)[0]

    def add_series(self, name, times, size_x, size_y, size_z):
        return Galery.objects.get_or_create(experiment=self, name=name, total_times=times, x_size=size_x, y_size= size_y, z_size=size_z)[0]


class Galery(models.Model):

    experiment = models.ForeignKey(Experiment)
    name = models.CharField(max_length=128)
    total_times = models.IntegerField(default=0)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)

    def add_sample(self, name, scale_value):

        x_size = int(self.x_size/scale_value)
        y_size = int(self.y_size /scale_value)
        z_size = int(self.z_size /scale_value)
        name = name

        return Sample.objects.get_or_create(galery=self, name=name, x_size=x_size, y_size=y_size, z_size=z_size)[0]

    def check_atlas(self):
        return self.is_atlas

    def get_sample(self, muestra_key):

        muestra =  Sample.objects.get(Q(galery=self) & Q(name=muestra_key))
        return muestra

    def get_samples(self):
        return Sample.objects.filter(Q(galery=self)).order_by('-x_size')

    def get_axis(self, muestra_key, axis_name):
        return self.get_sample(muestra_key).get_axis(axis_name)

    def get_image(self, muestra_key, axis_name, pos, time):
        return self.get_sample(muestra_key).get_image(axis_name,pos,time)

    def get_matrix(self, muestra_key):
        return Sample.objects.get(Q(serie=self) & Q(name=muestra_key)).get_matrix()

    def __str__(self):
        return self.name

class Sample(models.Model):

    galery = models.ForeignKey(Galery)
    name = models.CharField(max_length=128)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)

    def add_axis(self, name):
        axis = Axis.objects.get_or_create(name=name, sample=self)[0]
        axis.save()
        return axis

    def get_axis(self, axis_name):
        return Axis.objects.get(Q(sample=self) & Q(name=axis_name))

    def get_image(self, axis_name, pos, time):
        return self.get_axis(axis_name).get_image(pos,time)

    def __str__(self):
        return self.galery.__str__() + " quality " + self.name

class Axis(models.Model):

    name = models.CharField(max_length=2)
    sample = models.ForeignKey(Sample)

    def add_image(self, image, pos, time):
        im = Image.objects.get_or_create(axis=self, image=image, pos=pos, time=time)[0]
        im.save()
        return im

    def get_image(self, pos, time):
        image = Image.objects.get(Q(axis=self) & Q(pos=pos) & Q(time=time)).image.url
        return image

    def __str__(self):
        return self.sample.__str__() + " axis " + self.name

class Image(models.Model):

    axis = models.ForeignKey(Axis)
    image = models.ImageField(upload_to=config.IMAGES_PATH)
    pos = models.IntegerField(default=-1)
    time = models.IntegerField(default=-1)

    def __str__(self):
        return self.axis.__str__() + " position " + str(self.pos_z) + " and time " + str(self.time)

class UserProfile(models.Model):

    username = models.OneToOneField(User, default=None)
    organization = models.CharField(blank=True, max_length=20, default='none')

    def __str__(self):
        return self.user.username

def get_experiments(user):
    if user.is_anonymous():
        series_list = Experiment.objects.filter(Q(owner=User.objects.get_by_natural_key(config.ADMIN_NAME))).exclude(
            is_atlas=True)
    else:
        series_list = Experiment.objects.filter(
            Q(owner=user) | Q(owner=User.objects.get_by_natural_key(config.ADMIN_NAME))).exclude(is_atlas=True)
    return series_list

def get_experiment(experiment_id):
    experiment =  Experiment.objects.get(Q(id=experiment_id))
    return experiment

def get_atlas():
    return Experiment.objects.get(is_atlas=True).get_galerys()