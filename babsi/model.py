import os
import re

from .utils import *
from .decorators import *
from .validations import *

#from mako.template import Template

# ---------- GLOBALS ----------

MEDIA_TYPES = [ "picture", "audio", "video"]

# ---------- Class BaseClass -----------

@virtual_attributes(
    meta_information = lambda self: load_yaml_file(self.yaml_file)
)
@file_attributes(
    yaml_file = (
        lambda self: self.meta_dir,
        lambda self: "%s.yml" % self.__class__.__name__.lower()
    ),
    media_dir = (
        lambda self: self.podcast.media_base_dir,
        lambda self: self.file_id,
    )
)
class BaseClass:
    
    def __init__(self, podcast, **kwargs):
        assert isinstance(podcast, Podcast)
        
        self.podcast = podcast
        self.parent = kwargs["parent"] if "parent" in kwargs else None
        self.media_types = (kwargs["media_types"]
                            if "media_types" in kwargs
                            else MEDIA_TYPES )
        self.inherit_attrs = (kwargs["inherit_attrs"]
                              if 'inherit_attrs' in kwargs else [])
        
        assert self.parent == None or isinstance(self.parent, BaseClass)
        for media_type in self.media_types:
            assert media_type in MEDIA_TYPES
    
    def __getattr__(self, name):
        if name in self.meta_information:
            return self.meta_information[name]
        else:
            if name in self.inherit_attrs:
                return getattr(self.parent, name)
            
            raise AttributeError(
                "'%s' has no attribute '%s'" % (self.__class__.__name__, name)
            )
    
    @property
    def children(self):
        for sub_dir_name in sub_dir_names(self.meta_dir):
            yield self[sub_dir_name]
            
    def validate(self):
        assertIsDir(self.meta_dir)
        assertIsValidYaml(self.yaml_file)
        
        self.selfvalidate()
        
        if os.path.isdir(self.media_dir):
            for file_name in os.listdir(self.media_dir):
                if file_name not in [ 'originals' ]:
                    file = os.path.join(self.media_dir, file_name)
                    
                    if os.path.isdir(file):
                        try:
                            assertIsFile(self[file_name].yaml_file)
                        except Exception:
                            raise RuntimeError("media dir '%s' has no meta "
                                            "information" % file)
                    else:
                        assertIsFile(file)
                        
                        if True not in [ file_name.startswith(y + ".") for y in
                                        self.media_types + [ 'original' ] ]:
                            raise RuntimeError("what is the function of file "
                                               "'%s'?!" % file)
        
        for child in self.children:
            child.validate()
            

    def build_media_files(self):
        for media_type in self.media_types:
            input_file, input_format = self.input_file(media_type)
            
            if input_file != None:
                for target_format in self.podcast.target_formats[media_type]:
                    target_file = self.target_file(target_format)
                    
                    if not os.path.exists(target_file):
                        convert(media_type, input_format, input_file,
                                target_format, target_file)
                
        for child in self.children:
            child.build_media_files()
    
    convert = build_media_files
    
    def add_meta_information(self):
        for media_type in self.media_types:
            input_file, input_format = self.input_file(media_type)
            
            if input_file != None:
                add_meta_information(media_type, input_format, input_file, self)
            
            for target_format in self.podcast.target_formats[media_type]:
                target_file = self.target_file(target_format)
                
                if os.path.exists(target_file):
                    add_meta_information(media_type, target_format,
                                         target_file, self)
        
        for child in self.children:
            child.add_meta_information()
    
    addmeta = add_meta_information
    
    def input_file(self, media_type):
        result = None
        result_format = None
        
        for input_format in self.podcast.input_formats[media_type]:
            input_file = os.path.join(self.media_dir,
                                       "%s.%s" % (media_type, input_format))
            
            if file_exists(input_file):
                if result == None:
                    result = input_file
                    result_format = input_format
                else:
                    raise RuntimeError("too many %s files in folder "
                                       "'%s'" % (media_type, self.media_dir))
                                                                  
        return (result, result_format)
    
    def target_file(self, file_format):
        return os.path.join(
            self.podcast.build_dir,
            self.target_file_name(file_format)
        )
    
    def target_file_name(self, file_format):
        return "%s.%s" % (self.file_id, file_format)
        
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.file_id.__repr__())
    
    @property
    def author(self):
        if "authors" in self.meta_information:
            return ", ".join(self.authors)
        elif self.parent != None:
            return self.parent.author
        else:
            return ""

# ---------- The class "Podcast" ----------
        
