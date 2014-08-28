#!/usr/bin/python3

import tempfile
import zipfile
import xml.etree.ElementTree as ET
import os
import cairo

import pysmartpen
import parsestf


class Parser(parsestf.STFParser):
    def __init__(self, stream):
        super(Parser, self).__init__(stream)
        self.force = 0

    def handle_stroke_end(self, time):
        self.ctx.stroke()
        self.force = 0

    def handle_point(self, x, y, force, time):
        ctx = self.ctx
        if force:
            if self.force:
                ctx.set_line_width(force/3.)
                ctx.line_to(x, y)
            else:
                ctx.move_to(x, y)
        self.force = force

    def parse(self, ctx):
        self.ctx = ctx
        super(Parser, self).parse()


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

    @staticmethod
    def notebook_to_pdf(fil):
        z = zipfile.ZipFile(fil, "r")

        surface = cairo.PDFSurface("{}.pdf".format(fil), 4963, 6278)
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(0xff, 0xff, 0xff)
        ctx.paint()
        ctx.set_source_rgb(0x00, 0x00, 0x00)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)

        for name in sorted(z.namelist()):
            if not name.startswith('data/'):
                continue
            f = z.open(name)
            p = Parser(f)
            p.parse(ctx)
            ctx.show_page()


if __name__ == "__main__":
    pen = Smartpen()
    pen.connect()
    print(pen.get_info().decode("ascii"))
    for lsp, fd in pen.notebooks():
        nb = "{}.zip".format(lsp.get("title"))
        print(nb)
        open(nb, "wb").write(os.fdopen(fd, "rb").read())
        pen.notebook_to_pdf(nb)
    pen.disconnect()
