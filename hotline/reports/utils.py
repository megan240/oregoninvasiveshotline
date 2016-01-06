import logging
import os

from PIL import Image, ImageDraw, ImageFilter


log = logging.getLogger(__name__)


def generate_icon(output_path,
                  inner_icon=None,
                  color='#999',
                  generated_icon_size=(30, 45),
                  square_coords=((0, 0), (30, 30)),
                  triangle_coords=((10, 30), (15, 45), (20, 30)),
                  icon_offset=(0, -10),
                  transparent=(0, 0, 0, 0),
                  outline_color=(10, 10, 10, 255)):
    """Generate a map-style icon.

    In general usage, this is only used by the `Report` model, but this
    detached implementation will allow us to more-easily test icon
    generation in the shell or in unit tests.

    These icons are displayed on the map to show `Report` locations and
    also in `Report` list views.

    If an ``inner_icon`` is specified, it will be placed in the center
    of the main icon.

    Icons look something like this, where $$ represents the inner icon::

         ____
        |    |
        | $$ |
        |_  _|
          \/

    They are constructed in the following way:

    - A transparent canvas is created to hold the icon
    - A square is placed in the canvas so that it's aligned with the top
    - An inverted triangle is placed directly under the square to
      complete the background
    - The outline of the two shapes is extracted and converted to the
      correct color
    - The inner icon image is pasted in the center of a transparent
      canvas (assuming ``inner_icon`` was passed)
    - The canvas is pasted in the middle of the background
    - Tinally, the outline is merged on top of the background

    """
    # Define the color mode (because the mode has to be the same in
    # order to merge images).
    mode = 'RGBA'

    # Create a new, transparent image as a canvas.
    canvas = Image.new(mode, generated_icon_size, transparent)

    # Draw the background onto the canvas.
    background = ImageDraw.Draw(canvas)
    background.rectangle(square_coords, fill=color)
    background.polygon(triangle_coords, fill=color)

    # Filter out the edges of the background and add a nice dark outline
    # to it by traversing pixel by pixel.
    outline = canvas.filter(ImageFilter.FIND_EDGES)
    outline_width, outline_height = outline.size
    outline_pixels = outline.load()
    for i in range(outline_width):
        for j in range(outline_height):
            if outline_pixels[i, j] != transparent:
                # Since our canvas is transparent, any pixel that isn't
                # transparent is guaranteed to be an edge and should
                # have its color changed to the outline color.
                outline_pixels[i, j] = outline_color

    if inner_icon and os.path.exists(inner_icon.path):
        # Before we can use the inner icon, it needs to be pasted into
        # an image with the same properties as the background image.
        # Otherwise, transparency will not be preserved. To do this, we
        # simply create a new image with the same properties as the
        # canvas, and paste the icon into it.
        inner_icon = Image.open(inner_icon.path)
        inner_icon_canvas = Image.new(mode, generated_icon_size)
        inner_icon_canvas.paste(inner_icon, icon_offset)

        # Alpha composite merge is used to ensure transparency is
        # preserved while moving the icon onto the canvas.
        img = Image.alpha_composite(canvas, inner_icon_canvas)
    else:
        img = canvas

    # Now merge the image with the outline.
    img = Image.alpha_composite(img, outline)

    try:
        img.save(output_path)
    except IOError:
        log.exception('Error while saving icon image')