from flask import Flask, request
app = Flask(__name__)


def shutdown_server():
        # func = request.environ.get('werkzeug.server.shutdown')
        # if func is None:
        #         raise RuntimeError('Not running with the Werkzeug Server')
        # func()
        return True

@app.route('/')
def authorize():
        #print(request.args['oauth_verifier'])
        print(request)
        shutdown_server()
        return "Thank you, you can close the tab"

@app.route('/test')
def test():
        return "Hello!"

if __name__ == "__main__":
    app.run(debug=True)
