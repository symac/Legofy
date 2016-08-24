from __future__ import unicode_literals

from PIL import Image, ImageSequence
import sys
import os

# Python 2 and 3 support
# TODO: Proper images2gif version that supports both Py 2 and Py 3 (mostly handling binary data)
if sys.version_info < (3,):
    import legofy.images2gif_py2 as images2gif
else:
    import legofy.images2gif_py3 as images2gif
from legofy import palettes


def apply_color_overlay(image, color):
    '''Small function to apply an effect over an entire image'''
    overlay_red, overlay_green, overlay_blue = color
    channels = image.split()

    r = channels[0].point(lambda color: overlay_effect(color, overlay_red))
    g = channels[1].point(lambda color: overlay_effect(color, overlay_green))
    b = channels[2].point(lambda color: overlay_effect(color, overlay_blue))


    channels[0].paste(r)
    channels[1].paste(g)
    channels[2].paste(b)

    return Image.merge(image.mode, channels)

def overlay_effect(color, overlay):
    '''Actual overlay effect function'''
    if color < 33:
        return overlay - 100
    elif color > 233:
        return overlay + 100
    else:
        return overlay - 133 + color

def checkAdjacentPixels(color_matrix, brick_x, brick_y, brick_w, brick_h, currentColor):
    for processX in range(brick_w):
        for processY in range(brick_h):
            # print "%s %s / %s vs. %s" % (brick_x + processX, brick_y + processY, color_matrix[processX][processY], currentColor)
            try:
                if color_matrix[brick_x + processX][brick_y + processY] != currentColor:
                    return False
            except:
                return False
    return True

def make_lego_image(thumbnail_image, brick_image, minimize_bricks_number):
    '''Create a lego version of an image from an image'''
    base_width, base_height = thumbnail_image.size
    one_stud_brick_width, one_stud_brick_height = brick_image.size

    rgb_image = thumbnail_image.convert('RGB')

    lego_image = Image.new("RGB", (base_width * one_stud_brick_width,
                                   base_height * one_stud_brick_height), "white")

    # we define the bricks we can use, just 1x1 by default, others if the user wants
    if minimize_bricks_number:
        bricks_by_size = [
            [4,2],
            [2,4],
            [2,2],
            [4,1],
            [1,4],
            [2,1],
            [1,2],
            [1,1],
        ]
    else:
        bricks_by_size = [
            [1,1],
        ]

    # We create the color matrix once, will be used afterwards to group bricks
    color_matrix = []
    for brick_x in range(base_width):
        column_matrix = []
        for brick_y in range(base_height):
            color = rgb_image.getpixel((brick_x, brick_y))
            column_matrix.append(color)
        color_matrix.append(column_matrix)

    # We then run the "brickification"
    for brick in bricks_by_size:
        brick_w = brick[0]
        brick_h = brick[1]
        print "Testing brick %sx%s.png" % (brick_w, brick_h)

        brick_path = os.path.join(os.path.dirname(__file__), "assets",
                          "bricks", "%sx%s.png" % (brick_w, brick_h))
        if not os.path.isfile(brick_path):
            print('Brick asset "{0}" was not found.'.format(brick_path))
            sys.exit(1)
        brick_image = Image.open(brick_path)

        for brick_x in range(base_width):
            for brick_y in range(base_height):
                # print brick_x, brick_y
                currentColor = color_matrix[brick_x][brick_y]

                if currentColor != None:
                    sameColor = checkAdjacentPixels(color_matrix, brick_x, brick_y, brick_w, brick_h, currentColor)
                    if sameColor == True:
                        # print "\t%s %s matching" % (brick_x, brick_y)
                        lego_image.paste(apply_color_overlay(brick_image, currentColor),
                                 (brick_x * one_stud_brick_width, brick_y * one_stud_brick_height))

                        for processX in range(brick_w):
                            for processY in range(brick_h):
                                clearX = brick_x + processX
                                clearY = brick_y + processY

                                # print "\t\tSetting %s,%s to None" % (clearX, clearY)
                                color_matrix[clearX][clearY] = None
                    else:
                        # print "\t%s %s not matching" % (brick_x, brick_y)
                        pass
    return lego_image


