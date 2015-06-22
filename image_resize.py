import urllib2
import StringIO
import math
from PIL import Image


max_width = 384.
max_height = 512.

def aspect_fit(img, width, height):
  size =  img.size

  xScale = float(width)/size[0]
  yScale = float(height)/size[1]

  scale = min(xScale, yScale)

  new_size = (int(size[0] * scale), int(size[1] * scale))
  return img.resize(new_size, Image.ANTIALIAS)


if __name__ == "__main__":
  try:
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = urllib2.Request('http://townandcountryremovals.com/wp-content/uploads/2013/10/firefox-logo-200x200.png', None, headers)
    data = urllib2.urlopen(req).read()

    img = Image.open(StringIO.StringIO(data))
    new_image = resize(img, max_width, max_height)

    print img
    print new_image
  except Exception, e:
    # The image is not valid
    print e
