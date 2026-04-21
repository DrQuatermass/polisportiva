from io import BytesIO

from django.contrib.staticfiles import finders
from django.http import HttpResponse
from PIL import Image, ImageOps


SOCIAL_IMAGE_SIZE = (1200, 630)
FALLBACK_SOCIAL_IMAGE = 'images/POL_SANMARINESE.png'


def _open_source_image(image_field):
    if image_field and image_field.name:
        try:
            return Image.open(image_field.path)
        except Exception:
            pass

    fallback_path = finders.find(FALLBACK_SOCIAL_IMAGE)
    if fallback_path:
        return Image.open(fallback_path)

    raise FileNotFoundError(FALLBACK_SOCIAL_IMAGE)


def social_image_response(image_field):
    image = ImageOps.exif_transpose(_open_source_image(image_field)).convert('RGB')
    image.thumbnail(SOCIAL_IMAGE_SIZE, Image.Resampling.LANCZOS)

    canvas = Image.new('RGB', SOCIAL_IMAGE_SIZE, (255, 255, 255))
    x = (SOCIAL_IMAGE_SIZE[0] - image.width) // 2
    y = (SOCIAL_IMAGE_SIZE[1] - image.height) // 2
    canvas.paste(image, (x, y))

    output = BytesIO()
    canvas.save(output, format='JPEG', quality=88, optimize=True)

    response = HttpResponse(output.getvalue(), content_type='image/jpeg')
    response['Cache-Control'] = 'public, max-age=86400'
    return response