def get_new_filename(file_path, ext_override=None):
    '''Returns the save destination file path'''
    folder, basename = os.path.split(file_path)
    base, extention = os.path.splitext(basename)
    if ext_override:
        extention = ext_override
    new_filename = os.path.join(folder, "{0}_lego{1}".format(base, extention))
    return new_filename


def get_new_size(base_image, brick_image, size=None):
    '''Returns a new size the first image should be so that the second one fits neatly in the longest axis'''
    new_size = base_image.size
    if size:
        scale_x, scale_y = size, size
    else:
        scale_x, scale_y = brick_image.size

    if new_size[0] > scale_x or new_size[1] > scale_y:
        if new_size[0] < new_size[1]:
            scale = new_size[1] / scale_y
        else:
            scale = new_size[0] / scale_x

        new_size = (int(round(new_size[0] / scale)) or 1,
                    int(round(new_size[1] / scale)) or 1)

    return new_size

def get_lego_palette(palette_mode):
    '''Gets the palette for the specified lego palette mode'''
    legos = palettes.legos()
    palette = legos[palette_mode]
    return palettes.extend_palette(palette)


def apply_thumbnail_effects(image, palette, dither):
    '''Apply effects on the reduced image before Legofying'''
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette)
    return image.im.convert("P",
                        Image.FLOYDSTEINBERG if dither else Image.NONE,
                        palette_image.im)

def legofy_gif(base_image, brick_image, output_path, size, palette_mode, dither):
    '''Alternative function that legofies animated gifs, makes use of images2gif - uses numpy!'''
    im = base_image

    # Read original image duration
    original_duration = im.info['duration']

    # Split image into single frames
    frames = [frame.copy() for frame in ImageSequence.Iterator(im)]

    # Create container for converted images
    frames_converted = []

    print("Number of frames to convert: " + str(len(frames)))

    # Iterate through single frames
    for i, frame in enumerate(frames, 1):
        print("Converting frame number " + str(i))

        new_size = get_new_size(frame, brick_image, size)
        frame.thumbnail(new_size, Image.ANTIALIAS)
        if palette_mode:
            palette = get_lego_palette(palette_mode)
            frame = apply_thumbnail_effects(frame, palette, dither)
        new_frame = make_lego_image(frame, brick_image)
        frames_converted.append(new_frame)

    # Make use of images to gif function
    images2gif.writeGif(output_path, frames_converted, duration=original_duration/1000.0, dither=0, subRectangles=False)

def legofy_image(base_image, brick_image, output_path, size, palette_mode, dither, minimize_bricks_number):
    '''Legofy an image'''
    new_size = get_new_size(base_image, brick_image, size)
    base_image.thumbnail(new_size, Image.ANTIALIAS)
    if palette_mode:
        palette = get_lego_palette(palette_mode)
        base_image = apply_thumbnail_effects(base_image, palette, dither)
    make_lego_image(base_image, brick_image, minimize_bricks_number).save(output_path)


def main(image_path, output_path=None, size=None,
         palette_mode=None, dither=False, minimize_bricks_number=False):
    '''Legofy image or gif with brick_path mask'''
    image_path = os.path.realpath(image_path)
    if not os.path.isfile(image_path):
        print('Image file "{0}" was not found.'.format(image_path))
        sys.exit(1)

    brick_path = os.path.join(os.path.dirname(__file__), "assets",
                              "bricks", "1x1.png")

    if not os.path.isfile(brick_path):
        print('Brick asset "{0}" was not found.'.format(brick_path))
        sys.exit(1)

    base_image = Image.open(image_path)
    brick_image = Image.open(brick_path)

    if palette_mode:
        print ("LEGO Palette {0} selected...".format(palette_mode.title()))
    elif dither:
        palette_mode = 'all'

    if image_path.lower().endswith(".gif") and base_image.is_animated:
        if output_path is None:
            output_path = get_new_filename(image_path)
        print("Animated gif detected, will now legofy to {0}".format(output_path))
        legofy_gif(base_image, brick_image, output_path, size, palette_mode, dither)
    else:
        if output_path is None:
            output_path = get_new_filename(image_path, '.png')
        print("Static image detected, will now legofy to {0}".format(output_path))
        legofy_image(base_image, brick_image, output_path, size, palette_mode, dither, minimize_bricks_number)

    base_image.close()
    brick_image.close()
    print("Finished!")
