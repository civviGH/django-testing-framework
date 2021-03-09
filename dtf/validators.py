
import jsonschema

from django.core import exceptions
from django.utils.deconstruct import deconstructible

@deconstructible
class JSONSchemaValidator:

    def __init__(self, schema):
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        self.json_validator = validator_cls(schema)

    def __call__(self, value):
        errors = [
            exceptions.ValidationError(error.message.replace("\\\\", "\\"), code="jsonschema")
            for error in self.json_validator.iter_errors(value)
        ]
        if errors:
            raise exceptions.ValidationError(errors)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.schema == other.schema
