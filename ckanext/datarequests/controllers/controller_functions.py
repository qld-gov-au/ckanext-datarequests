# encoding: utf-8

import functools
import logging
import re
import six

from six.moves.urllib.parse import urlencode

from ckan import model
from ckan.lib import helpers, captcha
from ckan.plugins import toolkit as tk
from ckan.plugins.toolkit import g, h, request, _

from ckanext.datarequests import constants, request_helpers

_link = re.compile(r'(?:(https?://)|(www\.))(\S+\b/?)([!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]*)(\s|$)', re.I)

log = logging.getLogger(__name__)


def _get_errors_summary(errors):
    errors_summary = {}

    for key, error in errors.items():
        errors_summary[key] = ', '.join(error)

    return errors_summary


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, six.string_types) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def search_url(params):
    url = tk.url_for('datarequest.index')
    return url_with_params(url, params)


def org_datarequest_url(params, id):
    url = tk.url_for('datarequest.organization', id=id)
    return url_with_params(url, params)


def user_datarequest_url(params, id):
    url = tk.url_for('datarequest.user', id=id)
    return url_with_params(url, params)


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': g.user, 'auth_user_obj': g.userobj}


def _show_index(user_id, organization_id, include_organization_facet, url_func, file_to_render, extra_vars=None):
    def pager_url(state=None, sort=None, q=None, page=None):
        params = []

        if q:
            params.append(('q', q))

        if state is not None:
            params.append(('state', state))

        params.append(('sort', sort))
        params.append(('page', page))

        return url_func(params)

    try:
        context = _get_context()
        page = int(request_helpers.get_first_query_param('page', 1))
        limit = constants.DATAREQUESTS_PER_PAGE
        offset = (page - 1) * constants.DATAREQUESTS_PER_PAGE
        data_dict = {'offset': offset, 'limit': limit}

        state = request_helpers.get_first_query_param('state', None)
        if state:
            data_dict['closed'] = True if state == 'closed' else False

        q = request_helpers.get_first_query_param('q', '')
        if q:
            data_dict['q'] = q

        if organization_id:
            data_dict['organization_id'] = organization_id

        if user_id:
            data_dict['user_id'] = user_id

        sort = request_helpers.get_first_query_param('sort', 'desc')
        sort = sort if sort in ['asc', 'desc'] else 'desc'
        if sort is not None:
            data_dict['sort'] = sort

        tk.check_access(constants.LIST_DATAREQUESTS, context, data_dict)
        datarequests_list = tk.get_action(constants.LIST_DATAREQUESTS)(context, data_dict)

        if not extra_vars:
            extra_vars = {}
        extra_vars['filters'] = [(tk._('Newest'), 'desc'), (tk._('Oldest'), 'asc')]
        extra_vars['sort'] = sort
        extra_vars['q'] = q
        extra_vars['organization'] = organization_id
        extra_vars['state'] = state
        extra_vars['datarequest_count'] = datarequests_list['count']
        extra_vars['datarequests'] = datarequests_list['result']
        extra_vars['search_facets'] = datarequests_list['facets']
        extra_vars['page'] = helpers.Page(
            collection=datarequests_list['result'],
            page=page,
            url=functools.partial(pager_url, state, sort),
            item_count=datarequests_list['count'],
            items_per_page=limit
        )
        extra_vars['facet_titles'] = {
            'state': tk._('State'),
        }
        # Organization facet cannot be shown when the user is viewing an org
        if include_organization_facet is True:
            extra_vars['facet_titles']['organization'] = tk._('Organizations')

        if 'user' not in extra_vars:
            extra_vars['user'] = None
        if 'user_dict' not in extra_vars:
            extra_vars['user_dict'] = None
        extra_vars['group_type'] = 'organization'
        return tk.render(file_to_render, extra_vars=extra_vars)
    except ValueError as e:
        # This exception should only occur if the page value is not valid
        log.warning(e)
        return tk.abort(400, tk._('"page" parameter must be an integer'))
    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('Unauthorized to list Data Requests'))


