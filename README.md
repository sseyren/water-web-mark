# water-web-mark

Görsellere filigran (watermark) uygulayan bir web uygulamasıdır.
Görselin üstüne saydam yazı ve başka bir görsel ekler.
Görsellerin URL adreslerini (ve bazı ek parametreleri) alır, bunları kullanarak
yeni görsel üretir.

[OpenCV](https://opencv.org) ve [Flask](https://flask.palletsprojects.com)
kullanılarak yapılmıştır.

## Canlı Demo: <https://water-web-mark.herokuapp.com>

Kurulum yapmadan web servisine erişebilirsiniz.

## Kurulum

Bağımlılıkları kurun:
```sh
pip install -r requirements.txt
```

Flask uygulamasını başlatın:
```sh
FLASK_ENV=development flask run
```

Tarayıcınızdan <http://localhost:5000> adresini ziyaret edin.