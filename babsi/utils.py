import collections
import re
import os
import yaml
import logging

# ----------- Globals -----------

ID_REGEX = '[a-z_0-9]+'

CACHE = {}

# ----------- Initialize Logger ----------

# Todo: ein Logger pro Podcast-Projekt!

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s: %(message)s'))

logger = logging.getLogger("Babsi")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

del handler # not needed anymore

def is_id(obj):
    """Check whether the given object is a valid id."""
    return (
        isinstance(obj, str)
        and len(obj) > 0
        and re.match('^{0}$'.format(ID_REGEX),obj)
    )

def find_unique_element(
        iterator, test_closure, no_unique_element_err_msg=None,
        no_element_found_err_msg=None):
    """
    Find a unique element in a sequence of objects and raise an error if
    there is no unique element.

    parameters:
    
        iterator - Iterator object where to search the unique object
        test_closure - callable with has to return true for the searched object
        no_unique_element_err_msg (optional)
            - error message if there match more objects the test callable
        no_element_found_err_msg (optional)
            - error message if no element could be found
    """
    assert isinstance(iterator, collections.Iterable)
    assert callable(test_closure)
    
    result = None
    result_found = False
    
    for element in iterator:
        if test_closure(element):
            if not result_found:
                result = element
                result_found = True
            else:
                raise RuntimeError(
                    no_unique_element_err_msg
                    if no_unique_element_err_msg != None
                    else 'there is no unique element'
                )
    
    if result_found:
        return result
    else:
        raise RuntimeError(
            no_element_found_err_msg
            if no_element_found_err_msg != None
            else 'no element found'
        )
            
def load_yaml_file(yaml_file):
    """Load a yaml file (with caching of the result)."""
    assert os.path.isfile(yaml_file), ('YAML file `%s` does not'
                                       'exist' % yaml_file)
    
    yaml_file_mtime = os.path.getmtime(yaml_file)
    
    if not (yaml_file in CACHE and CACHE[yaml_file][0] >= yaml_file_mtime):
        CACHE[yaml_file] = (yaml_file_mtime, yaml.load(open(yaml_file, 'r')))
    
    return CACHE[yaml_file][1]
    
def file_exists(file):
    return file != None and os.path.isfile(file)
    
def sub_dir_names(dir):
    assert os.path.isdir(dir)
    
    for file_name in os.listdir(dir):
        if os.path.isdir(os.path.join(dir, file_name)):
            yield file_name

def convert(media_type, input_format, input_file, target_format, target_file):
    logger.info("convert %s %s" % (input_file, target_file))
    
    if input_format == target_format:
        os.system("cp -v %s %s" % (input_file, target_file))
    else:
        if target_format == 'mp3':
            os.system("avconv -i %s -b 64k %s" % (input_file, target_file))
        elif target_format == 'ogg':
            os.system("avconv -i %s -b 64k %s" % (input_file, target_file))
        elif target_format == 'm4a':
            os.system("avconv -i %s -b 48k %s" % (input_file, target_file))
        

def add_meta_information(media_type, file_format, file, metaobj):
    logger.info("add meta information to %s" % file)
    
    if media_type != 'picture':
        metadata = {}
        metadata['title'] = metaobj.title
        metadata['author'] = metaobj.author
        metadata['album_artist'] = metaobj.podcast.author
        metadata['album'] = metaobj.podcast.name
        metadata['show'] = metaobj.podcast.name
        metadata['genre'] = metaobj.genre
        metadata['episode_id'] = metaobj.file_id
        metadata['comment'] = metaobj.podcast.homepage
        
        if hasattr(metadata, "date"):
            metadata['year'] = metaobj.date.year 
        
        if hasattr(metadata, "number"):
            metadata['track'] = metaobj.number
        
        if hasattr(metadata, "subtitle"):
            metadata['synopsis'] = metaobj.subtitle
        
        cmd = "avconv -i %s -c copy " % file.__repr__()
        
        for key, value in metadata.items():
            cmd += "-metadata %s=%s " % (key, str(value).__repr__())
        
        cmd += file.__repr__()
        
        os.system(cmd)