# encoding: utf-8
""" Some useful functions for interacting with the current request.
"""


def get_request():
    from ckan.common import request
    return request


def get_cookie(field_name, default=None):
    """ Get the value of a cookie, or the default value if not present.
    """
    return get_request().cookies.get(field_name, default)


def has_query_params():
    """ Determine whether the request has a POST body.
    """
    return getattr(get_request(), 'GET', None) \
        or getattr(get_request(), 'args', None)


def has_post_params():
    """ Determine whether the request has a POST body.
    """
    return getattr(get_request(), 'POST', None) \
        or getattr(get_request(), 'form', None)


def get_post_params(field_name):
    """ Retrieve a list of all POST parameters with the specified name
    for the current request.

    This uses 'request.POST' for Pylons and 'request.form' for Flask.
    """
    if hasattr(get_request(), 'form'):
        return get_request().form.getlist(field_name)
    else:
        return get_request().POST.getall(field_name)


def get_query_params(field_name):
    """ Retrieve a list of all GET parameters with the specified name
    for the current request.

    This uses 'request.GET' for Pylons and 'request.args' for Flask.
    """
    if hasattr(get_request(), 'args'):
        return get_request().args.getlist(field_name)
    else:
        return get_request().GET.getall(field_name)


def delete_param(field_name):
    """ Remove the parameter with the specified name from the current
    request. This requires the request parameters to be mutable.
    """
    for collection_name in ['args', 'form', 'GET', 'POST']:
        collection = getattr(get_request(), collection_name, {})
        if field_name in collection:
            del collection[field_name]


def scoped_attrs():
    """ Returns a mutable dictionary of attributes that exist in the
    scope of the current request, and will vanish afterward.
    """
    return get_request().environ['webob.adhoc_attrs']
