#!/usr/bin/env python
"""
This syncs markdown files from a file or folder to Confluence as child pages of a given parent.

Features:
- Can exclude files as well
- Compares pages before updating

If selecting a single file, it assumes the file you want to sync is located in the main repo dir,
but the path is editable, currently in the GitHub Action or your favorite python environment.
"""

import difflib
import os
import sys
import requests
from markdown_it import MarkdownIt


def load_environment_variables():
    """
    Load environment variables and check for required values.
    """
    env_var_names = {
        "cloud": "INPUT_CLOUD",
        "user": "INPUT_USER",
        "token": "INPUT_TOKEN",
        "parent_page_id": "INPUT_PARENT_PAGE_ID",
        "space_id": "INPUT_SPACE_ID",
        "input_file": "INPUT_INPUT_FILE",
        "input_md_directory": "INPUT_INPUT_MD_DIRECTORY",
        "exclude_files": "INPUT_EXCLUDE_FILES"
    }

    envs = {}
    for var_name, input_name in env_var_names.items():
        envs[var_name] = os.environ.get(input_name)
        if not envs[var_name] and var_name not in [
            "input_file", 
            "input_md_directory", 
            "exclude_files"
        ]:
            print(f"Missing value for {var_name}")
            sys.exit(1)

    return envs


def read_markdown_file(md_file):
    """
    Read a markdown file.
    """
    with open(md_file, encoding="utf-8") as f:
        return f.read()


def render_html(md_content):
    """
    Render the page so Confluence understands it
    """
    markdown = MarkdownIt()
    return markdown.render(md_content)


def get_page_title(md_file):
    """
    Extract the page title from the Markdown file title
    """
    return os.path.splitext(os.path.basename(md_file))[0]


def process_directory(envs, links):
    """
    Process a directory of markdown files
    """
    md_directory = os.path.join(
        os.environ["GITHUB_WORKSPACE"], envs["input_md_directory"]
    )
    if envs.get("exclude_files"):
        exclude_files = envs["exclude_files"].split(",")
    else:
        exclude_files = []

    for root, _, files in os.walk(md_directory):
        for f in files:
            if f.endswith(".md") and f not in exclude_files:
                md_file = os.path.join(root, f)
                links = process_file(md_file, envs, links)

    return links


def update_confluence_page(envs, config, links):
    """
    Update a Confluence page
    """
    update_url = (
        f"https://{envs['cloud']}.atlassian.net/wiki/api/v2/pages/{config['page_id']}"
    )
    headers = {"Content-Type": "application/json"}
    update_content = {
        "id": config["page_id"],
        "status": "current",
        "version": {"number": config["new_version"]},
        "title": config["page_title"],
        "body": {"value": config["html"], "representation": "storage"},
    }

    update_response = requests.put(
        update_url,
        json=update_content,
        auth=(envs["user"], envs["token"]),
        headers=headers,
        timeout=10,
    )

    if update_response.status_code == 200:
        updated_link = (
            f"https://{envs['cloud']}.atlassian.net/wiki"
            + update_response.json()["_links"]["webui"]
        )
        links.append(f"{config['page_title']}: {updated_link}")
        print(f"{config['page_title']}: Success. New version: {config['new_version']}")
    else:
        print(
            f"{config['page_title']}: Failed. HTTP status code: {update_response.status_code}"
        )


def create_confluence_page(envs, page_title, html, links):
    """
    Create a Confluence page
    """
    url = f"https://{envs['cloud']}.atlassian.net/wiki/api/v2/pages"
    content = {
        "spaceId": envs["space_id"],
        "status": "current",
        "title": page_title,
        "parentId": envs["parent_page_id"],
        "body": {"value": html, "representation": "storage"},
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    response = requests.post(
        url,
        json=content,
        auth=(envs["user"], envs["token"]),
        headers=headers,
        timeout=10,
    )

    if response.status_code == 200:
        link = (
            f"https://{envs['cloud']}.atlassian.net/wiki"
            + response.json()["_links"]["webui"]
        )
        links.append(f"{page_title}: {link}")
        print(f"{page_title}: Content upload successful.")
    else:
        print(f"{page_title}: Failed. HTTP status code: {response.status_code}")


def process_file(md_file, envs, links):
    """
    Process a file and ensure formatting
    """
    new_version = None
    md_content = read_markdown_file(md_file)
    html = render_html(md_content)
    page_title = get_page_title(md_file)
    page_id, current_version, page_content = find_page_by_title(page_title, envs)

    if current_version:
        new_version = current_version + 1

    if page_id:
        adjusted_html = html.strip()
        adjusted_page = page_content.strip()
        differ = difflib.Differ()
        diff = list(differ.compare(adjusted_html, adjusted_page))

        # Check if there are substantial differences
        if any(line.startswith("+ ") or line.startswith("- ") for line in diff):
            update_confluence_page(
                envs,
                {
                    "page_id": page_id,
                    "page_title": page_title,
                    "html": html,
                    "new_version": new_version,
                },
                links,
            )
        else:
            print(f"{page_title}: Identical content, no update required.")
    else:
        create_confluence_page(envs, page_title, html, links)

    return links


# update this to find by ID
def find_page_by_title(page_title, envs):
    """
    Find a Confluence page by title.
    """
    url = f"https://{envs['cloud']}.atlassian.net/wiki/api/v2/pages"
    params = {
        "title": page_title,
    }
    headers = {"Accept": "application/json"}
    response = requests.get(
        url,
        params=params,
        auth=(envs["user"], envs["token"]),
        headers=headers,
        timeout=10,
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            page_id = data["results"][0]["id"]
            version_number = data["results"][0]["version"]["number"]

            page_url = (
                f"https://{envs['cloud']}.atlassian.net/wiki/rest/api/content/"
                f"{page_id}?expand=body.storage"
            )
            page_response = requests.get(
                page_url,
                auth=(envs["user"], envs["token"]),
                headers=headers,
                timeout=10,
            )
            page = page_response.json()
            page_content = page["body"]["storage"]["value"]

            return page_id, version_number, page_content

    return None, None, None


def main():
    """
    Main function that orchestrates it all
    """
    envs = load_environment_variables()
    links = []
    if "input_file" in envs:
        # Process a single file
        single_file = os.path.join(os.environ["GITHUB_WORKSPACE"], envs["input_file"])
        links = process_file(single_file, envs, links)
    elif "input_md_directory" in envs:
        # Process a directory of markdown files
        links = process_directory(envs, links)
    else:
        # Handle the case where neither are provided
        print("No specific input provided.")
        sys.exit(1)

    print(links)


if __name__ == "__main__":
    main()
