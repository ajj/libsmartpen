#!/usr/bin/env python3
import pysmartpen
import sys
import time
import xml.etree.ElementTree as ElementTree
"""
Script to help measure the drift of the (rtc) clock on the pen.

Each point in a pen stroke uses this clock. Also, when a session starts, the
pen records the start_time as well as user_time, which seems to be a constant
offset from start_time until the next time you set the pen clock.

Print pen_id, now (unix ms), time of rtc clock epoch (unix ms)

To run this on all the pens, do this:
while read x; do ./get-time.py; done
"""
def main():
  s = pysmartpen.Smartpen()
  s.connect(vendor=0x1cfb, product=0x1010)
  now_unix_ms = time.time() * 1000
  peninfo = s.get_info()
  xml = ElementTree.fromstring(peninfo)
  pen_id = int(xml.find('peninfo').attrib['penid'], 16)
  now_rtc = int(xml.find('peninfo/time').attrib['absolute'])
  batt = xml.find('peninfo/battery').attrib['level']
  rtc_epoch_start_ms = now_unix_ms - now_rtc
  s.disconnect()
  print("0x%016x\t%d\t%d\t%s" %(pen_id, now_unix_ms, rtc_epoch_start_ms, batt))

if __name__ == "__main__":
  main()
