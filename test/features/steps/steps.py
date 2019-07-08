from behave import when, then
from behaving.web.steps import *  # noqa: F401, F403
from behaving.personas.steps import *  # noqa: F401, F403
from behaving.web.steps.url import when_i_visit_url
from behaving.mail.steps import *
import random
import email
import quopri

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
    """.format(random.randrange(1000)) )

# The default behaving step does not convert base64 emails
# Modifed the default step to decode the payload from base64
@then(u'I should receive an email at "{address}" containing "{text}"')
def should_receive_email_containing_text(context, address, text):
    def filter_contents(mail):
        mail = email.message_from_string(mail)
        payload = mail.get_payload()
        payload += "=" * ((4 - len(payload) % 4) % 4) # do fix the padding error issue
        decoded_payload = quopri.decodestring(payload).decode('base64')
        return text in decoded_payload

    assert context.mail.user_messages(address, filter_contents)
