"""
NOTE: named xblock_api to prevent name clashes with imports from xblock.
"""

from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.exceptions import NotFound, ImmediateHttpResponse
from tastypie.http import HttpNotImplemented

from tastypie.resources import Resource
from django.conf.urls import url


from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from xmodule.course_module import CourseDescriptor

from .utils import get_xblock_metadata


# Only return a subset of the data
METADATA_WHITELIST = ['display_name']


class XBlockObject(object):
    def __init__(self):
        self.location = ''
        self.category = ''
        self.metadata = {}
        self.data = ''


class XBlockResource(Resource):
    location = fields.CharField(attribute='location')
    category = fields.CharField(attribute='category')
    data = fields.CharField(attribute='data')
    metadata = fields.DictField(attribute='metadata')

    class Meta:
        resource_name = 'xblock'
        object_class = XBlockObject
        authentication = Authentication()
        authorization = Authorization()
        include_resource_uri = False
        allowed_methods = ['get']

    def prepend_urls(self):
        """
        The tastypie default url pattern don't like our locations, what with
        their strange chars (like ':').  Add another url pattern that looks
        similar, but is less restrictive.
        """
        return [
            url(r"^(?P<resource_name>{0})/(?P<pk>[\w\d:/_.-]+)/$".format(
                self._meta.resource_name),
                self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def obj_get(self, request=None, **kwargs):
        location = kwargs['pk']

        real_loc = Location(location)
        hack_list = ['video', 'html']
        if real_loc.category not in hack_list:
            raise ImmediateHttpResponse(HttpNotImplemented())

        store = modulestore()
        try:
            xblock = store.get_item(location)
        except ItemNotFoundError:
            raise NotFound

        # @TODO: Check for authorization

        # TODO: make this a real thing
        result = XBlockObject()

        result.metadata = get_xblock_metadata(xblock, METADATA_WHITELIST)
        result.data = xblock.data

        result.location = xblock.location.url()
        result.category = xblock.location.category
        return result