def index():
    return _show_index(None, request_helpers.get_first_query_param('organization', ''), True, search_url,
                       'datarequests/index.html')


def _process_post(action, context):
    # If the user has submitted the form, the data request must be created
    if request_helpers.get_post_params():
        data_dict = {}
        data_dict['title'] = request_helpers.get_first_post_param('title', '')
        data_dict['description'] = request_helpers.get_first_post_param('description', '')
        data_dict['organization_id'] = request_helpers.get_first_post_param('organization_id', '')

        if action == constants.UPDATE_DATAREQUEST:
            data_dict['id'] = request_helpers.get_first_post_param('id', '')

        try:
            captcha.check_recaptcha(request)
            result = tk.get_action(action)(context, data_dict)
            return tk.redirect_to(tk.url_for('datarequest.show', id=result['id']))
        except tk.ValidationError as e:
            log.warning(e)
            # Fill the fields that will display some information in the page
            return {
                'datarequest': {
                    'id': data_dict.get('id', ''),
                    'title': data_dict.get('title', ''),
                    'description': data_dict.get('description', ''),
                    'organization_id': data_dict.get('organization_id', ''),
                },
                'errors': e.error_dict,
                'errors_summary': _get_errors_summary(e.error_dict),
            }
        except captcha.CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            # Fill the fields that will display some information in the page
            return {
                'datarequest': {
                    'id': data_dict.get('id', ''),
                    'title': data_dict.get('title', ''),
                    'description': data_dict.get('description', ''),
                    'organization_id': data_dict.get('organization_id', ''),
                }
            }
    return {}


def new():
    context = _get_context()

    # Basic initialization
    extra_vars = {
        'datarequest': {},
        'errors': {},
        'errors_summary': {},
    }

    # Check access
    try:
        tk.check_access(constants.CREATE_DATAREQUEST, context, None)
        post_result = _process_post(constants.CREATE_DATAREQUEST, context)
        if isinstance(post_result, dict):
            extra_vars.update(post_result)
            return tk.render('datarequests/new.html', extra_vars=extra_vars)
        else:
            return post_result
    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('Unauthorized to create a Data Request'))


def show(id):
    data_dict = {'id': id}
    context = _get_context()

    try:
        tk.check_access(constants.SHOW_DATAREQUEST, context, data_dict)
        extra_vars = {
            'datarequest': tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)
        }

        context_ignore_auth = context.copy()
        context_ignore_auth['ignore_auth'] = True

        return tk.render('datarequests/show.html', extra_vars=extra_vars)
    except tk.ObjectNotFound:
        return tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('You are not authorized to view the Data Request %s' % id))


def update(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic initialization
    extra_vars = {
        'datarequest': {},
        'errors': {},
        'errors_summary': {},
    }

    try:
        tk.check_access(constants.UPDATE_DATAREQUEST, context, data_dict)
        current_datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)
        extra_vars['datarequest'] = current_datarequest
        extra_vars['original_title'] = current_datarequest.get('title')
        post_result = _process_post(constants.UPDATE_DATAREQUEST, context)
        if isinstance(post_result, dict):
            extra_vars.update(post_result)
            return tk.render('datarequests/edit.html', extra_vars=extra_vars)
        else:
            return post_result
    except tk.ObjectNotFound as e:
        log.warning(e)
        return tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('You are not authorized to update the Data Request %s' % id))


def delete(id):
    data_dict = {'id': id}
    context = _get_context()

    try:
        tk.check_access(constants.DELETE_DATAREQUEST, context, data_dict)
        datarequest = tk.get_action(constants.DELETE_DATAREQUEST)(context, data_dict)
        h.flash_notice(tk._('Data Request %s has been deleted') % datarequest.get('title', ''))
        return tk.redirect_to(tk.url_for('datarequest.index'))
    except tk.ObjectNotFound as e:
        log.warning(e)
        return tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('You are not authorized to delete the Data Request %s' % id))


