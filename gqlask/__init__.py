
__all__ = ['__version__', 'GraphqlResolver', 'GraphqlSchema', 'CustomScalar']
__version__ = '0.1'

import sys
from gqlask.scalar import CustomScalar
from gqlask.schema import GraphqlResolver, GraphqlSchema

python_major_version = sys.version_info[0]
python_minor_version = sys.version_info[1]

if python_major_version != 3 or python_minor_version < 6:
    err_msg = 'because of zappa, gqlask only support Python >=3.6'
    raise RuntimeError(err_msg)
