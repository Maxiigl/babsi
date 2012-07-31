import os

from .utils import load_yaml_file

def assertIsDir(dir, dir_name="directory"):
    if not os.path.isdir(dir):
        raise RuntimeError("%s '%s' does not exist" % (dir_name, dir))

def assertIsFile(file, file_name="file"):
    if not os.path.isfile(file):
        raise RuntimeError("%s '%s' does not exist" % (file_name, file))

def assertIsValidYaml(file, file_name="yaml file"):
    assertIsFile(file, file_name)
    
    try:
        load_yaml_file(file)
    except Exception as e:
        raise RuntimeError("%s '%s' is no valid yaml "
                           "markup" % (file_name, file)) 

def assertHasKeys(dct, keys, map_name="map"):
    for key in keys:
        if not key in dct:
            raise RuntimeError("there is no key '%s' in %s" % (key, map_name))