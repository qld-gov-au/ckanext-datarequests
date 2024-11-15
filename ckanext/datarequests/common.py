# -*- coding: utf-8 -*-

# Copyright (c) 2021 Queensland Government

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

import os

import ckan.lib.helpers as h
from ckan.plugins.toolkit import config


def get_config_bool_value(config_name, default_value=False):
    value = config.get(config_name, default_value)
    value = value if isinstance(value, bool) else value != 'False'
    return value


def is_fontawesome_4():
    if hasattr(h, 'ckan_version'):
        ckan_version = float(h.ckan_version()[0:3])
        return ckan_version >= 2.7
    else:
        return False


def get_plus_icon():
    return 'plus-square' if is_fontawesome_4() else 'plus-sign-alt'


def get_question_icon():
    return 'question-circle' if is_fontawesome_4() else 'question-sign'


def _load_words(filepath):
    if os.path.isfile(filepath):
        f = open(filepath, 'r')
        x = f.read().splitlines()
        f.close()
    else:
        x = []
    return x


def load_bad_words():
    filepath = config.get('ckan.comments.bad_words_file', None)
    if not filepath:
        filepath = os.path.dirname(os.path.realpath(__file__)) + '/bad_words.txt'
    return _load_words(filepath)


def load_good_words():
    filepath = config.get('ckan.comments.good_words_file', None)
    if not filepath:
        filepath = os.path.dirname(os.path.realpath(__file__)) + '/good_words.txt'
    return _load_words(filepath)


def profanity_check(cleaned_comment):
    from profanityfilter import ProfanityFilter

    custom_profanity_list = config.get('ckan.comments.profanity_list', [])

    if custom_profanity_list:
        pf = ProfanityFilter(custom_censor_list=custom_profanity_list.splitlines())
    else:
        # Fall back to original behaviour of built-in Profanity bad words list
        # combined with bad_words_file and good_words_file
        more_words = load_bad_words()
        whitelist_words = load_good_words()

        pf = ProfanityFilter(extra_censor_list=more_words)
        for word in whitelist_words:
            pf.remove_word(word)

    return pf.is_profane(cleaned_comment)
