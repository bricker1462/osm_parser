import xml.etree.ElementTree as ET
import numpy as np
import math
import os.path
import urllib
import pygame
from PIL import Image
from PIL import ImageDraw
from sys import exit
from pyx import *
from pygame.locals import *
# sudo apt-get install imagemagick

#################
### FUNCTIONS ###
#################
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

def get_mouse_deg(mouse_x, mouse_y, image, tile_nw, tile_se, zoom):
  mouse_map_x = (float(mouse_x) / image.size[0]) * (tile_se[0] - tile_nw[0] + 1) + tile_nw[0]
  mouse_map_y = (float(mouse_y) / image.size[1]) * (tile_se[1] - tile_nw[1] + 1) + tile_nw[1]
  (mouse_lat, mouse_lon) = num2deg(mouse_map_x, mouse_map_y, zoom)
  # print mouse_lat, mouse_lon
  # print mouse_map_x, mouse_map_y
  return (mouse_lat, mouse_lon)

def get_node(mouse_lat, mouse_lon, threshold, root):
  min_distance = 1.0
  min_node_id  = None
  for node in root.iter('node'):
    node_lat = float(node.get('lat'))
    node_lon = float(node.get('lon'))
    node_id  = node.get('id')
    distance = math.sqrt(pow(mouse_lat - node_lat, 2) + pow(mouse_lon - node_lon, 2))
    if (distance < min_distance):
      # print "found a new minimum distance: ", distance
      min_distance = distance
      min_node_id  = node_id
  # print "minimum node_id: ", min_node_id, " distance: ", min_distance
  if min_distance < threshold:
    return min_node_id
  else:
    return None

def get_node_xy(node_id, root, image, tile_nw, tile_se, zoom):
    for node in root.iter('node'):
      if node_id == node.get('id'):
        node_lat = float(node.get('lat'))
        node_lon = float(node.get('lon'))
        (node_map_x, node_map_y) = deg2pos(node_lat, node_lon, zoom)
        node_x = int((node_map_x - tile_nw[0]) / (tile_se[0] - tile_nw[0] + 1) * image.size[0])
        node_y = int((node_map_y - tile_nw[1]) / (tile_se[1] - tile_nw[1] + 1) * image.size[1])
        return (node_x, node_y)
    return (0, 0)

def print_node_info(node_id, root):
  for node in root.iter('node'):
    current_node_id = node.get('id')
    if node_id == current_node_id:
      print "found a match in node: ", node.get('id')
  for way in root.iter('way'):
    for nd in way.iter('nd'):
      current_node_id = nd.get('ref')
      if node_id == current_node_id:
        print "found a match in way: ", way.get('id')
  # for rel in root.iter('relation'):
  #   for member in rel.iter('member'):
  #     current_node_id = member.get('ref')
  #     if node_id == current_node_id:
  #       print "found a match in relation: ", rel.get('id')
  print "----------------------------------------"

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
  # pdf.stroke(path.line(0,0,1,1))
  pdf.stroke(path.line(prev_node_xy[0] - tile_nw[0],
                       -1*(prev_node_xy[1] - tile_se[1] - 1),
                       node_xy[0]      - tile_nw[0],
                       -1*(node_xy[1]      - tile_se[1] - 1) ))


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

##################
### TREE PARSE ###
##################
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

#####################
### BUILD MAP PNG ###
#####################
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
# map_image.show()
map_image.save("map_image_empty.png")

### DRAW NODES TO PNG ###
map_image_node = map_image.copy()

for node in root.iter('node'):
  # print node.attrib
  node_lat = float(node.get('lat'))
  node_lon = float(node.get('lon'))
  node_xy = deg2pos(node_lat, node_lon, zoom)
  rel_location = relative_location(node_xy, tile_nw, tile_se)
  draw_node_to_png(rel_location, map_image_node)

######################
### BUILD PDF FILE ###
######################
c = canvas.canvas()
c.insert(bitmap.bitmap(0, 0, map_image_node, height=(tile_se[1] - tile_nw[1] + 1)))

