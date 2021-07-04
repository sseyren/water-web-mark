from flask import Flask, Response, render_template, abort, request
from urllib.parse import urlparse, urlencode
import requests

import watermarks
from watermarks import WatermarkType, TextPosition

app = Flask(__name__)

def generate_embed_js(watermark_type:WatermarkType, hostname:str, params:dict):
    template = app.jinja_env.get_template("js_code.jinja")

    return template.render(
        hostname=hostname,
        endpoint=f"/watermark/{watermark_type.value}",
        query=urlencode(params),
    )

@app.route("/", methods=["GET", "POST"])
def index():
    watermark_type = WatermarkType.TEXT
    params = {
        "position": TextPosition.CENTER.value,
        "size_ratio": 0.8,
        "alpha": 0.5,
    }
    generated_code = None

    if request.method == "POST":
        try:
            watermark_type = WatermarkType(request.form.get("type"))
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

        generated_code = generate_embed_js(
            watermark_type, request.host_url[0:-1], params)

    return render_template(
        "index.jinja",
        watermark_type=watermark_type.value,
        params=params,
        generated_code=generated_code,
        TextPosition=TextPosition
    )

@app.route(
    f"/watermark/{WatermarkType.TEXT.value}/<file_name>",
    methods=["GET"]
)
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