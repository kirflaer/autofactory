import time
from typing import Callable
from django.core.cache import cache
from rest_framework.exceptions import APIException
from rest_framework.response import Response


def cache_api(request, body: dict, function: Callable, *args, **kwargs):
    request_id = request.stream.headers.get('id')
    if request.user.settings.use_cache and request_id:
        cache_data = cache.get(request_id)
        ttl = request.user.settings.ttl_cache
        if not cache_data:
            cache_data = {'status': 'wait', 'status_code': 102, 'body': body}
            cache.set(request_id, cache_data, ttl)

            try:
                function(request, *args, **kwargs)
                cache_data['body'] = body
                cache_data['status'] = 'done'
                cache_data['status_code'] = 200
                time.sleep(20)
            except APIException as e:
                cache_data['status'] = 'error'
                cache_data['body'] = {'detail': e.args[0]}
                cache_data['status_code'] = e.status_code

            cache.set(request_id, cache_data, ttl)

        return Response(cache_data['body'], status=cache_data['status_code'])
    else:
        return function(request, *args, **kwargs)
