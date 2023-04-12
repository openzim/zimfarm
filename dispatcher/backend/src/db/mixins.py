# temporary mixin for mypy type checker,
# see https://docs.sqlalchemy.org/en/20/orm/dataclasses.html

import typing

if typing.TYPE_CHECKING:

    class MappedAsDataclass:
        """Mixin class which works in the same way as
        :class:`_orm.MappedAsDataclass`,
        but does not include :pep:`681` directives.

        """

        def __init__(self, *arg: typing.Any, **kw: typing.Any):
            pass

else:
    from sqlalchemy.orm import MappedAsDataclass  # noqa: F401
