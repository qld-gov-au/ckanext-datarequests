# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of CKAN Data Requests Extension.

# CKAN Data Requests Extension is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# CKAN Data Requests Extension is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with CKAN Data Requests Extension. If not, see <http://www.gnu.org/licenses/>.

import logging

import functools
import re
import six

from six.moves.urllib.parse import urlencode

from flask import Blueprint

from ckan import model
from ckan.common import request
from ckan.lib import helpers
from ckan.plugins import toolkit as tk
from ckanext.datarequests import constants

import request_helpers


_link = re.compile(r'(?:(https?://)|(www\.))(\S+\b/?)([!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]*)(\s|$)', re.I)

log = logging.getLogger(__name__)
c = tk.c



def get_first(values, default=None):
    """ Retrieve the first value from the specified list, or the provided
    default if it isn't present.
    """
    if values:
        returnValue = values[0]
    else:
        returnValue = None
    return returnValue or default


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
    url = helpers.url_for(named_route='datarequest.index')
    return url_with_params(url, params)


def org_datarequest_url(params, id):
    url = helpers.url_for(named_route='organization_datarequest.organization_datarequests', id=id)
    return url_with_params(url, params)


def user_datarequest_url(params, id):
    url = helpers.url_for(named_route='user_datarequest.user_datarequests', id=id)
    return url_with_params(url, params)


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': c.user, 'auth_user_obj': c.userobj}


def _show_index(user_id, organization_id, include_organization_facet, url_func, file_to_render):

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
        page = int(get_first(request_helpers.get_query_params('page'), 1))
        limit = constants.DATAREQUESTS_PER_PAGE
        offset = (page - 1) * constants.DATAREQUESTS_PER_PAGE
        data_dict = {'offset': offset, 'limit': limit}

        state = get_first(request_helpers.get_query_params('state'))
        if state:
            data_dict['closed'] = True if state == 'closed' else False

        q = get_first(request_helpers.get_query_params('q'), '')
        if q:
            data_dict['q'] = q

        if organization_id:
            data_dict['organization_id'] = organization_id

        if user_id:
            data_dict['user_id'] = user_id

        sort = get_first(request_helpers.get_query_params('sort'), 'desc')
        sort = sort if sort in ['asc', 'desc'] else 'desc'
        if sort is not None:
            data_dict['sort'] = sort

        tk.check_access(constants.LIST_DATAREQUESTS, context, data_dict)
        datarequests_list = tk.get_action(constants.LIST_DATAREQUESTS)(context, data_dict)

        c.filters = [(tk._('Newest'), 'desc'), (tk._('Oldest'), 'asc')]
        c.sort = sort
        c.q = q
        c.organization = organization_id
        c.state = state
        c.datarequest_count = datarequests_list['count']
        c.datarequests = datarequests_list['result']
        c.search_facets = datarequests_list['facets']
        c.page = helpers.Page(
            collection=datarequests_list['result'],
            page=page,
            url=functools.partial(pager_url, state, sort),
            item_count=datarequests_list['count'],
            items_per_page=limit
        )
        c.facet_titles = {
            'state': tk._('State'),
        }

        # Organization facet cannot be shown when the user is viewing an org
        if include_organization_facet is True:
            c.facet_titles['organization'] = tk._('Organizations')

        return tk.render(file_to_render, extra_vars={'user_dict': c.user_dict if hasattr(c, 'user_dict') else None, 'group_type': 'organization'})
    except ValueError as e:
        # This exception should only occur if the page value is not valid
        log.warn(e)
        tk.abort(400, tk._('"page" parameter must be an integer'))
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('Unauthorized to list Data Requests'))


def index():
    return _show_index(None, get_first(request_helpers.get_query_params('organization'), ''), True, search_url, 'datarequests/index.html')


def _process_post(action, context):
    # If the user has submitted the form, the data request must be created
    if request_helpers.has_post_params():
        data_dict = {}
        data_dict['title'] = get_first(request_helpers.get_post_params('title'), '')
        data_dict['description'] = get_first(request_helpers.get_post_params('description'), '')
        data_dict['organization_id'] = get_first(request_helpers.get_post_params('organization_id'), '')

        if action == constants.UPDATE_DATAREQUEST:
            data_dict['id'] = get_first(request_helpers.get_post_params('id'), '')

        try:
            result = tk.get_action(action)(context, data_dict)
            tk.redirect_to(helpers.url_for(named_route='datarequest.show', id=result['id']))

        except tk.ValidationError as e:
            log.warn(e)
            # Fill the fields that will display some information in the page
            c.datarequest = {
                'id': data_dict.get('id', ''),
                'title': data_dict.get('title', ''),
                'description': data_dict.get('description', ''),
                'organization_id': data_dict.get('organization_id', '')
            }
            c.errors = e.error_dict
            c.errors_summary = _get_errors_summary(c.errors)


