import re
import yaml
import gitlab
import pandas as pd
from tqdm import tqdm
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Settings


def get_project_file_paths(project, branch_name, path=''):
    file_paths = []
    items = project.repository_tree(path=path, all=True, recursive=False, ref=branch_name)
    for item in items:
        if item['type'] == 'blob':  # 'blob' indicates a file
            file_paths.append(item['path'])
        elif item['type'] == 'tree':  # 'tree' indicates a directory
            file_paths.extend(get_project_file_paths(project, branch_name, item['path']))
    return file_paths


def is_conventional_commit(message):
    pattern = r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(\S+\))?: .{1,}'
    return re.match(pattern, message) is not None


# Function to calculate the percentage of conventional commits by each user for a given project
def calculate_conventional_commit_percentage(project):
    # Get commits from the project
    commits = project.commits.list(all=True)

    # Initialize dictionaries to store counts
    total_commits_by_user = {}
    conventional_commits_by_user = {}

    # Check each commit message and count
    for commit in commits:
        author = commit.author_name
        total_commits_by_user[author] = total_commits_by_user.get(author, 0) + 1
        if is_conventional_commit(commit.message):
            conventional_commits_by_user[author] = conventional_commits_by_user.get(author, 0) + 1

    # Calculate percentages
    percentage_conventional_by_user = {}
    for user, total_commits in total_commits_by_user.items():
        conventional_commits = conventional_commits_by_user.get(user, 0)
        percentage = (conventional_commits / total_commits) * 100
        percentage_conventional_by_user[user] = percentage

    return percentage_conventional_by_user


def get_commits_by_branch(project):
    branches_commits = {}
    branches = project.branches.list(all=True)
    for branch in branches:
        commits = project.commits.list(all=True, query_parameters={'ref_name': branch.name})
        branches_commits[branch.name] = [commit.id for commit in commits]
    return branches_commits


def get_ci_cd_stages(project, branch_name='main'):
    try:
        # Get the file content
        file_content = project.files.get(file_path='.gitlab-ci.yml', ref=branch_name)
        # Decode the file content
        file_data = yaml.safe_load(file_content.decode())
        # Return the list of stages
        return file_data.get('stages', [])
    except Exception as e:
        print(f"Error getting CI/CD stages: {e}")
        return None


def has_tests(project):
    items = project.repository_tree(all=True)
    for item in items:
        if item['type'] == 'tree' and item['name'].lower() == 'tests':
            return True
    return False


def process_project(project):
    try:
        main_developers = Counter([x.author_name for x in project.commits.list(get_all=True, all=True)])
        commit_per_branch = get_commits_by_branch(project)
        most_commited_branch = max(commit_per_branch, key=commit_per_branch.get)
        project_files = get_project_file_paths(project, branch_name=most_commited_branch)
        project_data = {
            'Name': project.name,
            'Link': project.web_url,
            'Creation Date': project.created_at.split('T')[0],
            'Number of Commits': len(project.commits.list(get_all=True, all=True)),
            'Number of Branches': len(project.branches.list(get_all=True, all=True)),
            'Commits per Branch': commit_per_branch,
            'Conventional Commits Status': calculate_conventional_commit_percentage(project),
            'Default Branch': project.default_branch,
            'Most Commited Branch': most_commited_branch,
            'Main Developers': main_developers,
            'Has Docker': 'yes' if sum([1 for file in project_files if 'dockerfile' in file]) else 'no',
            'Has docker-compose': 'yes' if sum([1 for file in project_files if 'docker-compose' in file]) else 'no',
            'Languages': get_language_percentages(project),
            'Has CI / CD': 'yes' if '.gitlab-ci.yml' in project_files else 'no',
            'Has Docker compose': 'yes' if 'docker-compose.yml' in project_files else 'no',
            'has tests': has_tests(project),
            # 'Number of connected CI/CD Servers': ...,
            # 'Technologies': ...
        }
        return project_data
    except Exception as e:
        print(f'Error in getting {project.name} data: {e}')
        return None


def get_language_percentages(project):
    percentages = project.languages()
    # total_bytes = sum(languages.values())
    # percentages = {language: (bytes / total_bytes * 100) for language, bytes in languages.items()}
    return percentages


if __name__ == '__main__':
    settings = Settings()
    # Process projects in parallel
    # Connect to GitLab
    gl = gitlab.Gitlab(settings.gitlab_url, private_token=settings.access_token)

    # Get all projects
    projects = gl.projects.list(all=True)

    # Group projects by group
    grouped_projects = {}
    for project in projects:
        group_name = project.namespace['name']
        if group_name not in grouped_projects:
            grouped_projects[group_name] = []
        grouped_projects[group_name].append(project)

    # For each group, create a DataFrame and save it to an Excel file
    with pd.ExcelWriter('./gitlab_projects.xlsx') as writer:
        for group, projects in grouped_projects.items():
            data = []
            print(f'group name = {group}')
            for project in tqdm(projects):
                try:
                    project_data = process_project(project=project)
                    data.append(project_data)
                except Exception as e:
                    print(f'Error in getting {project.name} data: {e}')

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Write to a different sheet
            df.to_excel(writer, sheet_name=group)
    # with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
    #     future_to_project = {executor.submit(process_project, project): project for project in projects}
    #     for future in as_completed(future_to_project):
    #         project = future_to_project[future]
    #         try:
    #             data = future.result()
    #             if data:
    #                 # Process the data (e.g., append it to a DataFrame or list)
    #                 pass
    #         except Exception as e:
    #             print(f'Error processing project {project.name}: {e}')
