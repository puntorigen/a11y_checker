# A11y PR Checker

A GitHub Action for checking pull requests (PRs) against accessibility guidelines and provide suggested fixes as comments. It uses a team of experts to assess and validate incremental accesibility issues on your repositories.

## Requirements

- OpenAI API Key

## Sample Usage

1. Create a GitHub workflow template in your repository like the following:

    ```yml
    name: PR A11Y BOT

    on:
      pull_request:
        types: [opened, synchronize, reopened]

    # This is needed for the action to be able to post comments
    permissions:
      issues: write
      pull-requests: write
      contents: read

    jobs:
      test-action:
        runs-on: ubuntu-latest

        steps:
          - name: Checkout code
            uses: actions/checkout@v2

          - name: Run PR BOT
            uses: puntorigen/a11y-checker@v1.0.0
            with:
              github-token: ${{ secrets.GITHUB_TOKEN }}
              openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    ```

Now, every time you create a PR in your repository, the action will check if it complies with the WCAG accessibility guidelines. It will then post a comment with the results, indicating whether the PR is successful or not. If the PR has breaking guidelines, an explanation will be provided below the non-compliant files alongside a suggested fix.


#### This project is based on the [pr-rules](github.com/puntorigen/pr-rules) project.