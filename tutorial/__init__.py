__author__ = 'Kael'
# test_task_chat
from pyramid.config import Configurator


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.add_route('grouplist', '/grouplist')
    config.add_route('start', '/start')
    config.add_route('group', '/group')
    config.scan('.views')
    return config.make_wsgi_app()