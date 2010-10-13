#!/usr/bin/env python
#
# This tool depends on the "pygame" package.
#
# The Ben NanoNote has a "delta" arrangement of the pixels on its LCD:
#
# even rows:  R G B|R G B|..
# odd rows:  G B R|G B R|..
#
# Note that the odd-numbered rows are shifted 1/6th of pixel width left.
#
# A white pixel at (0,1) will appear shifted 1/6th of a pixel left relative to
# a white pixel at (0,0) resulting in jaggies on vertical lines.
#
# This tool processes a sheet of 8x8 font glyphs into a sheet of 4x8 font
# glyphs using individual green and magenta "pixels" to achieve twice the
# horizontal resolution.  It also compensates for the unusual screen on the
# NanoNote.
#
# NOTE: On the even rows, a single pixel is discarded that would have been made
# up of the red component of the first column along with the blue component of
# the last column.  On odds rows, the green component of the first column is
# discarded.  This means that last column of the source image is ignored.
#
# Example usage:
#
#  tools/un-fuzzy.py  fonts/pre-4x8-font.png  /tmp/un-fuzzy-4x8-font.tga
#
# Then use GIMP to convert the .tga file to a .pnm file.  Imagemagick seems to
# create P3 .pnm files yet setfont2 can only load P6 .pnm files presently.
#

import sys
import pygame


# Check and grab the command line arguments
if len( sys.argv) < 3:
  print "Use: %s  source-image-file  target-image-file(BMP|TGA) [grid]" % sys.argv[0]
  sys.exit( 1)

path_to_source_file = sys.argv[ 1]
path_to_target_file = sys.argv[ 2]
grid = ( 4 == len( sys.argv))

# Load the source image and create the target image with the same number of
# rows but half the number of columns
source_image = pygame.image.load( path_to_source_file)
target_image = pygame.Surface( (source_image.get_width()/2, source_image.get_height()))


class Colour:
  def __init__( self):
    self.red   = 0
    self.green = 0
    self.blue  = 0

  def isnt_black( self):
    return self.red != 0 or self.green != 0 or self.blue != 0

  def __repr__( self):
    return "(%i,%i,%i)" % ( self.red, self.green, self.blue)


def update_pixel( self, location, colour):
  current_state = list( self.get_at( location))
  # NOTE that the new luminances are logical-ORed with the current state of
  # the pixels since no component should be added to twice, which means that
  # no overflow of component values should be possible
  current_state[ 0] |= colour.red
  current_state[ 1] |= colour.green
  current_state[ 2] |= colour.blue
  self.set_at( location, current_state)


for row in range( source_image.get_height()):
  for column in range( source_image.get_width() - 1):
    pixel = source_image.get_at( (column, row))
    # "pixel" should be monochrome
    red   = pixel[ 0]
    green = pixel[ 1]
    blue  = pixel[ 2]
    if red != green or green != blue:
      raise Exception("not monochrome at (%i,%i)"%( column, row))

    luminance = red

    # The pixel at ( x, y) in the target image encodes two virtual pixels: one
    # from the green component and one from the magenta component made by
    # combining the blue component and the red component of the pixel
    # immediately to the right of this pixel
    # For odd-numbered rows the virtual pixels are:
    #  1) magenta made from blue and red
    #  2) the green component of the pixel to the right

    # The luminance of the pixel at ( x, y) in the source image is encoded in
    # different ways depending whether the row is odd or even-numbered and
    # whether the column is odd or even-numbered

    left  = Colour()
    right = Colour()

    # If preparing SubLCD for a grid-based LCD rather than a Delta LCD..
    if grid:
      if 0 == column & 1:
        # The luminance of this pixel is provided by the green component of the
        # pixel at ( x, y)
        left.green = luminance
      else:
        # The luminance of this pixel is provided by the magenta component that
        # is distributed across two pixels ( the blue component of the pixel at
        # ( x, y) and the red component of the pixel at ( x+1, y))
        left.blue = luminance
        right.red = luminance
    else:
      # If this row is even-numbered..
      if 0 == row & 1:
        # If this column is even-numbered..
        if 0 == column & 1:
          # The luminance of this pixel is provided by the green component of the
          # pixel at ( x, y)
          left.green = luminance
        else:
          # The luminance of this pixel is provided by the magenta component that
          # is distributed across two pixels ( the blue component of the pixel at
          # ( x, y) and the red component of the pixel at ( x+1, y))
          left.blue = luminance
          right.red = luminance
      else:
        if 0 == column & 1:
          # The luminance of this pixel is provided by the magenta component (
          # the sum of the red and blue components) of the pixel at ( x, y)
          left.red = luminance
          left.blue = luminance
        else:
          # The luminance of this pixel is provided by the green component of the
          # pixel at ( x+1, y)
          right.green = luminance
    update_pixel( target_image, (column/2,row), left)
    #print repr((column,row))
    #print "L"+repr(left)
    #print "R"+repr(right)
    if right.isnt_black():
      update_pixel( target_image, (column/2+1,row), right)

pygame.image.save( target_image, path_to_target_file)

