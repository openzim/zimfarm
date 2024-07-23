from typing import Any, Type


def raise_if_none(
    object_to_check: Any, exception_class: Type[Exception], *exception_args: object
) -> None:
    """Checks if the `object_to_check` argument is None.
    If it is None, then raises a new object of type `exception_class` initialized
    with `exception_args`.

    Arguments:
    object_to_check -- the object to check if None or not
    exception_class -- the exception to create and raise if the object_to_check is None
    exception_args -- the args to create the exception
    """
    raise_if(object_to_check is None, exception_class, *exception_args)


def raise_if(
    condition: bool, exception_class: Type[Exception], *exception_args: object
) -> None:
    """Checks if the `condition` argument is True.
    If it is True, then it raises the exception.

    Arguments:
    condition -- the condition to check if True
    exception_class -- the exception to create and raise if the condition is True
    exception_args -- the args to create the exception
    """
    if condition:
        raise exception_class(*exception_args)


def cleanup_value(value: Any) -> Any:
    """Remove unwanted characters before inserting / updating in DB"""
    if isinstance(value, str):
        return value.replace("\u0000", "")
    return value