def new():
    context = _get_context()

    # Basic intialization
    c.datarequest = {}
    c.errors = {}
    c.errors_summary = {}

    # Check access
    try:
        tk.check_access(constants.CREATE_DATAREQUEST, context, None)
        _process_post(constants.CREATE_DATAREQUEST, context)

        # The form is always rendered
        return tk.render('datarequests/new.html')

    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('Unauthorized to create a Data Request'))


def show(id):
    data_dict = {'id': id}
    context = _get_context()

    try:
        tk.check_access(constants.SHOW_DATAREQUEST, context, data_dict)
        c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)

        context_ignore_auth = context.copy()
        context_ignore_auth['ignore_auth'] = True

        return tk.render('datarequests/show.html')
    except tk.ObjectNotFound:
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to view the Data Request %s'
                           % id))


def update(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic intialization
    c.datarequest = {}
    c.errors = {}
    c.errors_summary = {}

    try:
        tk.check_access(constants.UPDATE_DATAREQUEST, context, data_dict)
        c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)
        c.original_title = c.datarequest.get('title')
        _process_post(constants.UPDATE_DATAREQUEST, context)
        return tk.render('datarequests/edit.html')
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to update the Data Request %s'
                           % id))


def delete(id):
    data_dict = {'id': id}
    context = _get_context()

    try:
        tk.check_access(constants.DELETE_DATAREQUEST, context, data_dict)
        datarequest = tk.get_action(constants.DELETE_DATAREQUEST)(context, data_dict)
        helpers.flash_notice(tk._('Data Request %s has been deleted') % datarequest.get('title', ''))
        tk.redirect_to(helpers.url_for(named_route='datarequest.index'))
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to delete the Data Request %s'
                           % id))


def organization_datarequests(id):
    context = _get_context()
    c.group_dict = tk.get_action('organization_show')(context, {'id': id})
    url_func = functools.partial(org_datarequest_url, id=id)
    return _show_index(None, id, False, url_func, 'organization/datarequests.html')


def user_datarequests(id):
    context = _get_context()
    c.user_dict = tk.get_action('user_show')(context, {'id': id, 'include_num_followers': True})
    url_func = functools.partial(user_datarequest_url, id=id)
    return _show_index(id, get_first(request_helpers.get_query_params('organization'), ''), True, url_func, 'user/datarequests.html')


def close(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic intialization
    c.datarequest = {}

    def _return_page(errors=None, errors_summary=None):
        errors = errors or {}
        errors_summary = errors_summary or {}
        # Get datasets (if the data req belongs to an organization,
        # only the ones that belong to the organization are shown)
        organization_id = c.datarequest.get('organization_id', '')
        if organization_id:
            base_datasets = tk.get_action('organization_show')({'ignore_auth': True}, {'id': organization_id, 'include_datasets': True})['packages']
        else:
            # FIXME: At this time, only the 500 last modified/created datasets are retrieved.
            # We assume that a user will close their data request with a recently added or modified dataset
            # In the future, we should fix this with an autocomplete form...
            # Expected for CKAN 2.3
            base_datasets = tk.get_action('package_search')({'ignore_auth': True}, {'rows': 500})['results']

        c.datasets = []
        c.errors = errors
        c.errors_summary = errors_summary
        for dataset in base_datasets:
            c.datasets.append({'name': dataset.get('name'), 'title': dataset.get('title')})

        if tk.h.closing_circumstances_enabled:
            # This is required so the form can set the currently selected close_circumstance option in the select dropdown
            c.datarequest['close_circumstance'] = get_first(request_helpers.get_post_params('close_circumstance'), None)

        return tk.render('datarequests/close.html')

    try:
        tk.check_access(constants.CLOSE_DATAREQUEST, context, data_dict)
        c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)

        if c.datarequest.get('closed', False):
            tk.abort(403, tk._('This data request is already closed'))
        elif request_helpers.has_post_params():
            data_dict = {}
            data_dict['accepted_dataset_id'] = get_first(request_helpers.get_post_params('accepted_dataset_id'))
            data_dict['id'] = id
            if tk.h.closing_circumstances_enabled:
                data_dict['close_circumstance'] = get_first(request_helpers.get_post_params('close_circumstance'))
                data_dict['approx_publishing_date'] = get_first(request_helpers.get_post_params('approx_publishing_date'))
                data_dict['condition'] = get_first(request_helpers.get_post_params('condition'))

            tk.get_action(constants.CLOSE_DATAREQUEST)(context, data_dict)
            tk.redirect_to(helpers.url_for(named_route='datarequest.show', id=data_dict['id']))
        else:   # GET
            return _return_page()

    except tk.ValidationError as e:     # Accepted Dataset is not valid
        log.warn(e)
        errors_summary = _get_errors_summary(e.error_dict)
        return _return_page(e.error_dict, errors_summary)
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to close the Data Request %s'
                           % id))


