# encoding: utf-8

import click

from . import db


@click.group()
def datarequests():
    """ Data Request commands
    """
    pass


@datarequests.command()
def init_db():
    """ Create tables to store data requests.
    """
    db.init_db()


@datarequests.command()
def update_db():
    """ Make any database updates that may have been defined
    after tables were created.
    """
    db.update_db()


def get_commands():
    return [datarequests]