@virtual_attributes(
    file_id = lambda self: self.id,
    title = lambda self: self.name,
)
@file_attributes(
    meta_dir = ('base_dir', 'meta'),
    media_base_dir = ('base_dir', 'media'),
    build_dir = ('base_dir', 'build'),
)
class Podcast(BaseClass):
    
    def __init__(self, base_dir):
        super(Podcast, self).__init__(self, media_types = [ "picture" ])
        
        base_dir = os.path.abspath(base_dir)
        
        assert os.path.isdir(base_dir)
        
        self.base_dir = base_dir

    
    def selfvalidate(self):
        assertIsDir(self.base_dir)
        assertIsDir(self.media_base_dir)
        assertIsDir(self.build_dir)
        
        assertHasKeys(
            self.meta_information,
            # TODO: to be continued...
            [ 'name', 'subtitle', 'id', 'email', 'episode_prefix' ],
            "yaml file '%s'" % self.yaml_file
        )
        
        for file_name in os.listdir(self.media_base_dir):
            if not file_name in getattr(self, "personal_media_dirs", []):
                try:
                    assertIsFile(self[file_name].yaml_file)
                except Exception:
                    raise RuntimeError(
                        "media dir '%s' has no meta information"
                        % os.path.join(self.media_base_dir, file_name)
                    )
        
        for file_name in os.listdir(self.build_dir):
            file_id = re.match('(.*)\.[^\.]*', file_name).group(1)
            
            try:
                assertIsFile(self[file_id].yaml_file)
            except Exception:
                raise RuntimeError("build file '%s' has no meta information"
                                   % os.path.join(self.build_dir, file_name))
        
        
    def episode(self, episode_specifier):
        return Episode(self, episode_specifier)
        
    def __getitem__(self, key):
        if key == self.id:
            return self
        elif isinstance(key, str) and key.find(":_") >= 0:
            match = re.match("([^:]+):_([^:]+)", key)
            
            episode_specifier = match.group(1)
            episodepart_id = match.group(2)
            
            return self.episode(episode_specifier)[episodepart_id]
        else:
            return self.episode(key)
    
    #def create_rss(self, audio_format, video_format):
        #print(Template(filename=self.rss_template).render(podcast=self))

# ----------- Class Episode -----------
        
@virtual_attributes(
    file_id = lambda self: r'%s%s_%s' % (self.podcast.episode_prefix,
                                         self.number, self.id),
    title = lambda self: 'Folge %s: %s' % (self.number, self.name), # TODO
)
@file_attributes(
    meta_dir = (
        lambda self: self.podcast.meta_dir,
        lambda self: self.file_id
    )
)
class Episode(BaseClass):
    """Models an Episode of a podcast."""
    
    def __init__(self, podcast, episode_specifier):
        """
        Construct an Episode.
        
        parameters:
        
            podcast           - the Podcast Object the episode belongs to
            episode_specifier - a value which uniquely identifies the episode
        
        possible values for 'episode_specifier':
        
            * the number of the episode
            * the id of the episode
            * the name of the directory where the
        """
        super(Episode, self).__init__(podcast, parent=podcast,
                                      inherit_attrs=[ 'genre' ])
        
        if isinstance(episode_specifier, int):
            def_dir_pattern = ('^%s%s_%s$' % (podcast.episode_prefix,
                                              episode_specifier, ID_REGEX))
        elif episode_specifier.startswith(podcast.episode_prefix):
            def_dir_pattern = '^%s$' % re.escape(episode_specifier)
        elif is_id(episode_specifier):
            def_dir_pattern = (r'^%s\d+_%s$' % (podcast.episode_prefix,
                                                re.escape(episode_specifier)))
        else:
            raise ValueError("'%s' is no valid episode "
                             "secifier" % episode_specifier)
            
        
        # find the directory name where the episode information are stored
        def_dir_name = find_unique_element(
            os.listdir(podcast.meta_dir),
            lambda file_name: re.match(def_dir_pattern, file_name),
            'there are more than one episode'
            ' with specifier `%s`' % episode_specifier,
            'there is no episode with specifier `%s`' % episode_specifier
        )
        
        # calculate the id and the number of the episode from the found
        # directory name
        match = re.match(
            r'%s(\d+)_(%s)' % (podcast.episode_prefix, ID_REGEX),
            def_dir_name
        )
        
        self.number = int(match.group(1))
        self.id = match.group(2)
        
        assert self.number >= 0
        assert is_id(self.id)
    
    def selfvalidate(self):
        assertHasKeys(
            self.meta_information,
            [ 'name', 'subtitle', 'date'],
            "yaml file '%s'" % self.yaml_file
        )
    
    def episodepart(self, episodepart_id):
        return EpisodePart(self.podcast, self, episodepart_id)
        
    __getitem__ = episodepart

# ----------- Class EpisodePart ----------
@virtual_attributes(
    file_id = lambda self: "%s:_%s" % (self.episode.file_id, self.id),
    title = lambda self: '%s - %s' % (self.episode.title, self.name),
)
@file_attributes(
    meta_dir = (
        lambda self: self.episode.meta_dir,
        lambda self: self.id
    ),
    media_dir = (
        lambda self: self.episode.media_dir,
        lambda self: self.id,
    )
)
class EpisodePart(BaseClass):
    
    def __init__(self, podcast, episode, id):
        super(EpisodePart, self).__init__(
            podcast, parent=episode, inherit_attrs=[
                'genre', 'date', 'number'
            ]
        )
        
        assert isinstance(episode, Episode)
        assert is_id(id)
        
        self.id = id
        self.episode = episode
    
    def selfvalidate(self):
        assertHasKeys(self.meta_information, [ 'name' ],
                      "yaml file '%s'" % self.yaml_file)

