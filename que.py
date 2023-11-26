#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import argparse
import sys
import csv
import codecs
import re
import os
import tempfile
from distutils import dir_util
import hashlib
import codecs
import datetime
import json
import shutil


from datatypes import String, Scanner, CSV as CSVIO, TempCSV
from captain import Command, handle, arg

# from bs4 import BeautifulSoup
# import requests
# 
# try:
#     from cStringIO import StringIO
# except ImportError:
#     try:
#         from StringIO import StringIO
#     except ImportError:
#         from io import StringIO


__version__ = "0.0.3"


class CSVStream(object):
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


class Selector(object):
    """Break up the CSS Selector->print string so we know what we are looking for
    and printing out

    https://www.w3schools.com/cssref/css_selectors.php
    """
    def __init__(self, buffer):
        # the selector is in 2 parts divided by ->, the first part is a standard CSS
        # selector, the second part are the attributes you want to print of the matched
        # tags
        scanner = Scanner(buffer)
        delims = ["->", "+>"]

        selector = scanner.read_to_delims(delims)

        selector_scanner = Scanner(selector)

        chars = {"[", ">", "+", "~", ":"}
        element = selector_scanner.read_to_chars(chars).strip()
        char = selector_scanner.read_thru_chars(chars)

        self.needle = {}
        if char == "[":
            chars = {"=", "~", "|", "^", "$", "*"}
            attribute = selector_scanner.read_to_chars(chars).strip()
            assignment = selector_scanner.read_thru_chars(chars)
            needle = selector_scanner.read_to_delim("]").strip()
            self.needle = {
                "attribute": attribute,
                "assignment": assignment,
                "needle": needle,
            }

        if char == ":":
            action = selector_scanner.read_to_chars("(")

            subselector = selector_scanner.read_balanced_delims(
                "(", ")",
                strip=True
            )

            self.action = {
                "action": action,
                "selector": subselector,
            }

        self.columns = []
        self.assignment = scanner.read_thru_delims(delims)
        if self.assignment:
            while format_str := scanner.read_to_chars(",").strip():
                # each separate piece of the print parts can be a python format string
                # https://docs.python.org/2/library/string.html#formatspec
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

                self.columns.append(column)

                scanner.read_thru_chars(",")

        else:
            self.columns.append({"attrs": ["innerAll"]})

        self.selector = selector
        self.element = element

        # we split the Selector into the css selector and print value parts
#         parts = v.split("->", 1)
#         selector = parts[0]
#         pout.v(parts, selector)
# 
#         if selector[0] == "[":
#             attribute = ""
# 
#             assignment = ""
#             assignment_chars = {"=", "~", "|", "^", "$", "*"}
# 
#             needle = ""
#             in_needle = False
# 
#             index = 0
# 
#             while selector[index] != "]":
#                 ch = selector[index]
# 
#                 if ch in assignment_chars:
#                     while ch in assignment_chars:
#                         assignment += ch
#                         index += 1
#                         ch = selector[index]
# 
#                     in_needle = True
# 
#                 else:
#                     if in_needle:
#                         needle += ch
#                     else:
#                         assignment += ch
# 
#                 index += 1







    def __new2__(cls, val):
        instance = super().__new__(cls, val)

        # the selector is in 2 parts divided by ->, the first part is a standard CSS
        # selector, the second part are the attributes you want to print of the matched
        # tags
        # we split the Selector into the css selector and print value parts
        parts = instance.split("->", 1)
        selector = parts[0]
        contains = ""
        columns = []
        if len(parts) > 1:
            # we split the parts on non-escaped comma
            format_strs = re.split(r"(?<!\\),", parts[1])
            for format_str in format_strs:
                # each separate piece of the print parts can be a python format string
                # https://docs.python.org/2/library/string.html#formatspec
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

        else:
            columns.append({"attrs": ["innerAll"]})

        if ":contains" in selector:
            selector, contains = selector.split(":contains")
            contains = contains.strip("(\"')")

        instance.selector = selector
        instance.contains = contains
        instance.columns = columns
        pout.v(instance.selector, instance.contains, instance.columns)
        return instance

#     def select(self, html):
#         """This will return BeautifulSoup4 tag instances for the html that matches
#         the selector
# 
#         :param html: str, the html to use the CSS select on
#         :returns: generator, yields the matching tags
#         """
#         soup = BeautifulSoup(html, "html.parser")
#         tags = soup.select(self.selector)
#         for tag in tags:
#             if self.contains:
#                 if self.contains not in "".join(tag.strings):
#                     continue
# 
#             yield tag
# 
#     def map(self, html):
#         """This will take the html, apply the selector, and yield the results
# 
#         :param html: str, the html to use the CSS select on
#         :returns: generator, yields the rows the selector matched and formatted
#         """
#         for tag in self.select(html):
#             vals = []
#             for column in self.columns:
#                 keys = {}
#                 for attr in column["attrs"]:
#                     v = attr.lower() # we want to be flexible with case for inner*
#                     if v == "innerhtml":
#                         #keys[attr] = "".join(str(t) for t in tag.children)
#                         keys[attr] = tag.decode_contents(formatter="html")
# 
#                     elif v == "innertext":
#                         keys[attr] = "".join(tag.strings)
# 
#                     elif v == "innerall":
#                         keys[attr] = str(tag)
# 
#                     else:
#                         try:
#                             keys[attr] = tag[attr].strip()
#                         except KeyError:
#                             keys[attr] = ""
# 
#                 if "format_str" in column:
#                     vals.append(column["format_str"].format(**keys))
#                 else:
#                     vals.append(keys.values()[0])
# 
#             if vals:
#                 yield vals


