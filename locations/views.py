#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods
from rapidsms.utils import render_to_response, web_message
from rapidsms.conf import settings
from .forms import *
from .models import *
from .tables import *


def _breadcrumbs(location=None, first_caption="Planet Earth"):
    """
    Return the breadcrumb trail leading to ``location``. To avoid the
    trail being empty when browsing the entire world, the caption of the
    first crumb is hard coded.
    """

    breadcrumbs = [(first_caption, reverse(locations))]

    if location is not None:
        for loc in location.path:
            type = ContentType.objects.get_for_model(loc)
            url = reverse(locations, args=(loc.uid,))
            breadcrumbs.append((loc.name, url))

    return breadcrumbs


class LocationTypeStub(object):
    """
    This is a shim class, to encapsulate the nested type/location
    structure, and keep the code out of the template. It's not useful
    anywhere else, so I haven't moved it into a template tag.
    """

    def __init__(self, type, req, loc):
        self._type = type
        self._req = req
        self._loc = loc

    def content_type(self):
        return ContentType.objects.get_for_model(
            self._loc)

    def prefix(self):
        return self._type._meta.module_name + "-"

    def table(self):
        return LocationTable(
            self.locations(),
            request=self._req,
            prefix=self.prefix())

    def locations(self):
        if self._loc is not None:
            return self._type.objects.filter(
                parent_type=self.content_type(),
                parent_id=self._loc.pk)

        else: 
            return self._type.objects.filter(
                parent_type=None)

    def is_empty(self):
        return self.locations().count() == 0


@require_GET
def locations(req, location_uid=None):
    location = Location.get_for_uid(location_uid)\
        if location_uid else None

    types = [
        LocationTypeStub(type, req, location)
        for type in Location.subclasses()]

    return render_to_response(req,
        "locations/dashboard.html", {
            "location_types": types,
            "breadcrumbs": _breadcrumbs(location),

            # from rapidsms.contrib.locations.settings
            "default_latitude":  settings.MAP_DEFAULT_LATITUDE,
            "default_longitude": settings.MAP_DEFAULT_LONGITUDE,

            # if there are no locationtypes, then we should display a
            # big error, since this app is useless without them.
            "no_location_types": (len(types) == 0)
         }
     )


@require_http_methods(["GET", "POST"])
def edit_location(req, location_type_slug, location_pk):
    loc_type = get_object_or_404(LocationType, slug=location_type_slug)
    location = get_object_or_404(Location, pk=location_pk)

    if req.method == "GET":
        return render_to_response(req,
            "locations/location_form.html", {
                "active_location_type_tab": loc_type.pk,
                "location": location,

                # redirect back to this view to save (below)
                "save_url": reverse("edit_location", kwargs={
                    "location_type_slug": location_type_slug,
                    "location_pk": location_pk }),

            # is the map visible? default to 0 (hidden)
            # since the map makes everything very slow
            "show_map": int(req.GET.get("map", 0)) })

    elif req.method == "POST":
        # if DELETE was clicked... delete
        # the object, then and redirect
        if req.POST.get("delete", ""):
            pk = location.pk
            location.delete()

            return web_message(req,
                "Location %d deleted" % (pk),
                link=reverse("locations_dashboard"))

        # otherwise, just update the object
        # and display the success message
        else:
            
            location = update_via_querydict(location, req.POST)
            location.save()

            return web_message(req,
                "Location %d saved" % (location.pk),
                link=reverse("locations_dashboard"))


@require_http_methods(["GET", "POST"])
def add_location(req, location_type_slug):
    loc_type = get_object_or_404(LocationType, slug=location_type_slug)

    if req.method == "GET":
        return render_to_response(req,
            "locations/location_form.html", {
                "active_location_type_tab": loc_type.pk,

                # redirect back to this view to save (below)
                "save_url": reverse("add_location", kwargs={
                    "location_type_slug": location_type_slug}),

                # is the map visible? default to 1 (visible),
                # since i almost always want to set the location
                "show_map": int(req.GET.get("map", 1)) })

    elif req.method == "POST":
        location = insert_via_querydict(Location, req.POST, { "type": loc_type })
        location.save()
        
        return web_message(req,
            "Location %d saved" % (location.pk),
            link=reverse("locations_dashboard"))
