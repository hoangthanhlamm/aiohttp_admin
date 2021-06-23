import trafaret as t
from trafaret.contrib.rfc_3339 import DateTime


def build_field(key, value, relations=None):
    extra = None
    name = key
    if isinstance(value, t.Int):
        v = "number"
    elif isinstance(value, (t.String, t.URL)):
        v = "string"
    elif isinstance(value, t.Email):
        v = "email"
    elif isinstance(value, t.Float):
        v = "float"
    elif isinstance(value, t.Enum):
        v = "choice"
    elif isinstance(value, (t.Dict, t.List)):
        v = "json"
    elif isinstance(value, (t.Bool, t.StrBool)):
        v = "boolean"
    elif isinstance(value, DateTime):
        v = "datetime"
    else:
        v = "string"
    return name, v, extra
