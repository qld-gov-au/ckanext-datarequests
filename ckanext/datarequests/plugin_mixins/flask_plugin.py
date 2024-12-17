# encoding: utf-8

import ckan.plugins as p
from flask import Blueprint

from ckanext.datarequests import cli, common, constants
from ckanext.datarequests.controllers import controller_functions


datarequests_bp = Blueprint("datarequest", __name__)
datarequests_bp.add_url_rule(
    "/" + constants.DATAREQUESTS_MAIN_PATH,
    endpoint="index",
    view_func=controller_functions.index,
    methods=('GET',)
)
datarequests_bp.add_url_rule(
    "/{}/new".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="new",
    view_func=controller_functions.new,
    methods=('GET', 'POST',)
)
datarequests_bp.add_url_rule(
    "/{}/new".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="new",
    view_func=controller_functions.new,
    methods=('GET', 'POST',)
)
datarequests_bp.add_url_rule(
    "/{}/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="show",
    view_func=controller_functions.show,
    methods=('GET',)
)
datarequests_bp.add_url_rule(
    "/{}/edit/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="update",
    view_func=controller_functions.update,
    methods=('GET', 'POST',)
)
datarequests_bp.add_url_rule(
    "/{}/delete/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="delete",
    view_func=controller_functions.delete,
    methods=('POST',)
)
datarequests_bp.add_url_rule(
    "/{}/close/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="close",
    view_func=controller_functions.close,
    methods=('GET', 'POST',)
)
datarequests_bp.add_url_rule(
    "/{}/follow/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="follow",
    view_func=controller_functions.follow,
    methods=('POST',)
)
datarequests_bp.add_url_rule(
    "/{}/unfollow/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="unfollow",
    view_func=controller_functions.unfollow,
    methods=('POST',)
)
datarequests_bp.add_url_rule(
    "/organization/{}/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="organization",
    view_func=controller_functions.organization,
    methods=('GET',)
)
datarequests_bp.add_url_rule(
    "/user/{}/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="user",
    view_func=controller_functions.user,
    methods=('GET',)
)
datarequests_bp.add_url_rule(
    "/{}/purge/<user_id>".format(constants.DATAREQUESTS_MAIN_PATH),
    endpoint="purge",
    view_func=controller_functions.purge,
    methods=('GET', 'POST',)
)
if common.get_config_bool_value('ckan.datarequests.comments', True):
    datarequests_bp.add_url_rule(
        "/{}/comment/<id>".format(constants.DATAREQUESTS_MAIN_PATH),
        endpoint="comment",
        view_func=controller_functions.comment,
        methods=('GET', 'POST',)
    )
    datarequests_bp.add_url_rule(
        "/{}/comment/<datarequest_id>/delete/<comment_id>".format(
            constants.DATAREQUESTS_MAIN_PATH),
        endpoint="delete_comment",
        view_func=controller_functions.delete_comment,
        methods=('GET', 'POST',)
    )


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IClick)

    # IBlueprint

    def get_blueprint(self):
        return [datarequests_bp]

    # IClick

    def get_commands(self):
        return cli.get_commands()
