from __future__ import unicode_literals
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfgProject.settings")
from tfgWeb import config
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from PIL import Image as PILImage
import numpy as np
from django.db.models import Q

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class Serie(models.Model):

    name = models.CharField(max_length=128)
    owner = models.ForeignKey(AUTH_USER_MODEL)
    reduce_factor = models.IntegerField(default=1)
    total_times = models.IntegerField(default=0)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)

    def add_muestra(self, name,scale_value):

        x_size = int(self.x_size/scale_value)
        y_size = int(self.y_size /scale_value)
        z_size = int(self.z_size /scale_value)
        name = name

        return Muestra.objects.get_or_create(serie=self, name=name, x_size=x_size, y_size=y_size, z_size=z_size)[0]

    def get_muestra(self, muestra_key):

        muestra =  Muestra.objects.get(Q(serie=self) & Q(name=muestra_key))
        return muestra

    def get_matrix(self, muestra_key):
        return Muestra.objects.get(Q(serie=self) & Q(name=muestra_key)).get_matrix()

    def __str__(self):
        return self.name

class Muestra(models.Model):

    serie = models.ForeignKey(Serie)
    name = models.CharField(max_length=128)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)

    def get_matrix(self, time):

        try:
            shape = [self.x_size, self.y_size, self.z_size, 4, 1]

            matrix5d = np.empty(shape)

            image_list = list(Image.objects.filter(Q(muestra=self) & Q(time=time)))
            for z in range(0, self.z_size):
                matrix5d[:, :, z, :, time] = np.array(PILImage.open(image_list[z].image).convert('RGBA'))

        except Exception as e:
            print e.message
            matrix5d = None

        return matrix5d

    def add_image(self, image, pos_z, time):
        im = Image.objects.get_or_create(muestra=self, image=image, pos_z=pos_z, time=time)[0]
        im.save()
        return im

    def __str__(self):
        return self.serie.__str__() + " name " + self.name

class Image(models.Model):

    muestra = models.ForeignKey(Muestra)
    image = models.ImageField(upload_to=config.IMAGES_PATH)
    pos_z = models.IntegerField(default=-1)
    time = models.IntegerField(default=-1)

    def __str__(self):
        return self.muestra.__str__() + " position " + str(self.pos_z) + " and time " + str(self.time)

class UserProfile(models.Model):

    username = models.OneToOneField(User, default=None)
    organization = models.CharField(blank=True, max_length=20, default='none')

    def __str__(self):
        return self.user.username

class Atlas(models.Model):

    name = models.CharField(max_length=128)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)

    def add_muestra(self, name, scale_value):
        x_size = int(self.x_size / scale_value)
        y_size = int(self.y_size / scale_value)
        z_size = int(self.z_size / scale_value)
        name = name

        muestra = MuestraAtlas.objects.get_or_create(atlas=self, name=name, x_size=x_size, y_size=y_size, z_size=z_size)[0]
        return muestra

    def __str__(self):
        return self.name

class MuestraAtlas(models.Model):
    atlas = models.ForeignKey(Atlas)
    name = models.CharField(max_length=128)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)

    def get_atlas(self):
        try:
            shape = [self.x_size, self.y_size, self.z_size, self.c_size]
            atlas = np.empty(shape)

            image_list = list(AtlasImage.objects.filter(Q(muestra=self)))
            for z in range(0, self.z_size):
                atlas[:, :, z, :] = np.array(PILImage.open(image_list[z].image.name))

        except Exception as e:
            print e.message
            atlas = None

        return atlas

    def add_image(self, image, pos_z):
        im = AtlasImage.objects.get_or_create(muestra=self, image=image, pos_z=pos_z)[0]
        im.save()
        return im

    def __str__(self):
        return self.atlas.__str__() + " name " + self.name

class AtlasImage(models.Model):
    muestra = models.ForeignKey(MuestraAtlas, default=None)
    image = models.ImageField(upload_to=config.ATLAS_PATH)
    pos_z = models.IntegerField(default=-1)

    def __str__(self):
        return self.muestra.__str__() + " position " + str(self.pos_z)