"""分页封装 PageResult（G5）

请求参数：page(默认1)、size(默认10)
返回字段：total、pages、current、records
"""
from rest_framework.pagination import PageNumberPagination as DRFPageNumberPagination
from rest_framework.response import Response


class PageNumberPagination(DRFPageNumberPagination):
    page_query_param = "page"
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        size = self.get_page_size(self.request) or self.page_size
        pages = (total + size - 1) // size if size > 0 else 0
        return Response({
            "code": 200,
            "msg": "操作成功",
            "data": {
                "total": total,
                "pages": pages,
                "current": self.page.number,
                "records": data,
            },
        })
