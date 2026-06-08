from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'link' : {
                'next' : self.get_next_link(),
                'previous' : self.get_previous_link()
                
            },
            'pagination' : {
                'current_page' : self.page.number,
                'page_size' : self.page.paginator.per_page,
                'total_items' : self.page.paginator.count,
                'total_pages' : self.page.paginator.num_pages,
                'has_next' : self.page.has_next(),
                'has_previous' : self.page.has_previous()
            },
            'results' : data
        })
    


class SmallPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50




class LargePagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500