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
    front_axis = models.CharField(max_length=1,default='Z')
    side_axis = models.CharField(max_length=1,default='X')
    top_axis = models.CharField(max_length=1,default='Y')

    def __str__(self):
        return self.name

    def delete_experiment(self):
        self.delete()

    def change_name(self, name):
        self.name=name
        self.save()

    def get_galery(self, name):
        return Galery.objects.get(Q(experiment=self) & Q(name=name))

    def get_galerys(self):
        return Galery.objects.filter(Q(experiment=self))

    def add_atlas(self, name, size_x, size_y, size_z):
        return Galery.objects.get_or_create(experiment=self, name= name, total_times=1, x_size=size_x, y_size= size_y, z_size=size_z)[0]

    def add_series(self, name, times, size_x, size_y, size_z):
        return Galery.objects.get_or_create(experiment=self, name=name, total_times=times, x_size=size_x, y_size= size_y, z_size=size_z, width=-1, height=-1, depth=-1, start_x=0, start_y=0, start_z=0)[0]

class Galery(models.Model):

    experiment = models.ForeignKey(Experiment)
    name = models.CharField(max_length=128)
    total_times = models.IntegerField(default=0)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)
    width = models.IntegerField(default=-1)
    height = models.IntegerField(default=-1)
    depth = models.IntegerField(default=-1)
    start_x = models.IntegerField(default=0)
    start_y = models.IntegerField(default=0)
    start_z = models.IntegerField(default=0)

    def set_size(self, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth
        self.save()

    def set_position(self, start_x, start_y, start_z):
        self.start_x = start_x
        self.start_y = start_y
        self.start_z = start_z
        self.save()

    def add_axis(self, name):
        return Axis.objects.get_or_create(galery=self, name=name)[0]

    def check_atlas(self):
        return self.is_atlas

    def get_axis(self, axis_name):
        return Axis.objects.get(Q(galery=self) & Q(name=axis_name))

    def get_image(self, axis_name, pos, time):
        return self.get_axis(axis_name).get_image(pos,time)

    def __str__(self):
        return self.name

class Axis(models.Model):

    name = models.CharField(max_length=2)
    galery = models.ForeignKey(Galery)

    def add_image(self, image, pos, time):
        im = Image.objects.get_or_create(axis=self, image=image, pos=pos, time=time)[0]
        im.save()
        return im

    def get_image(self, pos, time):
        image = Image.objects.get(Q(axis=self) & Q(pos=pos) & Q(time=time)).image.url
        return image

    def __str__(self):
        return self.galery.__str__() + " axis " + self.name

class Image(models.Model):

    axis = models.ForeignKey(Axis)
    image = models.ImageField(upload_to=config.IMAGES_PATH)
    pos = models.IntegerField(default=-1)
    time = models.IntegerField(default=-1)

    def __str__(self):
        return self.axis.__str__() + " position " + str(self.pos) + " and time " + str(self.time)

class UserProfile(models.Model):

    username = models.OneToOneField(User, default=None)
    organization = models.CharField(blank=True, max_length=20)

    def __str__(self):
        return self.user.username

def get_experiments(user):
    if user.is_anonymous():
        return None
    else:
        return Experiment.objects.filter(
            Q(owner=user) | Q(owner=User.objects.get_by_natural_key(config.ADMIN_NAME))).exclude(is_atlas=True)


def get_experiment(experiment_id):
    experiment =  Experiment.objects.get(Q(id=experiment_id))
    return experiment

def get_atlas():
    return Experiment.objects.get(is_atlas=True).get_galerys()

def add_experiment(name, info, user, is_atlas, front_axis, top_axis, side_axis):
    experiment = Experiment.objects.get_or_create(owner=user, name=name, info= info, is_atlas=is_atlas, front_axis=front_axis, side_axis=side_axis, top_axis=top_axis)[0]
    return experiment