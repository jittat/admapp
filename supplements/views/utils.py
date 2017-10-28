def get_function(fname):
    import importlib
    mod_name, func_name = fname.rsplit('.',1)
    mod = importlib.import_module(mod_name)
    f = getattr(mod, func_name)
    return f
