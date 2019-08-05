from datetime import datetime, timezone
from graphql.language.ast import BooleanValue, StringValue, IntValue, ListValue, ObjectValue, FloatValue


class CustomScalar:
    type_name = None
    description = None

    @staticmethod
    def serialize(value):
        raise NotImplementedError()

    @staticmethod
    def parse_value(value):
        raise NotImplementedError()

    @staticmethod
    def parse_literal(ast):
        raise NotImplementedError()


class JSONScalar(CustomScalar):
    type_name = 'JSON'
    description = """
The `JSON` scalar type represents JSON values as specified by
[ECMA-404](http://www.ecma-international.org/
publications/files/ECMA-ST/ECMA-404.pdf)
"""

    @staticmethod
    def serialize(value):
        return JSONScalar.parse_value(value)

    @staticmethod
    def parse_value(value):
        if isinstance(value, (str, bool, int, float)):
            return value.__class__(value)
        elif isinstance(value, (list, dict)):
            return value
        else:
            return None

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, (StringValue, BooleanValue)):
            return ast.value
        elif isinstance(ast, IntValue):
            return int(ast.value)
        elif isinstance(ast, FloatValue):
            return float(ast.value)
        elif isinstance(ast, ListValue):
            return [JSONScalar.parse_literal(value) for value in ast.values]
        elif isinstance(ast, ObjectValue):
            return {field.name.value: JSONScalar.parse_literal(field.value) for field in ast.fields}
        else:
            return None


def build_datetime_scalar(scalar_name, format, tz: timezone):
    class DatetimeScalar(CustomScalar):
        type_name = scalar_name
        description = f'{type_name} format: {format}'

        @staticmethod
        def serialize(value):
            if isinstance(value, datetime):
                if value.tzinfo != tz:
                    raise ValueError(f'invalid timezone, expected {str(tz)} but got {str(value.tzinfo)}')
                return value.strftime(format)
            return None

        @staticmethod
        def parse_value(value):
            if isinstance(value, str) and value:  # not empty string
                return datetime.strptime(value, format).replace(tzinfo=tz)
            elif isinstance(value, int) and value > 0:
                return datetime.fromtimestamp(value).replace(tzinfo=tz)
            else:
                return None

        @staticmethod
        def parse_literal(ast):
            if isinstance(ast, StringValue):
                return ast.value
            elif isinstance(ast, IntValue):
                return int(ast.value)
            else:
                return None

    return DatetimeScalar


class Base64Scalar(CustomScalar):
    import base64

    type_name = 'Base64'
    description = 'Bae64'

    @staticmethod
    def serialize(value):
        if isinstance(value, bytes):
            return Base64Scalar.base64.b64decode(value)
        return None

    @staticmethod
    def parse_value(value):
        if isinstance(value, str):
            return Base64Scalar.base64.b64encode(value)
        return None

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, StringValue):
            return ast.value
        return None
