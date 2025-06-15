from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10
    max_page_size = 100