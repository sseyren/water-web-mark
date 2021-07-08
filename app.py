from flask import Flask, Response, render_template, abort, request
from urllib.parse import urlparse, urlencode, unquote
from pathlib import Path
import requests

import watermarks
from watermarks import WatermarkType, TextPosition

app = Flask(__name__)
app.jinja_env.filters['unquote'] = unquote

def generate_embed_js(watermark_type:WatermarkType, hostname:str, params:dict):
    template = app.jinja_env.get_template("js_code.jinja")

    return template.render(
        hostname=hostname,
        endpoint=f"/watermark/{watermark_type.value}",
        query=urlencode(params),
    )

@app.route("/", methods=["GET"])
def index():
    return render_template("index.jinja")

@app.route("/code-gen", methods=["GET", "POST"])
def code_generator():
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
        except:
            pass

        if request.form.get("content"):
            params["content"] = str(request.form.get("content"))

        try:
            pos = TextPosition(request.form.get("position")).value
            params["position"] = pos
        except:
            pass

        try:
            params["size_ratio"] = float(request.form.get("size_ratio"))
        except:
            pass

        try:
            params["alpha"] = float(request.form.get("alpha"))
        except:
            pass

        generated_code = generate_embed_js(
            watermark_type, request.host_url[0:-1], params)

    return render_template(
        "code_generator.jinja",
        watermark_type=watermark_type.value,
        params=params,
        generated_code=generated_code,
        TextPosition=TextPosition
    )

@app.route("/watermark/<type_path>/<file_name>", methods=["GET"])
def watermark(type_path, file_name):
    try:
        watermark_type = WatermarkType(type_path)
    except:
        return abort(404)

    image_url = urlparse(request.args.get("url"))
    if not image_url.geturl():
        return abort(400)

    try:
        size_ratio = float(request.args.get("size_ratio"))
    except:
        size_ratio = 0.8

    try:
        alpha = float(request.args.get("alpha"))
    except:
        alpha = 0.5

    position = request.args.get("position")
    try:
        position = TextPosition(position)
    except:
        position = TextPosition.CENTER

    image_request = requests.get(image_url.geturl())
    if image_request.status_code != requests.codes.ok:
        return abort(400)

    if watermark_type == WatermarkType.TEXT:
        text = request.args.get(
            "content",
            request.headers.get("Referer", image_url.hostname),
        )
        image = watermarks.one_text(
            bstring=image_request.content,
            text=text,
            position=position,
            size_ratio=size_ratio,
            alpha=alpha,
        )
    elif watermark_type == WatermarkType.IMAGE:
        watermark_url = urlparse(request.args.get("content"))
        if not watermark_url.geturl():
            return abort(400)

        watermark_request = requests.get(watermark_url.geturl())
        if watermark_request.status_code != requests.codes.ok:
            return abort(400)

        image = watermarks.one_image(
            image_bstr=image_request.content,
            watermark_bstr=watermark_request.content,
            position=position,
            size_ratio=size_ratio,
            alpha=alpha,
        )

    return Response(image, mimetype="image/png")


@app.route("/docs", methods=["GET"])
def documentation():
    return render_template('docs.jinja', TextPosition=TextPosition)

DEMO_PATH = Path.cwd() / "templates" / "demo"
DEMO_NAMES = [f.name.split(".")[0] for f in DEMO_PATH.iterdir() if f.is_file()]

@app.route("/demo/<page>", methods=["GET", "POST"])
def demo_page(page):
    if page in DEMO_NAMES:
        return render_template(f"demo/{page}.jinja")
    else:
        return abort(404)