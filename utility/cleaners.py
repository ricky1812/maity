
def replace_empty(val, default=None):
    '''Replaces empty string with the default value'''
    if not val:
        # if empty string or 'None' return 'None'
        return default
    return val
