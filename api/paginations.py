from rest_framework.pagination import PageNumberPagination
from urllib.parse import urlparse, parse_qs
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NextPageNumberPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_page_number(self, request, paginator):
        """Extract the page number from the request and paginator."""
        page_number = request.query_params.get(self.page_query_param, 1)
        return page_number

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_page_number(self.request, self.page.paginator),  # Fix here
            'previous': self.get_page_number(self.request, self.page.paginator),  # Fix here
            'results': data
        })
    