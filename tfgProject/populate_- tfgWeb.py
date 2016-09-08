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

    # # Checking VM
    # check_VM()
    #
    # bf_reader = utils.get_reader_lif(filename)
    # total_series = utils.get_total_series_lif(bf_reader.rdr)
    # names = utils.get_name_lif(filename)
    # name = utils.get_name_experiment(filename)

    # metadata
    # experiment = add_experiment(name=name,info=None,user=admin, is_atlas=False, top_axis='Z', side_axis='X', front_axis='Y')
    #
    # for serieID in range(0, total_series):
    #     print 'Loading serie: ' + names[serieID]
    #     utils.read_series(experiment=experiment, user=admin, bf_reader=bf_reader, serieID=serieID, name=names[serieID])
    #
    # kill_VM()

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