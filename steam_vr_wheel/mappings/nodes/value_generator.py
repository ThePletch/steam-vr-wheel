from __future__ import annotations
from abc import abstractmethod
from steam_vr_wheel.mappings.multiton import MultitonNode
from typing import Any, Hashable, TypeVar, Generic

O = TypeVar('O')


class ValueConsumer(metaclass=MultitonNode):
    requirements: set[str] = set()
    dependencies: dict[str, ValueGenerator[Any]]

    def __init__(
        self,
        *,
        dependencies: dict[str, ValueGenerator[Any]] = {}
    ):
        self.dependencies = dependencies
        self._enforce_requirements()

        for gen in self.dependencies.values():
            gen.bind_child(self)

        self.last_tick_update = -1

    # returns any config settings to parameterize instances on, in addition to their init params
    @classmethod
    def _parameterized_on(cls) -> list[Hashable]:
        return []

    def __dependencies_str__(self) -> str:
        if any(self.dependencies):
            return f"({', '.join(['='.join([k, repr(v)]) for k, v in self.dependencies.items()])})"
        
        return ''
    
    def __config_params_str__(self) -> str:
        config_params = self._parameterized_on()
        if any(config_params):
            return f"({', '.join(repr(c) for c in config_params)})"
        
        return ''

    def __repr__(self) -> str:
        return (
            f"[{self.__class__.__name__}{self.__config_params_str__()}{self.__dependencies_str__()}]"
        )
    
    def _enforce_requirements(self) -> None:
        missing_requirements = self.requirements - set(self.dependencies.keys())

        if missing_requirements:
            raise ValueError(
                f"Missing requirements for input mapping {self.__class__.__name__}!\n"
                f"Missing bindings: {', '.join(missing_requirements)}"
            )

    def dependencies_updated_for_tick(self, tick_index: int) -> bool:
        return all(binding.updated_for_tick(tick_index) for binding in self.dependencies.values())

    def updated_for_tick(self, tick_index: int) -> bool:
        return self.last_tick_update == tick_index

    def update(self, tick_index: int) -> None:
        if not self.dependencies_updated_for_tick(tick_index):
            return

        inputs = {key: generator.current_value for key, generator in self.dependencies.items()}

        self.last_tick_update = tick_index

        self.update_with_inputs(inputs)
    
    @abstractmethod
    def update_with_inputs(self, inputs: dict[str, Any]) -> None:
        pass


class ValueGenerator(Generic[O], ValueConsumer):
    current_value: O

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bound_children: list[ValueGenerator[Any]] = []
    
    def bind_child(self, child: ValueGenerator[Any]) -> None:
        self.bound_children.append(child)
    
    def update(self, tick_index: int) -> None:
        super().update(tick_index)

        for child in self.bound_children:
            child.update(tick_index)

    def update_with_inputs(self, inputs: dict[str, Any]) -> None:
        self.current_value = self.generate_output(inputs)
    
    @abstractmethod
    def generate_output(self, inputs: dict[str, Any]) -> O:
        pass