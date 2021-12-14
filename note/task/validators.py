from cerberus import Validator
from django.core.exceptions import ValidationError


class _TaskChecklistValidator(Validator):
    schema = {
        "list_type": {"type": "string"},
        "item_list": {
            "type": "list",
            "check_with": "valid_item_list_priority",
            "schema": {
                "type": "dict",
                "schema": {
                    "name": {"type": "string", "required": True},
                    "marked": {"type": "boolean", "required": True},
                    "priority": {"type": "integer", "required": True}
                }
            }
        }
    }

    def _check_with_valid_item_list_priority(self, field, value):
        priorities = [x["priority"] for x in self.document["item_list"]]
        if len(priorities) != len(set(priorities)):
            self._error(field, "item_list has items with same priority value")


def validate_checklist_schema(value):
    if value is not None:
        validator = _TaskChecklistValidator(_TaskChecklistValidator.schema)
        if not validator.validate(value):
            raise ValidationError("Error while saving checklist: ")
