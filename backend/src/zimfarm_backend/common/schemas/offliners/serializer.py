from enum import Enum
from types import UnionType
from typing import Annotated, Any, Union, get_args, get_origin

from pydantic import AnyUrl, BaseModel, EmailStr, SecretStr


def get_base_type(field_type: Any) -> Any:
    """Extract the base type from Annotated types and other complex types."""
    origin = get_origin(field_type)

    # Handle Annotated types (e.g., Annotated[int, Field(gt=0)])
    if origin is Annotated:
        args = get_args(field_type)
        if args:
            # The first argument is the base type
            return get_base_type(args[0])

    # Handle Union types (e.g., str | None)
    if origin is Union or origin is UnionType:
        # Remove None from the union to get the actual type
        non_none_types = [arg for arg in get_args(field_type) if arg is not type(None)]
        if len(non_none_types) == 1:
            return get_base_type(non_none_types[0])
        else:
            # For complex unions, default to str
            return str

    # Return the type as-is if it's not a special type
    return field_type


def get_field_type(field_type: Any) -> str:
    """Determine the type string for a field based on its type annotation."""
    # Get the base type first
    base_type = get_base_type(field_type)

    # Handle basic types
    if base_type is str:
        return "string"
    elif base_type is int:
        return "integer"
    elif base_type is float:
        return "float"
    elif base_type is bool:
        return "boolean"
    elif base_type is AnyUrl:
        return "url"
    elif base_type is EmailStr:
        return "email"
    elif base_type is SecretStr:
        return "string"
    elif isinstance(base_type, type) and issubclass(base_type, Enum):
        return "string-enum"

    # Handle list types
    origin = get_origin(base_type)
    if origin is list:
        args = get_args(base_type)
        if args:
            element_type = args[0]
            return "list-of-" + get_field_type(element_type)
        return "list-of-string"

    return "string"


def get_enum_choices(field_type: Any) -> list[str]:
    """Extract choices from an enum field."""
    # Get the base type first
    base_type = get_base_type(field_type)

    if isinstance(base_type, type) and issubclass(base_type, Enum):
        return [choice.value for choice in base_type]

    # Handle Union types with enums
    origin = get_origin(field_type)
    if origin is Union or origin is UnionType:
        args = get_args(field_type)
        for arg in args:
            if arg is not type(None):  # Skip None
                # Check if the arg is an enum directly
                if isinstance(arg, type) and issubclass(arg, Enum):
                    return [choice.value for choice in arg]

                arg_origin = get_origin(arg)
                if arg_origin is list:
                    arg_args = get_args(arg)
                    if arg_args:
                        element_type = arg_args[0]
                        return get_enum_choices(element_type)

                elif get_origin(arg) is Annotated:
                    base_arg_type = get_base_type(arg)
                    if isinstance(base_arg_type, type) and issubclass(
                        base_arg_type, Enum
                    ):
                        return [choice.value for choice in base_arg_type]

    # Handle list types with enums
    if origin is list:
        args = get_args(field_type)
        if args:
            element_type = args[0]
            # Check if the list element is an enum
            if isinstance(element_type, type) and issubclass(element_type, Enum):
                return [choice.value for choice in element_type]
            # Check if the list element is an Annotated type that might be an enum
            elif get_origin(element_type) is Annotated:
                base_element_type = get_base_type(element_type)
                if isinstance(base_element_type, type) and issubclass(
                    base_element_type, Enum
                ):
                    return [choice.value for choice in base_element_type]

    return []


def is_secret(field_type: Any) -> bool:
    """Determine if a field contains secret information."""
    return get_base_type(field_type) == SecretStr


def schema_to_flags(schema_class: type[BaseModel]) -> dict[str, list[dict[str, Any]]]:
    """
    Convert an offliner schema class to the flags format.

    Args:
        schema_class: The schema class to convert

    Returns:
        Dictionary with 'flags' key containing list of flag objects
    """
    flags: list[dict[str, Any]] = []

    # Get the model fields
    model_fields = schema_class.model_fields

    for field_name, field_info in model_fields.items():
        # Skip the offliner_id field as it's not a configurable flag
        if field_name == "offliner_id":
            continue
        field_type = field_info.annotation
        field_alias = field_info.alias or field_name

        # Get field metadata
        title = getattr(field_info, "title", field_name)
        description = getattr(field_info, "description", "")

        # Determine if field is required
        required = field_info.is_required()

        # Determine field type
        field_type_str = get_field_type(field_type)

        # Get enum choices if applicable
        choices = get_enum_choices(field_type)

        # Check if field is secret
        secret = is_secret(field_type)

        # Build flag object
        flag_obj = {
            "data_key": field_alias,
            "description": description,
            "key": field_alias,
            "label": title,
            "required": required,
            "type": field_type_str,
        }

        # Add choices if available
        if choices:
            flag_obj["choices"] = choices

        # Add secret flag if applicable
        if secret:
            flag_obj["secret"] = True

        flags.append(flag_obj)

    return {"flags": flags}
