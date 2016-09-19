import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfgProject.settings")
django.setup()
from tfgWeb import utils, config
from django.contrib.auth.models import User

filename = "/home/pablo/bioformats/twist_sytox_zo_4d.lif"
atlasname =  "/home/pablo/bioformats/ViBE-Z_48hpf_v1.h5"

def add_admin():
    try:
        user = User.objects.create_user(config.ADMIN_NAME, 'admin@admin.com', 'defaultpass2')
        user.save()
        return user
    except:
        user = User.objects.get_by_natural_key(config.ADMIN_NAME)
        return user

#Populate function
def populate(filename, atlasname):

    admin = add_admin()
    print "Loading experiment..."
    utils.save_lif(filename=filename,user=admin, top_axis='X',side_axis='Y',front_axis='Z')

    print "Loading atlas..."
    utils.save_h5(filename=atlasname, user=admin, top_axis='X',side_axis='Y', front_axis='Z', is_atlas=True)

    print "Populate finished succesfully!"

# Start execution here!
if __name__ == '__main__':
    print("Starting population script...")
    populate(filename,atlasname)