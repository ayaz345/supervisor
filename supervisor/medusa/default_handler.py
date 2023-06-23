# -*- Mode: Python -*-
#
#       Author: Sam Rushing <rushing@nightmare.com>
#       Copyright 1997 by Sam Rushing
#                                                All Rights Reserved.
#

RCS_ID = '$Id: default_handler.py,v 1.8 2002/08/01 18:15:45 akuchling Exp $'

# standard python modules
import mimetypes
import re
import stat

# medusa modules
import supervisor.medusa.http_date as http_date
import supervisor.medusa.http_server as http_server
import supervisor.medusa.producers as producers

from supervisor.medusa.util import html_repr

unquote = http_server.unquote

# This is the 'default' handler.  it implements the base set of
# features expected of a simple file-delivering HTTP server.  file
# services are provided through a 'filesystem' object, the very same
# one used by the FTP server.
#
# You can replace or modify this handler if you want a non-standard
# HTTP server.  You can also derive your own handler classes from
# it.
#
# support for handling POST requests is available in the derived
# class <default_with_post_handler>, defined below.
#

from supervisor.medusa.counter import counter

class default_handler:

    valid_commands = ['GET', 'HEAD']

    IDENT = 'Default HTTP Request Handler'

    # Pathnames that are tried when a URI resolves to a directory name
    directory_defaults = [
            'index.html',
            'default.html'
            ]

    default_file_producer = producers.file_producer

    def __init__ (self, filesystem):
        self.filesystem = filesystem
        # count total hits
        self.hit_counter = counter()
        # count file deliveries
        self.file_counter = counter()
        # count cache hits
        self.cache_counter = counter()

    hit_counter = 0

    def __repr__ (self):
        return '<%s (%s hits) at %x>' % (
                self.IDENT,
                self.hit_counter,
                id (self)
                )

    # always match, since this is a default
    def match (self, request):
        return 1

    # handle a file request, with caching.

    def handle_request(self, request):

        if request.command not in self.valid_commands:
            request.error (400) # bad request
            return

        self.hit_counter.increment()

        path, params, query, fragment = request.split_uri()

        if '%' in path:
            path = unquote (path)

        # strip off all leading slashes
        while path and path[0] == '/':
            path = path[1:]

        if self.filesystem.isdir (path):
            if path and path[-1] != '/':
                request['Location'] = f'http://{request.channel.server.server_name}/{path}/'
                request.error (301)
                return

            # we could also generate a directory listing here,
            # may want to move this into another method for that
            # purpose
            found = 0
            for default in self.directory_defaults:
                p = path + default
                if self.filesystem.isfile (p):
                    path = p
                    found = 1
                    break
            if not found:
                request.error (404) # Not Found
                return

        elif not self.filesystem.isfile (path):
            request.error (404) # Not Found
            return

        file_length = self.filesystem.stat (path)[stat.ST_SIZE]

        ims = get_header_match (IF_MODIFIED_SINCE, request.header)

        length_match = 1
        if ims:
            if length := ims.group(4):
                try:
                    length = int(length)
                    if length != file_length:
                        length_match = 0
                except:
                    pass

        ims_date = http_date.parse_http_date (ims.group (1)) if ims else 0
        try:
            mtime = self.filesystem.stat (path)[stat.ST_MTIME]
        except:
            request.error (404)
            return

        if length_match and ims_date:
            if mtime <= ims_date:
                request.reply_code = 304
                request.done()
                self.cache_counter.increment()
                return
        try:
            file = self.filesystem.open (path, 'rb')
        except IOError:
            request.error (404)
            return

        request['Last-Modified'] = http_date.build_http_date (mtime)
        request['Content-Length'] = file_length
        self.set_content_type (path, request)

        if request.command == 'GET':
            request.push (self.default_file_producer (file))

        self.file_counter.increment()
        request.done()

    def set_content_type(self, path, request):
        typ, encoding = mimetypes.guess_type(path)
        request['Content-Type'] = typ if typ is not None else 'text/plain'

    def status(self):
        return producers.simple_producer(
            (
                (
                    (
                        (
                            f'<li>{html_repr(self)}<ul>'
                            + f'  <li><b>Total Hits:</b> {self.hit_counter}'
                        )
                        + f'  <li><b>Files Delivered:</b> {self.file_counter}'
                    )
                    + f'  <li><b>Cache Hits:</b> {self.cache_counter}'
                )
                + '</ul>'
            )
        )

# HTTP/1.0 doesn't say anything about the "; length=nnnn" addition
# to this header.  I suppose its purpose is to avoid the overhead
# of parsing dates...
IF_MODIFIED_SINCE = re.compile (
        'If-Modified-Since: ([^;]+)((; length=([0-9]+)$)|$)',
        re.IGNORECASE
        )

USER_AGENT = re.compile ('User-Agent: (.*)', re.IGNORECASE)

CONTENT_TYPE = re.compile (
        r'Content-Type: ([^;]+)((; boundary=([A-Za-z0-9\'\(\)+_,./:=?-]+)$)|$)',
        re.IGNORECASE
        )

get_header = http_server.get_header
get_header_match = http_server.get_header_match

def get_extension(path):
    dirsep = path.rfind('/')
    dotsep = path.rfind('.')
    return path[dotsep+1:] if dotsep > dirsep else ''