def organization(id):
    context = _get_context()
    group_dict = tk.get_action('organization_show')(context, {'id': id})
    url_func = functools.partial(org_datarequest_url, id=id)
    return _show_index(None, id, False, url_func, 'organization/datarequests.html',
                       extra_vars={'group_dict': group_dict})


def user(id):
    context = _get_context()
    try:
        user_dict = tk.get_action('user_show')(context, {'id': id, 'include_num_followers': True})
    except tk.NotAuthorized:
        return tk.abort(403, tk._(u'Not authorized to see this page'))
    url_func = functools.partial(user_datarequest_url, id=id)
    return _show_index(id, request_helpers.get_first_query_param('organization', ''), True, url_func,
                       'user/datarequests.html',
                       extra_vars={'user': user_dict, 'user_dict': user_dict})


def close(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic initialization
    extra_vars = {
        'datarequest': {}
    }

    def _return_page(errors=None, errors_summary=None):
        errors = errors or {}
        errors_summary = errors_summary or {}
        # Get datasets (if the data req belongs to an organization,
        # only the ones that belong to the organization are shown)
        # FIXME: At this time, only the 500 last modified/created datasets are retrieved.
        # We assume that a user will close their data request with a recently added or modified dataset
        # In the future, we should fix this with an autocomplete form...
        search_data_dict = {'rows': 500}
        organization_id = extra_vars['datarequest'].get('organization_id', '')
        if organization_id:
            log.debug("Loading datasets for organisation %s", organization_id)
            search_data_dict['q'] = 'owner_org:' + organization_id
        else:
            # Expected for CKAN 2.3
            log.debug("Loading first 500 datasets...")
        base_datasets = tk.get_action('package_search')({'ignore_auth': True}, search_data_dict)['results']

        log.debug("Dataset candidates for closing data request: %s", base_datasets)
        extra_vars['datasets'] = []
        extra_vars['errors'] = errors
        extra_vars['errors_summary'] = errors_summary
        for dataset in base_datasets:
            extra_vars['datasets'].append({'name': dataset.get('name'), 'title': dataset.get('title')})

        if h.closing_circumstances_enabled:
            # This is required so the form can set the currently selected close_circumstance option in the select dropdown
            extra_vars['datarequest']['close_circumstance'] = request_helpers.get_first_post_param('close_circumstance', None)

        return tk.render('datarequests/close.html', extra_vars=extra_vars)

    try:
        tk.check_access(constants.CLOSE_DATAREQUEST, context, data_dict)
        extra_vars['datarequest'] = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)

        if extra_vars['datarequest'].get('closed', False):
            return tk.abort(403, tk._('This data request is already closed'))
        elif request_helpers.get_post_params():
            data_dict = {}
            data_dict['accepted_dataset_id'] = request_helpers.get_first_post_param('accepted_dataset_id', None)
            data_dict['id'] = id
            if h.closing_circumstances_enabled:
                data_dict['close_circumstance'] = request_helpers.get_first_post_param('close_circumstance', None)
                data_dict['approx_publishing_date'] = request_helpers.get_first_post_param('approx_publishing_date',
                                                                                           None)
                data_dict['condition'] = request_helpers.get_first_post_param('condition', None)

            tk.get_action(constants.CLOSE_DATAREQUEST)(context, data_dict)
            return tk.redirect_to(tk.url_for('datarequest.show', id=data_dict['id']))
        else:  # GET
            return _return_page()

    except tk.ValidationError as e:  # Accepted Dataset is not valid
        log.warning(e)
        errors_summary = _get_errors_summary(e.error_dict)
        return _return_page(e.error_dict, errors_summary)
    except tk.ObjectNotFound as e:
        log.warning(e)
        return tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('You are not authorized to close the Data Request %s' % id))


