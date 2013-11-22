import subprocess
from flask import Flask

app = Flask(__name__, static_url_path='', static_folder='')


bashCommand = "git --git-dir=/{repository_path}/.git --work-tree=/{repository_path} log --format='%ai|%an'"


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route("/data/<path:repository_path>")
def main(repository_path):
    process = subprocess.Popen(bashCommand.format(repository_path=repository_path).split(), stdout=subprocess.PIPE)
    (output, error) = process.communicate()

    if output == '':
        return ('An error has occured', 500)
    elif error is None:
        return '\n'.join([x[1:-1] for x in output.split('\n')])
    else:
        return (error, 500, [])


if __name__ == "__main__":
    app.run(debug=True)
