"""
Custom Flask-RESTX swagger fields not covered by the built-in field types.
"""

from flask_restx import fields


class NullableString(fields.String):
    """A Swagger string field whose JSON-schema type also accepts ``null``.

    Flask-RESTX's ``RESTX_VALIDATE = True`` auto-validates request bodies
    against the ``ns.model(...)`` swagger definition *before* the Marshmallow
    schema ever runs. A plain ``fields.String`` generates ``"type": "string"``,
    which rejects an explicit ``null`` (used to clear an optional field) with
    a 400 before the Marshmallow schema — which already allows ``None`` —
    gets a chance to validate it. Swagger 2.0 has no native "nullable"
    keyword, but the underlying `jsonschema` validator accepts a list of
    types, so ``["string", "null"]`` works correctly.
    """

    __schema_type__ = ["string", "null"]
