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
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from models import Document

def index(request):
    roots = Document.objects.get_roots()
    d = {"roots":roots}
    return render_to_response("documents/index.html",
                              d, RequestContext(request))

def show(request, label=None, format=None):
    if format == "plain":
        return show_plain(request, label)
    document = get_object_or_404(Document, label=label)
    siblings = Document.objects.get_children(document.parent)
    d = {"document":document,
         "parent":document.parent,
         "siblings":siblings,
         "children":document.children}
    return render_to_response("documents/document.html",
                              d, RequestContext(request))
    
def show_plain(request, label=None):
    document = get_object_or_404(Document, label=label)
    return render_to_response("documents/document_plain.html",
                              {"document":document}, 
                              RequestContext(request))
    
