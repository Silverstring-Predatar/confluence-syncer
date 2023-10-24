# Confluence Syncer

This Action copies the contents of a Markdown `.md` file or folder to a Confluence cloud parent page, with more features.

## Getting Started

```yml
      - uses: humanendpoint/confluence-syncer@v1.5
        with:
          input_md_directory: wiki
          exclude_files: this.md,that.md
          cloud: company
          space_id: ${{ secrets.CONFLUENCE_SPACE_ID }}
          parent_page_id: ${{ secrets.JIRA_SCRIPTS_PARENT_PAGE_ID }}
          user: ${{ secrets.JIRA_USER }}
          token: ${{ secrets.JIRA_TOKEN }}
```

## Authentication

Uses a token for the rest api v2.

## Input variables

- `input_md_directory`: The folder you want to sync

- `input_file`: If you don't want to sync a folder, you can also sync a single markdown file.

*WARNING! ONLY ONE OF THE ABOVE! (but one of them is required)*

- `cloud`: The ID can be found by looking at your confluence domain: `https://<cloud>.atlassian.net/...`

- `space_id`: The space ID of the page

- `parent_page_id`: The parent page ID of the page you want to crate a child page under

- `user`: The user that generated the access token

- `token`: You can generate the token [here](https://id.atlassian.com/manage-profile/security/api-tokens). Link to [Docs](https://confluence.atlassian.com/cloud/api-tokens-938839638.html)

*Not required*:

- `exclude_files`: If there are files in the folder you would want to exclude
