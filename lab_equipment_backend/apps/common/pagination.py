"""分页封装（对齐《后端API接口文档》1.3 通用分页响应结构）

请求参数：page(默认1)、pageSize(默认10)
返回字段：data = { list, total, page, pageSize, totalPages }
"""
from rest_framework.pagination import PageNumberPagination as DRFPageNumberPagination
from rest_framework.response import Response

from apps.common.response import now_ms


class PageNumberPagination(DRFPageNumberPagination):
    page_query_param = "page"
    page_size = 10
    page_size_query_param = "pageSize"
    max_page_size = 100

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        size = self.get_page_size(self.request) or self.page_size
        total_pages = (total + size - 1) // size if size > 0 else 0
        return Response({
            "code": 200,
            "message": "操作成功",
            "data": {
                "list": data,
                "total": total,
                "page": self.page.number,
                "pageSize": size,
                "totalPages": total_pages,
            },
            "timestamp": now_ms(),
        })


def paginate(request, queryset, serializer_cls):
    """对 queryset 分页并返回统一分页 Response（函数式视图共用）"""
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serializer_cls(page, many=True).data)
