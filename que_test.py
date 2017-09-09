# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
from unittest import TestCase
import subprocess
import os
from contextlib import contextmanager
import SimpleHTTPServer
import BaseHTTPServer

import testdata

from que import Selector, Bodies


class WebHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        self.base_path = server.base_path
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def translate_path(self, path):
        #path = super(WebHandler, self).translate_path(self, path)
        path = SimpleHTTPServer.SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.base_path, relpath)
        return fullpath


class HTTPServer(BaseHTTPServer.HTTPServer):
    def __init__(self, base_path, server_address, RequestHandlerClass):
        self.base_path = base_path
        BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)


class Webserver(object):
    def __init__(self, files, port=8765):
        base_path = testdata.create_files(files)
        self.hostname = "http://127.0.0.1:{}".format(port)

        httpd = HTTPServer(base_path, ("", port), WebHandler)
        self.httpd = httpd

        # TODO -- move all this to start() method
        def target():
            try:
                httpd.serve_forever()
            except Exception as e:
                raise

        th = testdata.Thread(target=target)
        th.daemon = True
        th.start()
        self.thread = th

    @classmethod
    @contextmanager
    def start(cls, *args, **kwargs):
        instance = None
        try:
            instance = cls(*args, **kwargs)
            yield instance

        finally:
            if instance:
                instance.stop()

    def url(self, *parts):
        vs = [self.hostname]
        vs.extend(map(lambda p: p.strip("/"), parts))
        return "/".join(vs)

    def stop(self):
        self.httpd.shutdown()


class Client(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.run()

    def run(self):
        self.output = subprocess.check_output(self.cmd, shell=True).rstrip()


class MainTest(TestCase):
    def test_stdin(self):
        c = Client('echo "<a href=\"http://example.com/foo\">text</a>" | python -m que "a->href"')
        self.assertEqual("http://example.com/foo", c.output)


class BodiesTest(TestCase):
    def test_url_file(self):
        s = set(["foo", "bar", "che"])

        with Webserver.start({"{}.html".format(k): k for k in s}) as w:
            # make sure whitespace is ignored
            path = testdata.create_file("bodies-url.txt", ["\n{}\n\n".format(w.url("{}.html".format(k))) for k in s])
            bods = Bodies([path])
            s2 = set(s)
            for bod in bods:
                self.assertTrue(bod in s2)
                s2.discard(bod)
            self.assertFalse(s2)

            path = testdata.create_file("bodies-url.txt", [w.url("{}.html".format(k)) for k in s])
            bods = Bodies([path])
            s2 = set(s)
            for bod in bods:
                self.assertTrue(bod in s2)
                s2.discard(bod)
            self.assertFalse(s2)

    def test_url_arg(self):
        with Webserver.start({"bodies-url-file.html": ["<p>text</p>"]}) as w:
            bods = Bodies([w.url("bodies-url-file.html")])
            for bod in bods:
                self.assertEqual("<p>text</p>", bod)

    def test_html_file(self):
        path = testdata.create_file("bodies-html.txt", [
            "<p>text</p>",
        ])
        bods = Bodies([path])
        for bod in bods:
            self.assertEqual("<p>text</p>", bod)

    def test_html_arg(self):
        bods = Bodies(["<p>text</p>"])
        for bod in bods:
            self.assertEqual("<p>text</p>", bod)

    def test_request_cache(self):
        with Webserver.start({"cached.html": ["<p>text</p>"]}) as w:
            bods = Bodies([w.url("cached.html")])
            bods.clear_cache()

            for bod in bods:
                self.assertEqual("<p>text</p>", bod)

            for bod in bods:
                self.assertEqual("<p>text</p>", bod)


class SelectorTest(TestCase):
    def test_contains(self):
        s = Selector("a:contains(Download)->href")
        self.assertEqual("a", s.selector)
        self.assertEqual("Download", s.contains)
        self.assertEqual([{"attrs": ["href"]}], s.columns)

    def test_startswith(self):
        s = Selector("a[data|=foo]->href")
        self.assertEqual("a[data|=foo]", s.selector)
        self.assertEqual([{"attrs": ["href"]}], s.columns)

    def test_comma(self):
        s = Selector("a->href,class,title")
        self.assertEqual([{"attrs": ["href"]}, {"attrs": ["class"]}, {"attrs": ["title"]}], s.columns)

    def test_format(self):
        s = Selector("a->http://example.com{href},boom {title}")
        self.assertEqual([
            {"attrs": ["href"], "format_str": "http://example.com{href}"},
            {"attrs": ["title"], "format_str": "boom {title}"},
        ], s.columns)

    def test_inner(self):
        s = Selector("a->innerHTML,innerText")
        rows = list(s.map("<a href=\"...\">This <emphasis>is</emphasis> the <strong>text</strong></a>"))
        self.assertEqual("This <emphasis>is</emphasis> the <strong>text</strong>", rows[0][0])
        self.assertEqual("This is the text", rows[0][1])