for way in root.iter('way'):
  for tag in way.iter('tag'):
    if tag.get('k') == "highway" and tag.get('v') == "residential":
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
              if prev_node_xy != None:
                draw_edge_to_pdf(prev_node_xy, node_xy, c, tile_nw, tile_se)
                prev_rel_loc = relative_location(prev_node_xy, tile_nw, tile_se)
                draw_edge_to_png(prev_rel_loc, rel_location, map_image_node)
              break
        prev_node_xy = node_xy
  # c.writePDFfile("map_image_node")
  # raw_input("Press a key to continue...")

c.writePDFfile("map_image_node") # PDF / EPS
map_image_node.save("map_image_node.png")

##########################
### INTERACTIVE WINDOW ###
##########################
fps = 60
pygame.init() # http://www.pygame.org/docs/ref/draw.html
pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, MOUSEMOTION])
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)
flags = DOUBLEBUF
window = pygame.display.set_mode(((tile_se[0]-tile_nw[0] + 1)*256,
                                  (tile_se[1]-tile_nw[1] + 1)*256), pygame.HWSURFACE)#flags)

window.set_alpha(None)
image_surf = pygame.image.load("map_image_node.png").convert()
window.blit(image_surf,(0,0))
# pygame.draw.circle(window, (255, 0, 0), (0,0), 20, 0)
# pygame.draw.line(window, (255, 255, 255), (0, 0), (30, 50))

#draw it to the screen
pygame.display.flip()

# with input handling:
old_rectangle  = pygame.draw.circle(window, (0, 0, 0), (0, 0), 20, 0)
node_rect = pygame.draw.circle(window, (0, 0, 0), (0, 0), 20, 0)
prev_node_rect = node_rect
selected_node = [0, 0]
prev_selected_node = [0, 0]
while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      exit(0)
    if event.type == pygame.MOUSEBUTTONDOWN:
      (mouse_x, mouse_y) = pygame.mouse.get_pos()
      (mouse_lat, mouse_lon) = get_mouse_deg(mouse_x, mouse_y, map_image, tile_nw, tile_se, zoom)
      node_id = get_node(mouse_lat, mouse_lon, 1.5e-5, root)
      if node_id != None:
        print "Node clicked is: ", node_id
        print_node_info(node_id, root)
        window.blit(image_surf, prev_node_rect, prev_node_rect)
        pygame.display.update(prev_node_rect)
        selected_node = get_node_xy(node_id, root, map_image, tile_nw, tile_se, zoom)
        node_rect = pygame.draw.circle(window, (0, 0, 255), (selected_node[0], selected_node[1]), 10, 0)
        pygame.display.update(node_rect)
        prev_node_rect = node_rect
        prev_selected_node = selected_node
    else:
      # print event
      window.blit(image_surf, old_rectangle, old_rectangle)
      (mouse_x, mouse_y) = pygame.mouse.get_pos()
      rectangle = pygame.draw.circle(window, (255, 0, 0), (mouse_x, mouse_y), 2, 0)
      node_rect = pygame.draw.circle(window, (0, 0, 255), (selected_node[0], selected_node[1]), 10, 0)
      rectangle.inflate_ip(10, 10)
      pygame.display.update(rectangle.union(old_rectangle))
      old_rectangle = rectangle
      # Info and flip screen
      # window.blit(font.render("fps: " + str(clock.get_fps()), 1, (255,255,255)), (0,0))
      # print "fps: " + str(clock.get_fps())
      # clock.tick(fps)

# without input handling:
# old_rectangle = pygame.draw.circle(window, (255, 0, 0), (0, 0), 20, 0)
# while True:
#   # print event
#   pygame.event.get()
#   window.blit(image_surf, old_rectangle, old_rectangle)
#   (mouse_x, mouse_y) = pygame.mouse.get_pos()
#   rectangle = pygame.draw.circle(window, (255, 0, 0), (mouse_x, mouse_y), 20, 0)
#   rectangle.inflate_ip(10, 10)
#   pygame.display.update(rectangle.union(old_rectangle))
#   old_rectangle = rectangle
#   # Info and flip screen
#   # window.blit(font.render("fps: " + str(clock.get_fps()), 1, (255,255,255)), (0,0))
#   print "fps: " + str(clock.get_fps())
#   clock.tick(fps)
