from django.http import HttpResponse

class AllowJSONPCallback(object):
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        request = args[0]
        callback = request.GET.get('callback')
        if callback:
            response = self.f(*args, **kwargs)
            if response.content[0] not in ['"', '[', '{'] \
                    or response.content[-1] not in ['"', ']', '}']:
                response.content = '"%s"' % response.content
            response.content = "%s(%s)" % (callback, response.content)
            response['Content-Type'] = 'application/javascript'
        else:
            response = self.f(*args, **kwargs)
        return response
