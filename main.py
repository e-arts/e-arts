from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello World!"


if __name__ == "__main__":
    port = 5001
    app.run(host="0.0.0.0", port=port)
