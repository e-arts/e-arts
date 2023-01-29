from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Prerelease v0.0.4-alpha"


if __name__ == "__main__":
    port = 3000
    app.run(host="0.0.0.0", port=port)
