import xml.etree.ElementTree as ET
import numpy as np
import math
import os.path
import urllib
from PIL import Image
from PIL import ImageDraw
from sys import exit
from pyx import *
# sudo apt-get install imagemagick

def deg2pos(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = float((lon_deg + 180.0) / 360.0 * n)
  ytile = float((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def relative_location(node_xy, tile_nw, tile_se): # top/left corner = center
    percentage_x = (node_xy[0] - tile_nw[0]) / (tile_se[0] - tile_nw[0] + 1)
    percentage_y = (node_xy[1] - tile_nw[1]) / (tile_se[1] - tile_nw[1] + 1)
    return (percentage_x, percentage_y)

def draw_node_to_png(relative_location, image):
    x = int(np.floor(image.size[0]*relative_location[0]))
    y = int(np.floor(image.size[1]*relative_location[1]))
    # image.putpixel((x,y), (255,255,255))
    # image.putpixel((x,y), (0))
    draw = ImageDraw.Draw(image)
    r = 5
    draw.ellipse((x-r, y-r, x+r, y+r), fill=(255,255,255))
    r = 2
    draw.ellipse((x-r, y-r, x+r, y+r), fill=(0,0,0))

def draw_node_to_png2(relative_location, image):
  x = int(np.floor(image.size[0]*relative_location[0]))
  y = int(np.floor(image.size[1]*relative_location[1]))
  # image.putpixel((x,y), (255,255,255))
  # image.putpixel((x,y), (0))
  draw = ImageDraw.Draw(image)
  r = 5
  draw.ellipse((x-r, y-r, x+r, y+r), fill=(0,255,255))
  r = 2
  draw.ellipse((x-r, y-r, x+r, y+r), fill=(0,0,0))

def draw_edge_to_png(prev_rel_loc, relative_location, image):
  x0 = int(np.floor(image.size[0]*prev_rel_loc[0]))
  y0 = int(np.floor(image.size[1]*prev_rel_loc[1]))
  x1 = int(np.floor(image.size[0]*relative_location[0]))
  y1 = int(np.floor(image.size[1]*relative_location[1]))
  draw = ImageDraw.Draw(image)
  # print 'drawing edge between: ', prev_node_xy, ' and ', node_xy
  draw.line((x0, y0, x1, y1), fill=(0,150,150), width=2)

def draw_edge_to_pdf(prev_node_xy, node_xy, pdf, tile_nw, tile_se):
  # bottom/left nw = center / requires flip y axis
  pdf.stroke(path.line(prev_node_xy[0] - tile_nw[0],
                       -1*(prev_node_xy[1] - tile_se[1] - 1),
                       node_xy[0]      - tile_nw[0],
                       -1*(node_xy[1]      - tile_se[1] - 1) ))
  pdf.stroke(path.line(0,0,1,1))

def is_node_hospital(node):
  is_hospital = False
  for tag in node.iter('tag'):
    # print tag.attrib
    if 'hospital' == tag.get('v'):
      is_hospital = True
      return is_hospital

def parse_bounds(node):
  # bounds = np.zeros(shape=(2,2))
  minlat = float(node.get('minlat'))
  maxlat = float(node.get('maxlat'))
  minlon = float(node.get('minlon'))
  maxlon = float(node.get('maxlon'))
  bounds = np.array([[minlat, minlon], [maxlat, maxlon]])
  print bounds
  return bounds

def build_url(zoom, tile_x, tile_y):
  url_name = ("http://a.tile.openstreetmap.org/" + str(zoom)
  + "/" + str(tile_x) + "/" + str(tile_y) + ".png")
  # print 'built url_name: ', url_name
  return url_name

def build_path(url_name):
  # url_name = "http://a.tile.openstreetmap.org/17/41195/61693.png"
  directory = "data/"
  name_zoom = url_name.split('/')[-3]
  name_x = url_name.split('/')[-2]
  name_y = url_name.split('/')[-1]
  file_name = name_zoom + "-" + name_x + "-" + name_y
  local_path = directory + file_name
  return local_path

def download_url(url_name):
  local_path = build_path(url_name)
  if not os.path.isfile(local_path):
    print "downloading: ", url_name
    urllib.urlretrieve(url_name, local_path)

# test_url = build_url(15, 3, 7)
# download_url(test_url)
# exit()

tree = ET.parse('map.osm')      # print root.tag
root = tree.getroot()           # print root.attrib
# for child in root:
# print child.tag, child.attrib

# for node in root.iter('node'):
  # print node.attrib
  # print is_node_hospital(node)

osm_bounds = root.find('bounds')
map_bounds = parse_bounds(osm_bounds)

# y direction -> latitude
# x direction -> longitude
zoom = 19
tile_nw = deg2num(map_bounds[1][0], map_bounds[0][1], zoom)
tile_se = deg2num(map_bounds[0][0], map_bounds[1][1], zoom)
print 'tile_nw_xy', tile_nw
print 'tile_se_xy', tile_se
tile_nw_deg = num2deg(tile_nw[0], tile_nw[1], zoom)
tile_se_deg = num2deg(tile_se[0], tile_se[1], zoom)
print 'north_west_deg: ', tile_nw_deg
print 'south_east_deg: ', tile_se_deg

for tile_x in range(tile_nw[0], tile_se[0]+1):
  for tile_y in range(tile_nw[1], tile_se[1]+1):
    print 'tiles: ', tile_x, tile_y
    tile_url = build_url(zoom, tile_x, tile_y)
    download_url(tile_url)

map_image = Image.new("RGB",
                      ((tile_se[0]-tile_nw[0] + 1)*256,
                       (tile_se[1]-tile_nw[1] + 1)*256))

for tile_x in range(tile_nw[0], tile_se[0]+1):
  for tile_y in range(tile_nw[1], tile_se[1]+1):
    tile_url = build_url(zoom, tile_x, tile_y)
    tile_path = build_path(tile_url)
    image256x256 = Image.open(tile_path)
    map_image.paste(image256x256, (0 + 256*(tile_x - tile_nw[0]),
                                   0 + 256*(tile_y - tile_nw[1])))


map_image_node = map_image.copy()

# node_lat = 10.4938379
# node_lon = -66.8522287
# node_xy = deg2pos(node_lat, node_lon, zoom)
# print node_xy
# rel_location = relative_location(node_xy, tile_nw, tile_se)
# print rel_location
# draw_node_to_png(rel_location, map_image_node)

for node in root.iter('node'):
  # print node.attrib
  node_lat = float(node.get('lat'))
  node_lon = float(node.get('lon'))
  node_xy = deg2pos(node_lat, node_lon, zoom)
  rel_location = relative_location(node_xy, tile_nw, tile_se)
  draw_node_to_png(rel_location, map_image_node)


c = canvas.canvas()
c.insert(bitmap.bitmap(0, 0, map_image_node, height=(tile_se[1] - tile_nw[1] + 1)))

for way in root.iter('way'):
  for tag in way.iter('tag'):
    if tag.get('k') == "highway":
      prev_node_xy = None
      for nd in way.iter('nd'):
        ref = nd.get('ref')
        for node in root.iter('node'):
          if node.get('id') == ref:
              node_lat = float(node.get('lat'))
              node_lon = float(node.get('lon'))
              node_xy = deg2pos(node_lat, node_lon, zoom)
              rel_location = relative_location(node_xy, tile_nw, tile_se)
              draw_node_to_png2(rel_location, map_image_node)
              if prev_node_xy is not None:
                draw_edge_to_pdf(prev_node_xy, node_xy, c, tile_nw, tile_se)
                # c.stroke(path.line(0, 0, 1, 1))
                prev_rel_loc = relative_location(prev_node_xy, tile_nw, tile_se)
                draw_edge_to_png(prev_rel_loc, rel_location, map_image_node)
              break
        prev_node_xy = node_xy
  c.writePDFfile("map_image_node")
  raw_input("Press a key to continue...")

# c.writePDFfile("map_image_node")

# map_image.show()
map_image.save("map_image_empty.png")
map_image_node.save("map_image_node.png")