class Bodies(object):
    """On the command line you can pass in a url, a file with html, a file with urls on each
    line, or you can pipe stdin, this class normalizes all that, requesting any urls
    passed in (from files and args) and returns just the bodies"""

    REGEX_URL = re.compile("^\s*\S+:\/\/\S+\s*$", re.M)

    @property
    def cache_dir(self):
        global __version__
        cache_dir = os.path.join(tempfile.gettempdir(), "que", __version__)
        return cache_dir

    def __init__(self, vals):
        if vals:
            self.vals = vals

        else:
            body = sys.stdin.read()
            if body:
                self.vals = [body]

        if not self.vals:
            raise ValueError("No Values found!")

    def __iter__(self):
        for val in self.vals:
            if self.REGEX_URL.match(val):
                body = self.fetch_body(val)
                yield body

            else:
                if os.path.isfile(val):
                    #path = os.path.abspath(os.path.expanduser(val))
                    path = val
                    with open(path) as fp:
                        body = fp.read()

                    lines = filter(None, body.splitlines(False))
                    if all(self.REGEX_URL.match(line) for line in lines):
                    #if self.REGEX_URL.match(body):
                        for url in lines:
                        #for url in body.splitlines(False):
                            url = url.strip()
                            body = self.fetch_body(url)
                            yield body

                    else:
                        yield body

                else:
                    yield val

    def fetch_body(self, url):
        global __version__

        ret = ""
        cache_dir = self.cache_dir
        cache_path = os.path.join(cache_dir, "{}.txt".format(hashlib.md5(str(url)).hexdigest()))
        cache_date_str = "%Y-%m-%dT%H:%M:%S.%fZ"
        now = datetime.datetime.utcnow()

        # !!! - I could use a more full featured caching library here:
        # https://httpcache.readthedocs.io/en/latest/
        # https://github.com/reclosedev/requests-cache
        # https://requests-cache.readthedocs.io/en/latest/user_guide.html
        # https://realpython.com/blog/python/caching-external-api-requests/

        if os.path.isfile(cache_path):
            with codecs.open(cache_path, encoding='utf-8', mode='r+') as fp:
                d = json.load(fp)
                created = datetime.datetime.strptime(d["created"], cache_date_str)
                ttl = datetime.timedelta(seconds=int(d["ttl"]))
                if (created + ttl) > now:
                    ret = d["body"]

        if not ret:
            user_agent = "Mozilla/5.0 AppleWebKit/0.0 (KHTML, like Gecko) Chrome/0.0.0.0 Safari/0.0 que/{}".format(
                __version__
            )

            browser = requests.Session()
            browser.headers.update({
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate, sdch, br",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            })

            res = browser.get(url)
            if res.status_code >= 400: 
                raise IOError("Fetching {} returned {} with body {}".format(url, res.status_code, res.content))

            ret = res.content

            # cache the response
            dir_util.mkpath(cache_dir)
            with codecs.open(cache_path, encoding='utf-8', mode='w+') as fp:
                json.dump({
                    "created": datetime.datetime.strftime(now, cache_date_str),
                    "ttl": 3600,
                    "body": ret
                }, fp)

        return ret

    def clear_cache(self):
        shutil.rmtree(self.cache_dir)


# def console():
#     parser = argparse.ArgumentParser(description='CSS selectors for parsing html on the command line')
#     parser.add_argument("--version", "-V", action='version', version="%(prog)s {}".format(__version__))
#     # TODO -- ; (semicolon) should separate different selectors and this should be type=Selectors
#     parser.add_argument('selector', type=Selector)
#     parser.add_argument('input', nargs='*')
# 
#     args = parser.parse_args()
#     bs = Bodies(args.input)
#     csv_writer = CSVWriter()
# 
#     selector = args.selector
#     for body in bs:
#         for vals in selector.map(body):
#             csv_writer.writerow(*vals)



class CSV(Command):
    @arg(
        "selector",
        type=Selector
    )
    @arg(
        "paths",
        nargs="*"
    )
    def handle(self, selector, paths):
        #pout.v(selector, paths)

        output_rows = []

        for path in paths:
            csv = CSVIO(path)

            for row in csv:
                output_row = {}

                if selector.needle:
                    needle = selector.needle["needle"]
                    haystack = row.get(selector.needle["attribute"])
                    assignment = selector.needle["assignment"]

                    if assignment == "~=":
                        if needle in haystack:
                            output_row = row

                    # TODO: need to add other checks
                    else:
                        raise NotImplementedError()

                else:
                    output_row = row

                if output_row:
                    if selector.assignment == "->":
                        if selector.columns:
                            orow = {}
                            for column in selector.columns:
                                for cname in column["attrs"]:
                                    orow[cname] = output_row.get(cname, None)

                            output_row = orow

                    output_rows.append(output_row)

        if selector.assignment == "+>":
            cname = selector.columns[0]["attrs"][0]
            value = 0
            for row in output_rows:
                value += float(row[cname])

            output_rows = [
                {
                    cname: value
                }
            ]

        if output_rows:
            with TempCSV() as csv:
                for row in output_rows:
                    csv.add(row)

            print(csv)

        #pout.v(output_rows)




if __name__ == "__main__":
    #console()
    handle()

