from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class Serie(models.Model):

    name = models.CharField(max_length=128)
    owner = models.ForeignKey(AUTH_USER_MODEL)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)
    c_size = models.IntegerField(default=0)
    total_times = models.IntegerField(default=0)

    class Meta:
        def __str__(self):
            return self.name

    def get_5d_matrix(self):
        return None

class Image(models.Model):

    serie = models.ForeignKey(Serie)
    image = models.ImageField(upload_to=settings.IMAGES_PATH, storage=settings.IMAGES_PATH + '/default/')
    pos_z = models.IntegerField(default=-1)
    time = models.IntegerField(default=-1)

    def __str__(self):
        return self.serie.__str__() + " position " + str(self.pos_z) + " and time " + str(self.time)

class UserProfile(models.Model):

    username = models.OneToOneField(User, default=None)
    organization = models.CharField(blank=True, max_length=20, default='none')

    def __str__(self):
        return self.user.username