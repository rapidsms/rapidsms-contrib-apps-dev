#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse
from rapidsms.webui.utils import render_to_response

def index(req):
    return render_to_response(req, "training/index.html")
