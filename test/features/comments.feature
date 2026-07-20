@comments
Feature: Comments

    @comment-add
    Scenario: When a logged-in user submits a comment on a Data Request the comment should then be visible on the Comments tab of the Data Request
        Given "TestOrgMember" as the persona
        When I log in
        And I create a datarequest
        And I go to data request "$last_generated_title" comments
        And I submit a comment with subject "Test subject" and comment "This is a test comment"
        Then I should see "This is a test comment" within 10 seconds
        And I should see an element with xpath "//ul[contains(@class, 'nav-tabs')]/li/a[contains(@href, '/datarequest/comment')]/span[contains(@class, 'badge')]"

    @comment-delete
    Scenario: When an admin visits a data request, they can delete a comment and should not see text 'This comment was deleted.'
        Given "SysAdmin" as the persona
        When I log in
        And I go to data request "Test Request" comments
        And I submit a comment with subject "Comment for deletion" and comment "This is a data request comment to test deletion"
        And I press the element with xpath "//a[contains(@href, '/delete')]/i[contains(@class, 'icon-remove')]"
        Then I should see "Are you sure you want to delete this comment?" within 1 seconds
        When I press the element with xpath "//button[contains(string(), 'Confirm')]"
        Then I should see "Comment has been deleted" within 2 seconds

    @comment-add @comment-profane @datarequest
    Scenario: When a logged-in user submits a comment containing profanity on a Data Request they should receive an error message and the comment will not appear
        Given "CKANUser" as the persona
        When I log in
        And I create a datarequest
        And I go to data request "$last_generated_title" comments
        And I submit a comment with subject "Test subject" and comment "He had sheep, and oxen, and he asses, and menservants, and maidservants, and she asses, and camels."
        Then I should see "Comment blocked due to profanity" within 5 seconds
