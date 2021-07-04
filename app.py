from flask import Flask, Response, render_template, abort, request
from urllib.parse import urlparse
import requests

import watermarks

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "selam"

@app.route("/watermark/text/<file_name>", methods=["GET"])
def show_user_profile(file_name):
    image_url = urlparse(request.args.get("url"))
    if not image_url.geturl():
        return abort(400)

    text = request.args.get(
        "text",
        request.headers.get("Referer", image_url.hostname),
    )
    size_ratio = float(request.args.get("size_ratio", 0.8))
    alpha = float(request.args.get("alpha", 0.5))

    position = request.args.get("position")
    try:
        position = watermarks.TextPosition(position)
    except ValueError:
        position = watermarks.TextPosition.CENTER

    image_request = requests.get(image_url.geturl())
    image = watermarks.one_text(
        bstring=image_request.content,
        text=text,
        position=position,
        size_ratio=size_ratio,
        alpha=alpha,
    )
    return Response(image, mimetype="image/png")