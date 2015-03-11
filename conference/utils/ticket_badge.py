#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import math
import optparse
import os
import os.path
import re
import sys
from PIL import Image, ImageDraw
from itertools import izip_longest

parser = optparse.OptionParser(usage='%(prog)s [options] output_dir')
parser.add_option("-i", "--input",
                    dest="input",
                    default=None,
                    action="store",
                    help="input file (default stdin)")
parser.add_option("-p", "--page-size",
                    dest="page_size",
                    default="490x318",
                    action="store",
                    help="page size (mm)")
parser.add_option("-d", "--dpi",
                    dest="dpi",
                    default=300,
                    action="store",
                    type="int",
                    help="dpi")
parser.add_option("-r", "--resize",
                    dest="resize",
                    default=None,
                    action="store",
                    type="float",
                    help="resize factor (if any)")
parser.add_option("-n", "--per-page",
                    dest="per_page",
                    default=9,
                    action="store",
                    type="int",
                    help="badge per page")
parser.add_option("-c", "--conf",
                    dest="conf",
                    default="conf.py",
                    action="store",
                    help="configuration script")
parser.add_option("-e", "--empty-pages",
                    dest="empty_pages",
                    default="0",
                    action="store",
                    help="prepare x empty pages")
parser.add_option("--center",
                    dest="align_center",
                    default=False,
                    action="store_true",
                    help="align badges horizontally")
parser.add_option("--x-mirror",
                    dest="mirror_x",
                    default=False,
                    action="store_true",
                    help="reorder badge along the x axis")

opts, args = parser.parse_args()

try:
    output_dir = args[0]
except IndexError:
    parser.print_usage()

conf = {}
os.chdir(os.path.dirname(opts.conf))
execfile(os.path.basename(opts.conf), conf)

MM2INCH = 0.03937
tickets = conf['tickets']
ticket = conf['ticket']
DPI = opts.dpi
WASTE = conf.get('WASTE', 0) * MM2INCH * DPI
PAGE_MARGIN = int(conf.get('PAGE_MARGIN', 10) * MM2INCH * DPI)

if opts.page_size == 'A3':
    psize = "420x297"
elif opts.page_size == 'A4':
    psize = "297x210"
else:
    psize = opts.page_size
PAGE_SIZE = map(lambda x: int(int(x) * MM2INCH * DPI), psize.split('x'))

data = json.loads(sys.stdin.read())

groups = tickets(data)

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

def wrap_text(font, text, width):
    words = re.split(' ', text)
    lines = []
    while words:
        word = words.pop(0).strip()
        if not word:
            continue
        if not lines:
            lines.append(word)
        else:
            line = lines[-1]
            w, h = font.getsize(line + ' ' + word)
            if w <= width:
                lines[-1] += ' ' + word
            else:
                lines.append(word)

    for ix, line in enumerate(lines):
        line = line.strip()
        while True:
            w, h = font.getsize(line)
            if w <= width:
                break
            line = line[:-1]
        lines[ix] = line
    return lines

def draw_info(image, max_width, text, pos, font, color, line_offset=8):
    d = ImageDraw.Draw(image)

    cx = pos[0]
    cy = pos[1] - font.getsize(text)[1]
    lines = wrap_text(font, text, max_width)
    for l in lines:
        d.text((cx, cy), l, font = font, fill = color)
        cy += font.getsize(l)[1] + line_offset

def assemble_page(images, align='left', mirror_x=False):
    page = Image.new('RGBA', PAGE_SIZE, (255, 255, 255, 255))
    limits = (
        PAGE_SIZE[0] - 2*PAGE_MARGIN,
        PAGE_SIZE[1] - 2*PAGE_MARGIN)

    x = y = 0
    rows = [[]]
    for img in images:
        size = img.size
        if x + size[0] > limits[0]:
            x = 0
            y += size[1]
            rows.append([])
        #elif y + size[1] > limits[1]:
        #    y += size[1]
        #    rows.append([])
        rows[-1].append((img, (x, y)))
        x += size[0]

    for row in rows:
        if align == 'center':
            align_offset = 1
            row_width = sum([ ])
            for img, pos in row:
                row_width += img.size[0]
            align_offset = (PAGE_SIZE[0] - row_width) / 2, PAGE_MARGIN
        else:
            align_offset = PAGE_MARGIN, PAGE_MARGIN
        if mirror_x:
            original = row
            mirrored = row[::-1]
            for ix, el in enumerate(zip(original, mirrored)):
                img = el[0][0]
                mirrored_pos = el[1][1]
                row[ix] = (img, mirrored_pos)
        for img, pos in row:
            x, y = pos
            align_x, align_y = align_offset
            page.paste(img, (x + align_x, y + align_y), img)
    return page

def add_page(name, page):
    with file(os.path.join(output_dir, name), 'w') as out:
        page.save(out, 'TIFF', dpi=(DPI, DPI))

def render_badge(image, attendee, utils, resize_factor=None):
    i = ticket(image, attendee, utils=utils)
    if resize_factor:
        nsize = i.size[0] * resize_factor, i.size[1] * resize_factor
        i = i.resize(nsize, Image.ANTIALIAS)
    return i

badge_align = 'left' if not opts.align_center else 'center'
badge_x_mirror = opts.mirror_x

for group_type, data in sorted(groups.items()):
    image = data['image']
    attendees = data['attendees']
    pages = len(attendees) / opts.per_page
    if len(attendees) % opts.per_page:
        pages += 1

    utils = {
        'wrap_text': wrap_text,
        'draw_info': draw_info,
    }
    count = 1
    for block in grouper(opts.per_page, attendees):
        if block:
            images = []
            for a in block:
                badge = render_badge(image, a, utils=utils, resize_factor=opts.resize)
                images.append(badge)
            page = assemble_page(images, badge_align, badge_x_mirror)

            name = '[%s] pag %s-%s.tif' % (group_type, str(count).zfill(2), str(pages).zfill(2))
            print >>sys.stderr, name
            add_page(name, page)

        count += 1

    if opts.empty_pages.endswith('%'):
        additional = int(math.ceil(pages * float(opts.empty_pages[:-1]) / 100 ))
    else:
        additional = int(opts.empty_pages)
    for ix in range(additional):
        name = '[%s][vuoti] pag %s-%s.tif' % (group_type, str(ix+1).zfill(2), str(additional).zfill(2))
        images = [ render_badge(image, None, utils=utils, resize_factor=opts.resize) for x in range(opts.per_page) ]
        add_page(name, assemble_page(images, badge_align))
