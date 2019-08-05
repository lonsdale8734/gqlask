from typing import Callable, Type
from types import MethodType
from collections import Hashable
from inspect import signature
from functools import wraps
from datetime import timezone
import graphql
from gqlask.scalar import CustomScalar, JSONScalar, build_datetime_scalar, Base64Scalar

reserved_param = {'_value', '_context', '_info'}


def enum_serialize(self, value):
    if isinstance(value, Hashable):
        enum_value = self._value_lookup.get(value)
        if enum_value:
            return enum_value.name

    return None


def resolver_wrapper(func):
    """ 封装来自于graphql参数 """

    @wraps(func)
    def wrapper(value, info, **kwargs):
        reserved = dict(_value=value, _context=info.context, _info=info)

        filled_kwargs = {}
        extra_kwargs = {}

        for param in signature(func).parameters.values():
            name = param.name

            if name in reserved:  # fill pass-down value
                filled_kwargs[name] = reserved[name]
            elif param.kind == param.VAR_POSITIONAL:
                continue
            elif param.kind == param.VAR_KEYWORD:
                extra_kwargs = kwargs
            elif name in kwargs:
                filled_kwargs[name] = kwargs.pop(name)  # 修正VAR_KEYWORD
            elif param.default == param.empty:
                filled_kwargs[name] = None
            else:
                filled_kwargs[name] = param.default

        return func(**filled_kwargs, **extra_kwargs)

    return wrapper


def _default_resolver(value, info, **_):
    key_ = info.field_name
    if isinstance(value, dict):
        value = value.get(key_, None)
    else:
        value = getattr(value, key_, None)
    return value


class GraphqlResolver:

    def __init__(self):
        self._type_resolvers = {}

    def query(self, name=None) -> Callable:
        def decorator(func: Callable):
            self._register_type('Query', name, func)
            return func
        return decorator

    def mutation(self, name=None) -> Callable:
        def decorator(func: Callable):
            self._register_type('Mutation', name, func)
            return func
        return decorator

    def type(self, type_name, field=None) -> Callable:
        def decorator(func: Callable):
            self._register_type(type_name, field, func)
            return func
        return decorator

    def _register_type(self, type_, field, resolver: Callable):
        field = field or resolver.__name__
        type_fields = self._type_resolvers.get(type_) or {}
        if field in type_fields:
            raise ValueError(f'{field} already registered')

        type_fields[field] = resolver
        self._type_resolvers[type_] = type_fields

    def get_resolvers(self, type_name) -> dict:
        return self._type_resolvers.get(type_name) or {}


class GraphqlSchema:

    def __init__(self, sdl: str = None, path: str = None, tz: timezone = None):
        if not sdl and not path:
            raise ValueError('没有设置SDL或者SDL路径')

        if not sdl:
            with open(path, 'r', encoding='utf-8') as fin:
                sdl = fin.read()

        self._sdl = sdl
        self.schema: graphql.GraphQLSchema = graphql.build_ast_schema(graphql.parse(self._sdl))

        _DateScalar = build_datetime_scalar('Date', '%Y%m%d', tz)
        _DatetimeScalar = build_datetime_scalar('Datetime', '%Y-%m-%d %H:%M:%S', tz)
        _DBDatetimeScalar = build_datetime_scalar('DatetimeMicro', '%Y-%m-%d %H:%M:%S.%f', tz)

        self.custom_scalar(JSONScalar)
        self.custom_scalar(_DateScalar)
        self.custom_scalar(_DatetimeScalar)
        self.custom_scalar(_DBDatetimeScalar)
        self.custom_scalar(Base64Scalar)

    def custom_scalar(self, scalar: Type[CustomScalar]):
        _ScalarType = self.schema.get_type(scalar.type_name)

        if _ScalarType and isinstance(_ScalarType, graphql.GraphQLScalarType):
            _ScalarType.description = scalar.description
            _ScalarType.serialize = scalar.serialize
            _ScalarType.parse_value = scalar.parse_value
            _ScalarType.parse_literal = scalar.parse_literal

        return self

    def custom_enum(self, name, enum):
        _EnumType = self.schema.get_type(name)
        if _EnumType and isinstance(_EnumType, graphql.GraphQLEnumType):
            _EnumType.serialize = MethodType(enum_serialize, _EnumType)
            for value in _EnumType.values:
                value.value = enum[value.name]

    def register_resolver(self, resolver: GraphqlResolver):
        type_map = self.schema.get_type_map()

        for type_name, type_def in type_map.items():
            if type_name.startswith('__') or not isinstance(type_def, graphql.GraphQLObjectType):
                continue

            type_resolvers = resolver.get_resolvers(type_name)
            for field_name, field in type_def.fields.items():
                _resolver = type_resolvers.get(field_name)
                if _resolver:
                    if field.resolver and field.resolver != _default_resolver:
                        raise ValueError(f'{type_name} cannot has duplicated {field_name} resolver')
                    field.resolver = resolver_wrapper(_resolver)
                elif not field.resolver:
                    field.resolver = _default_resolver

        return self

    def export_schema(self):
        return graphql.print_schema(self.schema)

    def exe(self, query, context=None, *, variable_values=None, operation_name=None, raise_error=False):
        """
        1. 当query出现语法错误时，ret.invalid == True, ret.errors记录异常对象
        2. 当resolver内抛出异常时，graqhql会打印异常信息，ret.invalid=False，ret.errors记录异常对象

        :param self:
        :param query: graphql request
        :param context: pass context variables
        :param variable_values: request variable
        :param operation_name: needed for multiple query
        :param raise_error: whether raise error
        :return:
        """

        result = graphql.graphql(self.schema, query,
                                 context_value=context,
                                 variable_values=variable_values,
                                 operation_name=operation_name)

        if result.errors:
            result.errors = [getattr(error, 'original_error', error) for error in result.errors]

            if raise_error:
                raise result.errors[0]

        return result

    def __str__(self):
        return self._sdl
