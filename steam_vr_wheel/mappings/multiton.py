from __future__ import annotations
from collections import defaultdict
import logging
from typing import Any, Hashable, Protocol

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")


class Parameterized(Protocol):
    @classmethod
    def _parameterized_on(cls) -> list[Hashable]: ...


# metaclass that implements the multiton pattern, i.e. initializing a class with the same arguments twice will produce the same object in memory,
# rather than two copies of that object. this ensures that axis computation steps don't need to repeat themselves, which should allow more functionally-defined
# controller mappings without duplicate computation.
class MultitonNode(type):
    __instances: dict[str, dict[int, Parameterized]] = defaultdict(dict)

    # type: ignore # mypy gets confused by metaclass typing
    def __call__(cls: type[Parameterized], *args: Any, **kwargs: dict[str, Any]) -> Parameterized:
        hashed_args = [hash(arg) for arg in args]
        hashed_kwargs = [(key, hash(value)) for key, value in kwargs.items()]

        hash_tuple = (*hashed_args, *cls._parameterized_on(), *hashed_kwargs)
        repr_args = [*[repr(p) for p in cls._parameterized_on()], *
                     [f'{key}: {repr(value)}' for key, value in kwargs.items()]]
        instance_hash = hash(hash_tuple)
        try:
            new_instance = MultitonNode.__instances[cls.__name__][instance_hash]
            logger.debug(f"Found cached instance of {cls.__name__} with args {', '.join(repr_args)}, returning")

        except KeyError:
            logger.debug(f"Cache miss for {cls.__name__} with args {', '.join(repr_args)}, building new instance")

            # type: ignore # mypy gets confused by metaclass typing
            new_instance = super(MultitonNode, cls).__call__(*args, **kwargs)
            MultitonNode.__instances[cls.__name__][instance_hash] = new_instance

        return new_instance
