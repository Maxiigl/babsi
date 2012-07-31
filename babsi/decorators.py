import os

def file_attributes(**kwargs):
    """
    Add attributes which return a file path depending on other instance
    attributes.
    
    Usage:
    
        @file_attribute(
            <attr_name>= (<parent_dir>, <sub_file>),
            <attr_name2>= (<parent_dir2>, <sub_file2>),
            ...
        )
        class Foo:
            ...
    
    This is equivalent to
    
        class Foo:
        
            @property
            def <attr_name>(self):
                return os.path.join(<*parent_dir*>, <*sub_file*>)
    
    Thereby <*parent_dir*> is the closure
    
        if callable(<parent_dir>):
            return <parent_dir>(self)
        else:
            return getattr(self, <parent_dir>)
    
    and <*sub_file*> is
    
        if callable(<sub_file>):
            return <sub_file>(self)
        else:
            return <sub_file>
    """
    def decorator_method(cls):
        for attr_name in kwargs.keys():
            parent_dir, sub_file = kwargs[attr_name]
            
            setattr(cls, attr_name, property(
                lambda self, parent_dir=parent_dir, sub_file=sub_file:
                    os.path.join(
                        parent_dir(self)
                            if callable(parent_dir)
                            else getattr(self, parent_dir),
                        sub_file(self) if callable(sub_file) else sub_file 
                    )
            ))
        
        return cls
    
    return decorator_method

def virtual_attributes(**kwargs):
    def decorator_method(cls):
        for attr_name in kwargs:
            setattr(cls, attr_name, property(kwargs[attr_name]))
        
        return cls
        
    return decorator_method