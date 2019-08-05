from gqlask import GraphqlResolver, GraphqlSchema
from enum import Enum


class TEnum(Enum):
    A = 'A'
    B = 'B'


resolver = GraphqlResolver()


@resolver.query()
def hello():
    # raise ValueError('hello')
    return 'hello'


@resolver.query()
def echo(v):
    # raise ValueError(v)
    print(v)
    return v


sdl = """
scalar JSON
schema {
    query: Query
}

type Query {
    hello: String!
    echo(v: T!): T!
}

enum T {
    A
    B
}
"""


def _build_schema():
    schema = GraphqlSchema(sdl=sdl)
    schema.register_resolver(resolver)
    schema.custom_enum('T', TEnum)
    return schema


_gpl_schema = _build_schema()


def exe_graphql(query, variables, context=None, operation_name=None):
    result = _gpl_schema.exe(query, variable_values=variables, context=context, operation_name=operation_name)

    if result.errors:
        errors = []
        for error in result.errors:
            errors.append(str(error))
        result.errors = errors

    return dict(data=result.data, errors=result.errors)


def query():
    q = """
query {
    hello
    echo(v: A)
    __typename
}
    """
    r = exe_graphql(q, {})
    print(r)


if __name__ == '__main__':
    query()
