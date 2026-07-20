@smoke
Feature: Homepage

    @homepage
    @unauthenticated
    Scenario: Smoke test to ensure Homepage is accessible
        Given "Unauthenticated" as the persona
        When I go to homepage
        Then I should see an element with xpath "//nav[contains(@class, 'navbar')]//li/a[contains(@href, '/datarequest')]/span[contains(@class, 'badge')]"
