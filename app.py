import subprocess
from flask import (
    Flask,
    request,
    g,
    session, redirect, url_for,
    render_template_string,
    jsonify
)
from flask.ext.github import (
    GitHub,
    GitHubError
)

SECRET_KEY = 'development key'
DEBUG = True

GITHUB_CLIENT_ID = '9b818f868e6191cf674e'
GITHUB_CLIENT_SECRET = '0423ed3a012ac8e50e9bd5d54c78b70ab9dc4000'
GITHUB_CALLBACK_URL = 'http://localhost:5000/github-callback'


app = Flask(__name__, static_url_path='', static_folder='')
app.config.from_object(__name__)
github = GitHub(app)

bashCommand = "git --git-dir=/{repository_path}/.git --work-tree=/{repository_path} log --format='%ai|%an'"


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = session['user_id']


@app.route('/')
def index():
    if g.user:
        t = 'Hello! <a href="{{ url_for("user") }}">Get user</a> ' \
            '<a href="{{ url_for("logout") }}">Logout</a>'
    else:
        t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'

    return render_template_string(t)


@app.route('/explore')
def explore():
    return app.send_static_file('index.html')


@app.route("/data/<path:repository_path>")
def data(repository_path):
    process = subprocess.Popen(bashCommand.format(repository_path=repository_path).split(), stdout=subprocess.PIPE)
    (output, error) = process.communicate()

    if output == '':
        return ('An error has occured', 500)
    elif error is None:
        return '\n'.join([x[1:-1] for x in output.split('\n')])
    else:
        return (error, 500, [])


@app.route('/login')
def login():
    return github.authorize()


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get('next') or url_for('index')
    if oauth_token is None:
        return redirect(next_url)

    user = oauth_token
    session['user_id'] = user
    return redirect(url_for('index'))


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user


@app.route('/user')
def user():
    return str(github.get('user'))


@app.route('/repo/<owner>/<repo>')
def repo(owner, repo):
    # GET /repos/:owner/:repo
    repo_infos = github.get('repos/%s/%s' % (owner, repo))

    # GET /repos/:owner/:repo/stats/contributors
    repo_stats_contributors = github.get('repos/%s/%s/stats/contributors' % (owner, repo))

    # GET /repos/:owner/:repo/stats/commit_activity
    repo_stats_commit_activity = github.get('repos/%s/%s/stats/commit_activity' % (owner, repo))

    # GET /repos/:owner/:repo/stats/code_frequency
    repo_stats_code_frequency = github.get('repos/%s/%s/stats/code_frequency' % (owner, repo))

    # GET /repos/:owner/:repo/stats/participation
    repo_stats_participation = github.get('repos/%s/%s/stats/participation' % (owner, repo))

    # GET /repos/:owner/:repo/stats/punch_card
    repo_stats_punch_card = github.get('repos/%s/%s/stats/punch_card' % (owner, repo))

    return jsonify({
        'infos': repo_infos,
        'stats_contributors': repo_stats_contributors,
        'stats_commit_activity': repo_stats_commit_activity,
        'stats_code_frequency': repo_stats_code_frequency,
        'stats_participation': repo_stats_participation,
        'stats_punch_card': repo_stats_punch_card
    })


@app.route('/commits/<owner>/<repo>')
def commits(owner, repo):
    """
    Must returns commits formated as :
    2013-11-22 22:04:05 +0100|Bertrand TORNIL
    2013-10-21 22:59:38 +0200|Bertrand TORNIL
    2013-10-21 12:05:41 +0200|Bertrand TORNIL

    ... etc.
    """
    # re-implement the github call, to provide pagination
    # links are in the header
    result = []

    response = raw_request('GET', '%srepos/%s/%s/commits' % (github.BASE_URL, owner, repo))
    status_code = str(response.status_code)

    if status_code.startswith('4'):
        raise GitHubError(response)

    assert status_code.startswith('2')

    for commit in response.json():
        result.append(commit['commit']['committer'])
        #{
        #   "name": "Monalisa Octocat",
        #   "email": "support@github.com",
        #   "date": "2011-04-14T16:00:49Z"
        # },

    while hasattr(response, 'links') and 'next' in response.links:
        response = raw_request('GET', response.links['next']['url'])
        status_code = str(response.status_code)
        if status_code.startswith('4'):
            raise GitHubError(response)

        assert status_code.startswith('2')
        for commit in response.json():
            result.append(commit['commit']['committer'])

    return '\n'.join(['%s|%s' % (row['date'], row['name']) for row in result])


def raw_request(method, url, params=None, **kwargs):
    """
    Makes a HTTP request and returns the raw
    :class:`~requests.Response` object.

    """
    if params is None:
        params = {}

    if 'access_token' not in params:
        params['access_token'] = github.get_access_token()

    return github.session.request(
        method, url, params=params, allow_redirects=True, **kwargs)


if __name__ == "__main__":
    app.run(debug=True)
