__author__ = 'Kael'

from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.view import (
    view_config,
    view_defaults
)


#@view_defaults(renderer='home.pt')
#class TutorialViews:
#    def __init__(self, request):
#        self.request = request

@view_defaults(renderer='home.jinja2')
class HomeView:
    def __init__(self, request):
        self.request = request

    @view_config(route_name='start')
    def start(self):
        return {'': ''}


@view_defaults(renderer='group.jinja2')
class GroupView:
    def __init__(self, request):
        self.request = request

    @view_config(route_name='group')
    def grouplist(self):
        return {'': ''}

@view_defaults(renderer='grouplist.jinja2')
class GrouplistView:
    def __init__(self, request):
        self.request = request

    @view_config(route_name='grouplist')
    def group(self):
        return {'': ''}