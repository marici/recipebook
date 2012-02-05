# coding: utf-8
"""
The MIT License

Copyright (c) 2009 Marici, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
from django.http import HttpResponseRedirect, get_host

class SSLRedirectMiddleware(object):
    """
    request.is_secure() がTrueの場合、リダイレクト先のURLをHTTPSプロトコルに書き換えます。
    """
    def process_response(self, request, response):
        if isinstance(response, HttpResponseRedirect) and request.is_secure():
            path = response["Location"]
            if path.startswith("/"):
                response["Location"] = "https://%s%s" % (get_host(request), 
                    path)
            elif path.startswith("http:"):
                if get_host(request) in path:
                    response["Location"] = path.replace("http:", "https:")
            else:
                response["Location"] = "https://%s%s%s" % (get_host(request),
                    request.path_info, path)
        return response
