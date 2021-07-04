from flask import Flask, Response, render_template, abort, request
from urllib.parse import urlparse
import requests

import watermarks
from watermarks import WatermarkType, TextPosition

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    params = {
        "type": WatermarkType.TEXT.value,
        "position": TextPosition.CENTER.value,
        "size_ratio": 0.8,
        "alpha": 0.5,
    }

    if request.method == "POST":
        try:
            params["type"] = WatermarkType(request.form.get("type")).value
        except ValueError:
            pass

        if request.form.get("content"):
            params["content"] = str(request.form.get("content"))

        try:
            pos = TextPosition(request.form.get("position")).value
            params["position"] = pos
        except ValueError:
            pass

        try:
            params["size_ratio"] = float(request.form.get("size_ratio"))
        except ValueError:
            pass

        try:
            params["alpha"] = float(request.form.get("alpha"))
        except ValueError:
            pass

    return render_template(
        "index.jinja",
        params=params,
        TextPosition=TextPosition
    )

@app.route("/watermark/text/<file_name>", methods=["GET"])
def watermark_text(file_name):
    image_url = urlparse(request.args.get("url"))
    if not image_url.geturl():
        return abort(400)

    text = request.args.get(
        "content",
        request.headers.get("Referer", image_url.hostname),
    )
    size_ratio = float(request.args.get("size_ratio", 0.8))
    alpha = float(request.args.get("alpha", 0.5))

    position = request.args.get("position")
    try:
        position = TextPosition(position)
    except ValueError:
        position = TextPosition.CENTER

    image_request = requests.get(image_url.geturl())
    image = watermarks.one_text(
        bstring=image_request.content,
        text=text,
        position=position,
        size_ratio=size_ratio,
        alpha=alpha,
    )
    return Response(image, mimetype="image/png")