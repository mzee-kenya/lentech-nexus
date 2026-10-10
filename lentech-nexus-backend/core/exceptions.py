from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Normalize DRF error responses without leaking internals.

    Unhandled (non-API) exceptions are left to Django so that, with DEBUG off,
    they produce a generic 500 response rather than a stack trace.
    """

    response = exception_handler(exc, context)

    if response is not None and isinstance(response.data, dict):
        response.data.setdefault('status_code', response.status_code)

    return response
