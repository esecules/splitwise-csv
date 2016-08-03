#! /usr/bin/python
from flask import Flask, request
app = Flask(__name__)


def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
        func()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def authorize( path ):
        print request.args['oauth_verifier']
        shutdown_server()
        return "Thank you, you can close the tab"

if __name__ == "__main__":
    app.run()
