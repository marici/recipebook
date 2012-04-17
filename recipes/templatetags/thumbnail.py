import os
import Image
from django.template import Library

register = Library()
thumb_dir = 'thumb'


def thumbnail(file, size='104x104'):
    # defining the size
    x, y = [int(x) for x in size.split('x')]
    # defining the filename and the miniature filename
    filehead, filetail = os.path.split(file.path)
    basename, format = os.path.splitext(filetail)
    miniature = basename + '_' + size + format
    filename = file.path
    if not os.path.exists(filename):
        return file.url
    miniature_filebase = os.path.join(filehead, thumb_dir)
    if not os.path.exists(miniature_filebase):
        os.makedirs(miniature_filebase)
    miniature_filename = os.path.join(filehead, thumb_dir, miniature)
    filehead, filetail = os.path.split(file.url)
    miniature_url = filehead + '/' + thumb_dir + '/' + miniature
    if (os.path.exists(miniature_filename) and
            os.path.getmtime(filename) > os.path.getmtime(miniature_filename)):
        os.unlink(miniature_filename)
    # if the image wasn't already resized, resize it
    if not os.path.exists(miniature_filename):
        image = Image.open(filename)
        image.thumbnail([x, y], Image.ANTIALIAS)
        try:
            image.save(miniature_filename, image.format, quality=90,
                    optimize=1)
        except:
            image.save(miniature_filename, image.format, quality=90)

    return miniature_url

register.filter(thumbnail)
