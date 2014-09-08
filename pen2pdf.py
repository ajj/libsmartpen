#!/usr/bin/python3

import tempfile
import zipfile
import xml.etree.ElementTree as ET
import os
import cairo
import re
import time

import pysmartpen
import parsestf


class Parser(parsestf.STFParser):
    def __init__(self, stream):
        super(Parser, self).__init__(stream)
        self.force = 0
        self.times = []

    def handle_stroke_end(self, time):
        self.ctx.stroke()
        self.force = 0

    def handle_point(self, x, y, force, time):
        ctx = self.ctx
        if force:
            if self.force:
                ctx.set_line_width(force**.3*3)
                ctx.line_to(x, y)
            else:
                ctx.move_to(x, y)
        self.force = force
        self.times.append(time)

    def parse(self, ctx, t0=None, name=None):
        self.ctx = ctx

        self.ctx.save()
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgb(0, .06, .33)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(8)

        super(Parser, self).parse()


        title = []
        if name is not None:
            title.append(name)

        if t0 is not None:
            t = "{} to {}".format(
                time.strftime("%c", time.localtime(self.times[0]/1000.+t0)),
                time.strftime("%c", time.localtime(self.times[-1]/1000.+t0)))
            title.append(t)

        if title:
            t = " - ".join(title)
            self.ctx.save()
            self.ctx.scale(10, 10)
            #x, y, w, h, dx, dy = self.ctx.text_extents(t)
            self.ctx.move_to(30, 30)
            self.ctx.show_text(t)
            self.ctx.restore()

        self.ctx.restore()


class Smartpen(pysmartpen.Smartpen):
    def connect(self, product=None):
        connect = super(Smartpen, self).connect
        if product is not None:
            return connect(product=product)
        usbids = 0x1010, 0x1020, 0x1030, 0x1032
        for id in usbids:
            try:
                return connect(product=id)
            except:
                continue
        raise

    def notebooks(self):
        changes = self.get_changelist()
        root = ET.fromstring(changes)
        for lsp in root.findall("changelist/lsp"):
            if not lsp.get("guid"):
                continue
            fd, tmpfile = tempfile.mkstemp()
            try:
                self.get_guid(tmpfile, lsp.get("guid"), 0)
                yield lsp, fd
            finally:
                os.unlink(tmpfile)

    def audio(self):
        fd, tmpfile = tempfile.mkstemp()
        self.get_paperreplay(tmpfile, 0)
        try:
            yield fd
        finally:
            os.unlink(tmpfile)


def notebook_to_pdf(fil, t0=None):
    z = zipfile.ZipFile(fil, "r")

    size = 4963, 6278
    res = 1/10.
    surface = cairo.PDFSurface("{}.pdf".format(fil), *(i*res for i in size))
    ctx = cairo.Context(surface)
    ctx.scale(res, res)

    files = sorted(z.namelist())
    pages = [n for n in files if re.match(r"^data/.*/.*/.*.stf$", n)]
    papers = [n for n in files if re.match(r"^userdata/lsac_data/.*\.png$", n)]

    papers = [cairo.ImageSurface.create_from_png(z.open(p)) for p in papers]

    for i, name in enumerate(pages):
        paper = papers[i%2]
        scale = size[0]/paper.get_width()
        f = z.open(name)
        ctx.save()
        ctx.scale(scale, scale)
        ctx.set_source_surface(paper, 0, 0)
        ctx.paint()
        ctx.restore()
        n = "{} - {}/{}".format(fil, i + 1, len(pages))
        Parser(f).parse(ctx, t0=t0, name=n)
        ctx.show_page()


if __name__ == "__main__":
    pen = Smartpen()
    pen.connect()
    info = pen.get_info()
    print(info.decode("ascii"))
    t0 = ET.fromstring(info).find("peninfo/time")
    t0 = time.time() - float(t0.get("absolute"))/1000
    for lsp, fd in pen.notebooks():
        nb = "{}.zip".format(lsp.get("title"))
        print(nb)
        open(nb, "wb").write(os.fdopen(fd, "rb").read())
        notebook_to_pdf(nb, t0=t0)

    for fd in pen.audio():
        nb = "audio.zip"
        open(nb, "wb").write(os.fdopen(fd, "rb").read())

    pen.disconnect()
