from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin

class RedirectSlash(MiddlewareMixin):
    def process_request(self, request):
        if '/admin' in request.path:
            if request.path[-1] != '/':
                url = request.path + '/'
                if request.META['QUERY_STRING']:
                    url += '?%s' % request.META['QUERY_STRING']
                return HttpResponsePermanentRedirect(url)
        elif request.path != '/':
            if request.path[-1] == '/':
                url = request.path[:-1]
                if request.META['QUERY_STRING']:
                    url += '?%s' % request.META['QUERY_STRING']
                return HttpResponsePermanentRedirect(url)