def comment(id):
    try:
        context = _get_context()
        data_dict_comment_list = {'datarequest_id': id}
        data_dict_dr_show = {'id': id}
        tk.check_access(constants.LIST_DATAREQUEST_COMMENTS, context, data_dict_comment_list)

        # Raises 404 Not Found if the data request does not exist
        extra_vars = {
            'datarequest': tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict_dr_show),
            'current_user': g.userobj,
        }

        comment_text = request_helpers.get_first_post_param('comment', '')
        comment_id = request_helpers.get_first_post_param('comment-id', '')
        updated_comment = None

        if request_helpers.get_post_params():
            action = constants.COMMENT_DATAREQUEST
            action_text = 'comment'

            if comment_id:
                action = constants.UPDATE_DATAREQUEST_COMMENT
                action_text = 'update comment'

            try:
                comment_data_dict = {'datarequest_id': id, 'comment': comment_text, 'id': comment_id}
                updated_comment = tk.get_action(action)(context, comment_data_dict)

                if not comment_id:
                    flash_message = tk._('Comment has been published')
                else:
                    flash_message = tk._('Comment has been updated')

                h.flash_notice(flash_message)

            except tk.NotAuthorized as e:
                log.warning(e)
                return tk.abort(403, tk._('You are not authorized to %s' % action_text))
            except tk.ValidationError as e:
                log.warning(e)
                extra_vars['errors'] = e.error_dict
                extra_vars['errors_summary'] = _get_errors_summary(e.error_dict)
            except tk.ObjectNotFound as e:
                log.warning(e)
                return tk.abort(404, tk._(str(e)))
            # Other exceptions are not expected. Otherwise, the request will fail.

            # This is required to scroll the user to the appropriate comment
            if not updated_comment:
                updated_comment = {
                    'id': comment_id,
                    'comment': comment_text
                }

        extra_vars['updated_comment'] = {
            'comment': updated_comment
        }
        # Comments should be retrieved once that the comment has been created
        get_comments_data_dict = {'datarequest_id': id}
        extra_vars['comments'] = tk.get_action(constants.LIST_DATAREQUEST_COMMENTS)(context, get_comments_data_dict)

        return tk.render('datarequests/comment.html', extra_vars=extra_vars)

    except tk.ObjectNotFound as e:
        log.warning(e)
        return tk.abort(404, tk._('Data Request %s not found' % id))

    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('You are not authorized to list the comments of the Data Request %s' % id))


def delete_comment(datarequest_id, comment_id):
    try:
        context = _get_context()
        data_dict = {'id': comment_id}
        tk.check_access(constants.DELETE_DATAREQUEST_COMMENT, context, data_dict)
        tk.get_action(constants.DELETE_DATAREQUEST_COMMENT)(context, data_dict)
        h.flash_notice(tk._('Comment has been deleted'))
        return tk.redirect_to(tk.url_for('datarequest.comment', id=datarequest_id))
    except tk.ObjectNotFound as e:
        log.warning(e)
        return tk.abort(404, tk._('Comment %s not found') % comment_id)
    except tk.NotAuthorized as e:
        log.warning(e)
        return tk.abort(403, tk._('You are not authorized to delete this comment'))


def follow(id):
    # Method is not called
    pass


def unfollow(id):
    # Method is not called
    pass


def purge(user_id):
    """ Delete all data requests associated with the specified account.
    This is intended for cleanup of spam.
    """
    data_dict = {'user_id': user_id}
    context = _get_context()

    post_params = request_helpers.get_post_params()
    if post_params:
        if 'cancel' in post_params:
            return tk.redirect_to('datarequest.index')

        try:
            tk.get_action(constants.PURGE_DATAREQUESTS)(context, data_dict)
            h.flash_notice(tk._('Deleted data request(s) for user'))
            return tk.redirect_to('datarequest.index')
        except tk.ObjectNotFound as e:
            log.warning(e)
            return tk.abort(404, tk._('User %s not found') % user_id)
    else:
        return tk.render('datarequests/confirm_delete_all.html', extra_vars={'user_id': user_id})
