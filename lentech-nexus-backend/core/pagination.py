from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Standard pagination used across list endpoints.

    Clients may request a larger page with `?page_size=` up to `max_page_size`
    to keep responses bounded.
    """

    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100