def comment(id):
    try:
        context = _get_context()
        data_dict_comment_list = {'datarequest_id': id}
        data_dict_dr_show = {'id': id}
        tk.check_access(constants.LIST_DATAREQUEST_COMMENTS, context, data_dict_comment_list)

        # Raises 404 Not Found if the data request does not exist
        c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict_dr_show)

        comment_text = get_first(request_helpers.get_post_params('comment'), '')
        comment_id = get_first(request_helpers.get_post_params('comment-id'), '')

        if request_helpers.has_post_params():
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

                helpers.flash_notice(flash_message)

            except tk.NotAuthorized as e:
                log.warn(e)
                tk.abort(403, tk._('You are not authorized to %s' % action_text))
            except tk.ValidationError as e:
                log.warn(e)
                c.errors = e.error_dict
                c.errors_summary = _get_errors_summary(c.errors)
            except tk.ObjectNotFound as e:
                log.warn(e)
                tk.abort(404, tk._(str(e)))
            # Other exceptions are not expected. Otherwise, the request will fail.

            # This is required to scroll the user to the appropriate comment
            if 'updated_comment' in locals():
                c.updated_comment = updated_comment
            else:
                c.updated_comment = {
                    'id': comment_id,
                    'comment': comment_text
                }

        # Comments should be retrieved once that the comment has been created
        get_comments_data_dict = {'datarequest_id': id}
        c.comments = tk.get_action(constants.LIST_DATAREQUEST_COMMENTS)(context, get_comments_data_dict)

        return tk.render('datarequests/comment.html')

    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found' % id))

    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to list the comments of the Data Request %s'
                           % id))


def delete_comment(datarequest_id, comment_id):
    try:
        context = _get_context()
        data_dict = {'id': comment_id}
        tk.check_access(constants.DELETE_DATAREQUEST_COMMENT, context, data_dict)
        tk.get_action(constants.DELETE_DATAREQUEST_COMMENT)(context, data_dict)
        helpers.flash_notice(tk._('Comment has been deleted'))
        tk.redirect_to(helpers.url_for(named_route='datarequest.comment', id=datarequest_id))
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Comment %s not found') % comment_id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to delete this comment'))


def follow(id):
    # Method is not called
    pass


def unfollow(id):
    # Method is not called
    pass


def get_blueprints(comments_enabled):
    datarequest = Blueprint(
        u'datarequest',
        __name__,
        url_prefix=u'/' + constants.DATAREQUESTS_MAIN_PATH
    )

    datarequest.add_url_rule(u'', view_func=index)
    datarequest.add_url_rule(u'/new', view_func=new, methods=['GET', 'HEAD', 'POST'])
    datarequest.add_url_rule(u'/<id>', view_func=show)
    datarequest.add_url_rule(u'/edit/<id>', view_func=update, methods=['GET', 'HEAD', 'POST'])
    datarequest.add_url_rule(u'/delete/<id>', view_func=delete, methods=['POST'])
    datarequest.add_url_rule(u'/close/<id>', view_func=close, methods=['GET', 'HEAD', 'POST'])
    datarequest.add_url_rule(u'/follow/<id>', view_func=follow, methods=['POST'])
    datarequest.add_url_rule(u'/unfollow/<id>', view_func=unfollow, methods=['POST'])

    if comments_enabled:
        datarequest.add_url_rule(u'/comment/<id>', view_func=comment, methods=['GET', 'HEAD', 'POST'])
        datarequest.add_url_rule(u'/comment/<datarequest_id>/delete/<comment_id>', view_func=delete_comment, methods=['GET', 'HEAD', 'POST'])

    organization = Blueprint(
        u'organization_datarequest',
        __name__,
        url_prefix=u'/organization/' + constants.DATAREQUESTS_MAIN_PATH
    )
    organization.add_url_rule(u'/<id>', view_func=organization_datarequests)

    user = Blueprint(
        u'user_datarequest',
        __name__,
        url_prefix=u'/user/' + constants.DATAREQUESTS_MAIN_PATH
    )
    user.add_url_rule(u'/<id>', view_func=user_datarequests)

    return [datarequest, organization, user]