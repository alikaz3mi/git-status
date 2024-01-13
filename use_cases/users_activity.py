import gitlab
from datetime import datetime
from tqdm import tqdm

def get_user_activity(settings):
    gl = gitlab.Gitlab(settings.gitlab_url, private_token=settings.access_token)
    projects = gl.projects.list(all=True)

    user_commit_dates = {}

    for project in tqdm(projects):
        for commit in project.commits.list(all=True):
            author_email = commit.author_email
            commit_date = datetime.strptime(commit.created_at.split('T')[0], '%Y-%m-%d')

            if author_email not in user_commit_dates:
                user_commit_dates[author_email] = {'first': commit_date, 'last': commit_date}
            else:
                if commit_date < user_commit_dates[author_email]['first']:
                    user_commit_dates[author_email]['first'] = commit_date
                if commit_date > user_commit_dates[author_email]['last']:
                    user_commit_dates[author_email]['last'] = commit_date

    for user, dates in user_commit_dates.items():
        print(f'User: {user}, First Commit: {dates["first"]}, Last Commit: {dates["last"]}')
        
if __name__ == '__main__':
    from config import Settings
    settings = Settings()
    get_user_activity(settings)