from tfgWeb import views
from django.conf.urls import url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^tfgWeb/', views.index, name='index'),
    url(r'^register/$',views.register, name='register'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^info/$', views.info, name='info'),
    url(r'^experiment/$', views.experiment, name='experiment'),
    url(r'^zone/$', views.choose_zone, name='choose zone'),
    url(r'^atlas/$', views.atlas, name='atlas'),
]
