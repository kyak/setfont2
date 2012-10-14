#!/usr/bin/env python2
# Converts Linux font character array to PNG.

import sys
# Python Imaging Library
# http://www.pythonware.com/products/pil/
import Image

def readSource(inp):
	data = []
	meta = {}
	inData = False
	inMeta = False
	for line in inp.readlines():
		csta = line.find('/*')
		if csta != -1:
			cend = line.index('*/') + 2
			line = line[ : csta] +  line[cend : ]
		line = line.strip()
		if inData:
			if line == '};':
				inData = False
			elif line:
				valStr = line.rstrip(',')
				# Chars wider than 8 not supported yet.
				assert ',' not in valStr
				data.append(int(valStr, 16))
		elif inMeta:
			if line == '};':
				inMeta = False
			elif line:
				key, value = line.split('=')
				key = key.strip().lstrip('.')
				value = value.strip().rstrip(',')
				meta[key] = value
		elif line.startswith('static const unsigned char'):
			assert line[-1] == '{'
			inData = True
		elif line.startswith('const struct font_desc'):
			assert line[-1] == '{'
			inMeta = True
	return data, meta

def createImage(width, height, data):
	assert len(data) == height * 256

	# Reserve space for a 32 * 8 grid of characters.
	image = Image.new('P', (32 * (width + 1) + 1, 8 * (height + 1) + 1))
	palette = [0, 0, 0] * 256
	palette[3 : 6] = [255, 255, 255] # foreground
	palette[6 : 9] = [128, 0, 0] # grid
	image.putpalette(palette)

	# Draw grid.
	for y in xrange(0, image.size[1], height + 1):
		for x in xrange(0, image.size[0]):
			image.putpixel((x, y), 2)
	for x in xrange(0, image.size[0], width + 1):
		for y in xrange(0, image.size[1]):
			image.putpixel((x, y), 2)

	# Draw characters.
	for c in xrange(256):
		row, col = divmod(c, 32)
		y = 1 + row * (height + 1)
		for i in xrange(c * height, (c + 1) * height):
			x = 1 + col * (width + 1)
			pat = data[i]
			for bit in xrange(width):
				if pat & 128:
					image.putpixel((x, y), 1)
				pat <<= 1
				x += 1
			y += 1
	return image

if len(sys.argv) != 2:
	print >>sys.stderr, 'Usage: python font2png.py <source_file>'
	sys.exit(2)
else:
	fileName = sys.argv[1]
	assert fileName.endswith('.c')
	outFileName = fileName[ : -2] + '.png'

inp = open(fileName, 'r')
try:
	data, meta = readSource(inp)
finally:
	inp.close()
width = int(meta['width'])
height = int(meta['height'])
image = createImage(width, height, data)
image.save(outFileName)
