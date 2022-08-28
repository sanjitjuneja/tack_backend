import logging
from collections import OrderedDict

from rest_framework.pagination import CursorPagination

from django.db.models import QuerySet
from django.utils.encoding import force_str
from rest_framework.pagination import LimitOffsetPagination, _positive_int
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework.compat import coreapi, coreschema
from rest_framework.utils.urls import replace_query_param


class LastObjectPagination(LimitOffsetPagination):
    last_obj_query_param = 'last_object'
    last_obj_query_description = _('The last object of current results')

    def __init__(self):
        self.request = None
        self.limit = None
        self.offset = None
        self.count = None
        self.last_object = None

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.count = self.get_count(queryset)
        self.offset = self.get_offset(request)
        self.last_object = self.get_last_object(request)
        if self.last_object:
            ids = list(queryset.values_list('id', flat=True))
            self.offset = ids.index(self.last_object) + 1

        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])

    def get_paginated_response(self, data):
        objs = []
        for obj in data:
            objs.append(obj['id'])
        logging.getLogger().warning(f"{objs = }")
        last_object = data[-1]['id'] if len(data) > 0 else None
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('last_object', last_object),
            ('results', data)
        ]))

    def get_last_object(self, request):
        try:
            return _positive_int(
                request.query_params[self.last_obj_query_param],
            )
        except (KeyError, ValueError):
            return 0

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.limit_query_param,
                required=False,
                location='query',
                schema=coreschema.Integer(
                    title='Limit',
                    description=force_str(self.limit_query_description)
                )
            ),
            coreapi.Field(
                name=self.offset_query_param,
                required=False,
                location='query',
                schema=coreschema.Integer(
                    title='Offset',
                    description=force_str(self.offset_query_description)
                )
            ),
            coreapi.Field(
                name=self.last_obj_query_param,
                required=False,
                location='query',
                schema=coreschema.Integer(
                    title='Last Object',
                    description='Last Object ID in Queryset'
                )
            )
        ]

    def get_schema_operation_parameters(self, view):
        parameters = [
            {
                'name': self.limit_query_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.limit_query_description),
                'schema': {
                    'type': 'integer',
                },
            },
            {
                'name': self.offset_query_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.offset_query_description),
                'schema': {
                    'type': 'integer',
                },
            },
            {
                'name': self.last_obj_query_param,
                'required': False,
                'in': 'query',
                'description': 'Last Object ID in queryset',
                'schema': {
                    'type': 'integer',
                }
            }
        ]
        return parameters

    def get_next_link(self):
        if self.offset + self.limit >= self.count:
            return None

        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        offset = self.offset + self.limit
        # last_object = self.last_object + self.limit + 1
        # url = replace_query_param(url, self.last_obj_query_param, last_object)
        return replace_query_param(url, self.offset_query_param, offset)


class CursorSetPagination(CursorPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    ordering = 'creation_time'
