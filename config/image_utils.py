from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def optimize_image_field(instance, field_name, max_size=(1600, 1600), quality=82):
    image_field = getattr(instance, field_name, None)
    if not image_field or not image_field.name:
        return

    if getattr(image_field, '_committed', True):
        return

    try:
        image_field.file.seek(0)
        image = Image.open(image_field.file)
        image = ImageOps.exif_transpose(image)
    except Exception:
        return

    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    if image.mode in ('RGBA', 'LA') or (
        image.mode == 'P' and 'transparency' in image.info
    ):
        image = image.convert('RGBA')
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel('A'))
        image = background
    else:
        image = image.convert('RGB')

    output = BytesIO()
    image.save(output, format='WEBP', quality=quality, method=6)
    output.seek(0)

    original_name = Path(image_field.name)
    optimized_name = f'{original_name.stem}.webp'
    image_field.save(optimized_name, ContentFile(output.read()), save=False)
