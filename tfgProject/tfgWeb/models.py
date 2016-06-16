from __future__ import unicode_literals

from django.db import models

class Serie(models.Model):

    name = models.CharField(max_length=128)
    x_size = models.IntegerField(default=0)
    y_size = models.IntegerField(default=0)
    z_size = models.IntegerField(default=0)
    total_times = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def get_5d_matrix(self):
        return None

class Image(models.Model):

    serie = models.ForeignKey(Serie)
    image = models.ImageField(upload_to='static/tfgWeb/')
    pos_z = models.IntegerField(default=-1)
    time = models.IntegerField(default=-1)

    def __str__(self):
        return self.serie.__str__() + " position " + str(self.pos_z) + " and time " + str(self.time)