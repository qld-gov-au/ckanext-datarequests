@smoke
Feature: Datarequest

# DQL-26: Data Requests - Install and configure extensionUAT - the Data Requests are accessible via the /datarequest URL (does not display a 404 error)
    Scenario: Browse to data request page
        When I go to datarequest page
        Then the browser's URL should contain "/datarequest"


# DQL-27: Data Base & Form updatesUAT - when visiting the /datarequests page as a non-logged in user, the button at the top of the page reads "Login to create a data request" and links to the /user/login page
    Scenario: View 'Login to create data request' button when not logged in
        When I go to datarequest page
        Then I should see an element with xpath "//a[contains(string(), 'Login to create data request')]"


# DQL-27: Data Base & Form updatesUAT - after logging in, the user is redirected to the /datarequests page and the "Add Data Request" button is visible
    Scenario: Clicking 'Login to create data request' button will redirect to login page
        Given "SysAdmin" as the persona
        When I go to datarequest page
        And I click the link with text "Login to create data request"
        And I log in
        Then I should see an element with xpath "//a[contains(string(), 'Add data request')]"

# DQL-27: Data Base & Form updatesUAT - data requests submitted without a description will produce an error message
    Scenario: Submit new data request without description value will show error message
        Given "SysAdmin" as the persona
        When I log in and go to datarequest page
        And I click the link with text that contains "Add data request"
        And I fill in "title" with "Test data request"
        And I press the element with xpath "//button[contains(string(), 'Create data request')]"
        Then I should see an element with the css selector "div.error-explanation.alert.alert-error" within 2 seconds
        And I should see "The form contains invalid entries" within 1 seconds    
        And I should see an element with the css selector "span.error-block" within 1 seconds
        And I should see "Description cannot be empty" within 1 seconds
    

# DQL-39: Data Requests - Ability to Re-open Data RequestUAT - Sysadmin or Admin users of the assigned organisation for a data request can see a "Re-open" button on the data request detail page for closed data requests
    Scenario Outline: Admin users should see Re-open button on closed data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Closed Request"
        Then I should see an element with xpath "//a[@class='btn btn-success' and contains(string(), ' Re-open')]"

        Examples: Users  
        | User              |
        | SysAdmin          |
        | DataRequestAdmin  |

    Scenario Outline: Non-admin users should not see Re-open button on closed data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Closed Request"
        Then I should not see an element with xpath "//a[@class='btn btn-success' and contains(string(), ' Re-open')]"

        Examples: Users  
        | User              |
        | CKANUser          |
        | DataRequestEditor |
        | DataRequestMember |
        | SalsaAdmin        |
        | SalsaEditor       |
        | SalsaMember       |

# DQL-39: Data Requests - Ability to Re-open Data RequestUAT - the data request creator, Sysadmin and Admin users of the assigned organisation for a data request can see a "Close" button on the data request detail page for opened data requests
    Scenario Outline: Admin users should see Close button on open data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Test Request"
        Then I should see an element with xpath "//a[contains(string(), 'Close')]"

        Examples: Users  
        | User              |
        | SysAdmin          |
        | DataRequestAdmin  |

    Scenario Outline: Non admin users should not see Close button on open data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Test Request"
        Then I should not see an element with xpath "//a[contains(string(), 'Close')]"

        Examples: Users  
        | User              |
        | CKANUser          |
        | DataRequestEditor |
        | DataRequestMember |
        | SalsaAdmin        |
        | SalsaEditor       |
        | SalsaMember       |


# DQL-29: Data Requests - Update email notifications
    Scenario: Creating a new data request should email the Admin users of the organisation
        Given "CKANUser" as the persona
        When I log in and go to datarequest page
        And I click the link with text that contains "Add data request"
        And I fill in title with random text
        And I fill in "description" with "Test description"
        And I press the element with xpath "//button[contains(string(), 'Create data request')]"
        When I wait for 2 seconds
        And I should receive an email at "dr_admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "admin@localhost" with subject "Queensland Government Open Data - Data Request"