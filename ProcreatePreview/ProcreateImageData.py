import sys
import math
import zipfile
from biplist import readPlist
import os
import lzo
import getpass
import shutil
from PIL import Image

procreatefile = sys.argv[-1]
zipref = zipfile.ZipFile(procreatefile, 'r')
user = getpass.getuser()
homedir = '/Users/' + user
pathtotemp = homedir + '/procreatetemp/'
zipref.extractall(pathtotemp)

plist = readPlist(pathtotemp + 'Document.archive')
objects = plist.get('$objects')
composite_number = objects[1].get('composite').integer
composite_key_number = objects[composite_number].get('UUID').integer
composite_key = objects[composite_key_number]
base = pathtotemp + composite_key + '/'
filelist = os.listdir(base)
imagesize_string = objects[objects[1].get('size').integer]
imagesize = imagesize_string.strip('{').strip('}').split(', ')
imagesize[0] = int(imagesize[0])
imagesize[1] = int(imagesize[1])
tilesize = objects[1].get('tileSize')
orientation = objects[1].get('orientation')
h_flipped = objects[1].get('flippedHorizontally')
v_flipped = objects[1].get('flippedVertically')

# create a new image
canvas = Image.new('RGBA', (imagesize[0], imagesize[1]))

# Figure out how many total rows and columns there are
columns = int(math.ceil(float(imagesize[0]) / float(tilesize)))
rows = int(math.ceil(float(imagesize[1]) / float(tilesize)))

# Calculate differencex and differencey
differencex = 0
differencey = 0
if imagesize[0] % tilesize != 0:
    differencex = (columns * tilesize) - imagesize[0]
if imagesize[1] % tilesize != 0:
    differencey = (rows * tilesize) - imagesize[1]

# iterate through chunks
# decompress them
# create images
# add those images to composite image
for (index, filename) in enumerate(filelist):

    # Get row and column from filename
    column = int(filename.strip('.chunk').split('~')[0])
    row = int(filename.strip('.chunk').split('~')[1]) + 1

    chunk_tilesize = {
        "x": tilesize,
        "y": tilesize
    }

    # Account for columns or rows that are too short
    if (column + 1) == columns:
        chunk_tilesize['x'] = tilesize - differencex
    if row == rows:
        chunk_tilesize['y'] = tilesize - differencey

    # read the actual data and create an image
    file = open(base + filename)
    data = file.read()
    # 262144 is the final byte size of the pixel data for 256x256 square.
    # This is based on 256*256*4 (width * height * 4 bytes per pixel)
    # finalsize is chunk width * chunk height * 4 bytes per pixel
    finalsize = chunk_tilesize['x'] * chunk_tilesize['y'] * 4
    decompressed = lzo.decompress(data, False, finalsize)
    # Will need to know how big each tile is instead of just saying 256
    tile = Image.frombytes('RGBA', (chunk_tilesize['x'],chunk_tilesize['y']), decompressed)
    # Tile starts upside down, flip it
    tile = tile.transpose(Image.FLIP_TOP_BOTTOM)

    # Calculate pixel position of tile
    positionx = column * tilesize
    positiony = (imagesize[1] - (row * tilesize))
    if (row == rows):
        positiony = 0

    # Add image to canvas
    canvas.paste(tile, (positionx,positiony))

if orientation == 3:
    canvas = canvas.rotate(90, expand=True)
elif orientation == 4:
    canvas = canvas.rotate(-90, expand=True)
elif orientation == 2:
    canvas = canvas.rotate(180, expand=True)

if h_flipped == 1 and (orientation == 1 or orientation == 2):
    canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)
if h_flipped == 1 and (orientation == 3 or orientation == 4):
    canvas = canvas.transpose(Image.FLIP_TOP_BOTTOM)
if v_flipped == 1 and (orientation == 1 or orientation == 2):
    canvas = canvas.transpose(Image.FLIP_TOP_BOTTOM)
if v_flipped == 1 and (orientation == 3 or orientation == 4):
    canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)
bytes = canvas.tobytes()
canvas.save(homedir + "/.procreatetemp.bmp")
shutil.rmtree(pathtotemp)