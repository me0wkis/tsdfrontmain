from rest_framework.pagination import LimitOffsetPagination

class CustomLimitOffsetPagination(LimitOffsetPagination):
    max_limit = 10000
    limit_query_param = 'limit'
    offset_query_param = 'offset'