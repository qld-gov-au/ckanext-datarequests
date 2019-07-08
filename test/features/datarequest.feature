Feature: Datarequest

# Data Requests - Install and configure extensionUAT - the Data Requests are accessible via the /datarequest URL (does not display a 404 error)
    Scenario: Browse to data request page
        When I go to datarequest page
        Then the browser's URL should contain "/datarequest"


# Data Base & Form updatesUAT - when visiting the /datarequests page as a non-logged in user, the button at the top of the page reads "Login to create a data request" and links to the /user/login page
    Scenario: View 'Login to create data request' button when not logged in
        When I go to datarequest page
        Then I should see an element with xpath "//a[contains(string(), 'Login to create data request')]"


# Data Base & Form updatesUAT - after logging in, the user is redirected to the /datarequests page and the "Add Data Request" button is visible
    Scenario: Clicking 'Login to create data request' button will redirect to login page
        Given "SysAdmin" as the persona
        When I go to datarequest page
        And I click the link with text "Login to create data request"
        And I log in
        Then I should see an element with xpath "//a[contains(string(), 'Add data request')]"

# Data Base & Form updatesUAT - data requests submitted without a description will produce an error message
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
    

# Data Requests - Ability to Re-open Data RequestUAT - Sysadmin or Admin users of the assigned organisation for a data request can see a "Re-open" button on the data request detail page for closed data requests
    Scenario Outline: Admin users should see Re-open button on closed data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Closed Request"
        Then I should see an element with xpath "//a[@class='btn btn-success' and contains(string(), ' Re-open')]"

        Examples: Users  
        | User                  |
        | SysAdmin              |
        | DataRequestOrgAdmin   |

    Scenario Outline: Non-admin users should not see Re-open button on closed data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Closed Request"
        Then I should not see an element with xpath "//a[@class='btn btn-success' and contains(string(), ' Re-open')]"

        Examples: Users  
        | User                  |
        | CKANUser              |
        | DataRequestOrgEditor  |
        | DataRequestOrgMember  |
        | TestOrgAdmin          |
        | TestOrgEditor         |
        | TestOrgMember         |

# Data Requests - Ability to Re-open Data RequestUAT - the data request creator, Sysadmin and Admin users of the assigned organisation for a data request can see a "Close" button on the data request detail page for opened data requests
    Scenario Outline: Admin users should see Close button on open data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Test Request"
        Then I should see an element with xpath "//a[contains(string(), 'Close')]"

        Examples: Users  
        | User                  |
        | SysAdmin              |
        | DataRequestOrgAdmin   |

    Scenario Outline: Non admin users should not see Close button on open data request
        Given "<User>" as the persona
        When I log in and go to datarequest page
        And I press "Test Request"
        Then I should not see an element with xpath "//a[contains(string(), 'Close')]"

        Examples: Users  
        | User                  |
        | CKANUser              |
        | DataRequestOrgEditor  |
        | DataRequestOrgMember  |
        | TestOrgAdmin          |
        | TestOrgEditor         |
        | TestOrgMember         |


# Data Requests - Email notifications
    Scenario: Creating a new data request should email the Admin users of the organisation
        Given "TestOrgEditor" as the persona
        When I log in and go to datarequest page
        And I click the link with text that contains "Add data request"
        And I fill in title with random text
        And I fill in "description" with "Test description"
        And I press the element with xpath "//button[contains(string(), 'Create data request')]"
        When I wait for 3 seconds
        Then I should receive an email at "dr_admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "dr_admin@localhost" containing "A new data request has been added and assigned to your organisation."
        And I should receive an email at "admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "admin@localhost" containing "A new data request has been added and assigned to your organisation."

    Scenario: Closing a data request should email the creator
        Given "DataRequestOrgAdmin" as the persona
        When I log in and go to datarequest page
        And I click the link with text that contains "Add data request"
        And I fill in title with random text
        And I fill in "description" with "Test description"
        And I press the element with xpath "//button[contains(string(), 'Create data request')]"
        And I press the element with xpath "//a[contains(string(), 'Close')]"
        And I press the element with xpath "//button[contains(string(), 'Close data request')]"
        When I wait for 3 seconds
        Then I should receive an email at "dr_admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "dr_admin@localhost" containing "Your data request has been closed."

    Scenario: Re-Opening a data request should email the Admin users of the organisation and creator
        Given "DataRequestOrgAdmin" as the persona
        When I log in and go to datarequest page
        And I click the link with text that contains "Add data request"
        And I fill in title with random text
        And I fill in "description" with "Test description"
        And I press the element with xpath "//button[contains(string(), 'Create data request')]"
        And I press the element with xpath "//a[contains(string(), 'Close')]"
        And I press the element with xpath "//button[contains(string(), 'Close data request')]"
        And I press the element with xpath "//a[@class='btn btn-success' and contains(string(), ' Re-open')]"
        When I wait for 3 seconds
        Then I should receive an email at "dr_admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "dr_admin@localhost" containing "Your data request has been re-opened."
        And I should receive an email at "admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "admin@localhost" containing "A data request assigned to your organisation has been re-opened."

     Scenario: Re-assigning a data request should email the Admin users of the assigned organisation and un-assigned organisation
        Given "DataRequestOrgAdmin" as the persona
        When I log in and go to datarequest page
        And I click the link with text that contains "Add data request"
        And I fill in title with random text
        And I fill in "description" with "Test description"
        And I press the element with xpath "//button[contains(string(), 'Create data request')]"
        And I press the element with xpath "//a[contains(string(), 'Manage')]"
        When I wait for 3 seconds
        # Have to use JS to change the selected value as the behaving framework does not work with autocomplete dropdown
        Then I execute the script "document.getElementById('field-organizations').value = document.getElementById('field-organizations').options[1].value"
        And I press the element with xpath "//button[contains(string(), 'Update data request')]"
        When I wait for 3 seconds
        Then I should receive an email at "admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "admin@localhost" containing "A data request that was assigned to your organisation has been re-assigned to another organisation."
        And I should receive an email at "test_org_admin@localhost" with subject "Queensland Government Open Data - Data Request"
        And I should receive an email at "test_org_admin@localhost" containing "A new data request has been added and assigned to your organisation."