#!/usr/bin/env python2
# Converts PNG to Linux font character array.

import sys
# Python Imaging Library
# http://www.pythonware.com/products/pil/
import Image

def getCellSize(image):
	x, y = image.size
	width = (x / 32) - 1
	height = (y / 8) - 1
	assert 32 * (width + 1) + 1 == x, x
	assert 8 * (height + 1) + 1 == y, y
	return width, height

def createData(width, height, image):
	data = []

	# Scan characters.
	for c in xrange(256):
		row, col = divmod(c, 32)
		y = 1 + row * (height + 1)
		for i in xrange(height):
			x = 1 + col * (width + 1)
			pat = 0
			mask = 128
			for bit in xrange(width):
				if image.getpixel((x, y)):
					pat |= mask
				mask >>= 1
				x += 1
			y += 1
			data.append(pat)

	return data

if len(sys.argv) != 2:
	print >>sys.stderr, 'Usage: python png2font.py <image_file>'
	sys.exit(2)
else:
	fileName = sys.argv[1]
	assert fileName.endswith('.png')
	outFileName = fileName[ : -4] + '.c'

image = Image.open(fileName)
width, height = getCellSize(image)
data = createData(width, height, image)
arrayName = 'fontdata_%dx%d' % (width, height)

out = open(outFileName, 'w')
try:
	print >>out, '#include <linux/font.h>'
	print >>out
#	print >>out, '#define FONTDATAMAX (%d*256)' % height
#	print >>out
	print >>out, 'static const unsigned char %s[] = {' % arrayName
	print >>out
	for c in xrange(256):
		if c < 32:
			cs = '^%s' % chr(c + 64)
		elif c >= 128:
			cs = '\\%o' % c
		else:
			cs = chr(c)
		print >>out, "\t/* %d 0x%02X '%s' */" % (c, c, cs)
		for i in xrange(c * height, (c + 1) * height):
			d = data[i]
			ds = ''.join(
				str((d >> bit) & 1)
				for bit in reversed(xrange(8))
				)
			print >>out, '\t0x%02X, /* %s */' % (d, ds)
		print >>out
	print >>out, '};'
	print >>out
	print >>out, 'const struct font_desc font_%dx%d = {' \
			% (width, height)
	print >>out, '\t.idx\t= FONT%dx%d_IDX,' % (width, height)
	print >>out, '\t.name\t= "%dx%d",' % (width, height)
	print >>out, '\t.width\t= %d,' % width
	print >>out, '\t.height\t= %d,' % height
	print >>out, '\t.data\t= %s,' % arrayName
	print >>out, '\t.pref\t= 0,'
	print >>out, '};'
finally:
	out.close()
