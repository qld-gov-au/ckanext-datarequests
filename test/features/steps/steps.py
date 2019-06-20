from behave import when
from behaving.web.steps import *  # noqa: F401, F403
from behaving.personas.steps import *  # noqa: F401, F403
from behaving.web.steps.url import when_i_visit_url
from behaving.mail.steps import *
import random

@when('I go to homepage')
def go_to_home(context):
    when_i_visit_url(context, '/')


@when('I log in')
def log_in(context):

    assert context.persona
    context.execute_steps(u"""
        When I fill in "login" with "$name"
        And I fill in "password" with "$password"
        And I press the element with xpath "//button[contains(string(), 'Login')]"
    """)

@when('I log in and go to datarequest page')
def log_in_go_to_datarequest(context):

    assert context.persona
    context.execute_steps(u"""
        When I go to homepage
        And I click the link with text that contains "Log in"
        And I log in
        And I go to datarequest page
    """)

@when('I go to datarequest page')
def go_to_datarequest(context):
    when_i_visit_url(context, '/datarequest')

@when('I fill in title with random text')
def title_random_text(context):

    assert context.persona
    context.execute_steps(u"""
        When I fill in "title" with "Test Title {0}"
    """.format(random.randrange(100)) )
