#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import argparse
import sys
import csv
import codecs
import re

from bs4 import BeautifulSoup

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO


__version__ = "0.0.2"


class CSVWriter(object):
    """Simple CSV writer that writes utf-8 to stdout"""
    def __init__(self, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = sys.stdout
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, *row):
        self.writer.writerow([str(s).encode("utf-8") for s in row]) # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8") # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)


def console():
    parser = argparse.ArgumentParser(description='CSS selectors for parsing html on the command line')
    parser.add_argument("--version", "-V", action='version', version="%(prog)s {}".format(__version__))
    parser.add_argument('selector', type=str)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)

    args = parser.parse_args()
    csv_writer = CSVWriter()

    selector = args.selector
    # the selector is in 2 parts divided by ->, the first part is a standard CSS
    # selector, the second part are the attributes you want to print of the matched
    # tags
    # TODO -- innerHtml or the like should be possible to print out
    parts = selector.split("->", 1)
    selector = parts[0]
    contains = ""
    columns = []
    if len(parts) > 1:
        format_strs = re.split(r"(?<!\\),", parts[1])
        for format_str in format_strs:
            attrs = re.findall(r"(?<={)[^}]+(?=})", format_str)
            if attrs:
                column = {
                    "format_str": format_str,
                    "attrs": attrs,
                }
            else:
                column = {
                    "attrs": [format_str],
                }

            columns.append(column)

    if ":contains" in selector:
        selector, contains = selector.split(":contains")
        contains = contains.strip("(\"')")

    html = args.infile.read()
    soup = BeautifulSoup(html, "html.parser")
    tags = soup.select(selector)
    for tag in tags:
        vals = []
        if contains:
            if contains not in "".join(tag.strings):
                continue

        for column in columns:
            keys = {}
            for attr in column["attrs"]:
                try:
                    keys[attr] = tag[attr].strip()
                except KeyError:
                    keys[attr] = ""

            if "format_str" in column:
                vals.append(column["format_str"].format(**keys))
            else:
                vals.append(keys.values()[0])

        if vals:
            csv_writer.writerow(*vals)


if __name__ == "__main__":
    console()

