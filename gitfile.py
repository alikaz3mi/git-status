import re
import yaml
import gitlab
import pandas as pd
from tqdm import tqdm
from typing import List, Dict
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor

from gitlab.v4.objects.projects import Project

from config import Settings
from utils.basic_logger import simple_logger

logger = simple_logger(__name__)


def get_project_file_paths(project: Project, branch_name: str, path: str = '') -> List[str]:
    file_paths = []
    items = project.repository_tree(path=path, all=True, recursive=False, ref=branch_name)
    for item in items:
        if item['type'] == 'blob':  # 'blob' indicates a file
            file_paths.append(item['path'])
        elif item['type'] == 'tree':  # 'tree' indicates a directory
            file_paths.extend(get_project_file_paths(project, branch_name, item['path']))
    return file_paths


def is_conventional_commit(message: str) -> bool:
    pattern = r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(\S+\))?: .{1,}'
    return re.match(pattern, message) is not None


# Function to calculate the percentage of conventional commits by each user for a given project
def calculate_conventional_commit_percentage(project: Project) -> Dict[str, float]:
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


def get_num_commits_by_branch(project: Project) -> Dict[str, int]:
    branches_commits = {}
    branches = project.branches.list(all=True)
    for branch in branches:
        commits = project.commits.list(all=True, query_parameters={'ref_name': branch.name})
        branches_commits[branch.name] = len(commits)
    return branches_commits


def get_ci_cd_stages(project: Project, branch_name='main') -> List[str]:
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


def has_tests(project: Project) -> bool:
    items = project.repository_tree(all=True)
    for item in items:
        if item['type'] == 'tree' and item['name'].lower() == 'tests':
            return True
    return False


def process_project(project: Project) -> Dict[str, str] | None:
    try:
        main_developers = dict(Counter([x.author_name for x in project.commits.list(get_all=True, all=True)]))
        num_commit_per_branch = get_num_commits_by_branch(project)
        most_committed_branch = max(num_commit_per_branch, key=num_commit_per_branch.get)
        project_files = get_project_file_paths(project, branch_name=most_committed_branch)
        project_data = {
            'Name': project.name,
            'Group Name': project.namespace['name'],
            'Link': project.web_url,
            'Creation Date': project.created_at.split('T')[0],
            'Last Commit Date': project.last_activity_at.split('T')[0],
            'Number of Commits': len(project.commits.list(get_all=True, all=True)),
            'Number of Branches': len(project.branches.list(get_all=True, all=True)),
            'Commits per Branch': num_commit_per_branch,
            'Conventional Commits Status': calculate_conventional_commit_percentage(project),
            'Default Branch': project.default_branch,
            'Most Committed Branch': most_committed_branch,
            'Main Developers': main_developers,
            'Has Docker': 'yes' if sum([1 for file in project_files if 'dockerfile' in file]) else 'no',
            'Has docker-compose': 'yes' if sum([1 for file in project_files if 'docker-compose' in file]) else 'no',
            'Languages': get_language_percentages(project),
            'Has CI / CD': 'yes' if '.gitlab-ci.yml' in project_files else 'no',
            'Has Docker compose': 'yes' if 'docker-compose.yml' in project_files else 'no',
            'Has Tests': 'yes' if has_tests(project) else 'no',
            'Number of connected CI/CD Servers': len(project.hooks.list()),
            'Technologies': ''
        }
        return project_data
    except Exception as e:
        logger.error(f'Error in getting {project.name} data: {e}')
        return None


def get_language_percentages(project: Project) -> Dict[str, float]:
    percentages = project.languages()
    return percentages


if __name__ == '__main__':
    settings = Settings()
    gl = gitlab.Gitlab(settings.gitlab_url, private_token=settings.access_token)
    projects = gl.projects.list(all=True)
    grouped_projects = {}
    for project in projects:
        group_name = project.namespace['name']
        if group_name not in grouped_projects:
            grouped_projects[group_name] = []

    with ProcessPoolExecutor(max_workers=4) as executor:  # Adjust max_workers as needed
        future_to_project = {executor.submit(process_project, project): project for project in projects}
        for future in as_completed(future_to_project):
            project = future_to_project[future]
            try:
                project_data = future.result()
                if project_data:
                    # Process the data (e.g., append it to a DataFrame or list)
                    grouped_projects[project_data['Group Name']].append(project_data)
            except Exception as e:
                logger.error(f'Error processing project {project.name}: {e}')

    with pd.ExcelWriter('./gitlab_projects.xlsx') as writer:
        for sheet_name, records in grouped_projects.items():
            df = pd.DataFrame(records)
            df.to_excel(writer, sheet_name=sheet_name, index=False)


