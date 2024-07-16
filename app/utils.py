from uuid import uuid4


def generate_image_url(name, ext):
    return f"static/images/{uuid4()}_{name}.{ext}"


def save_image(image_data):
    name: str = image_data.filename
    name, ext = name.rsplit('.', maxsplit=1)
    image_path = generate_image_url(name, ext)
    image_url = f"app/{image_path}"
    image_data.save(image_url)
    return image_path
