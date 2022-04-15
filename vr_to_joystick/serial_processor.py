from collections import deque
from dataclasses import dataclass
from typing import Any

from vr_to_joystick.nodes.value_generator import ValueConsumer, ValueGenerator


@dataclass
class SerialProcessor:
    root_node: ValueGenerator[Any]

    def process_for_tick(self, tick: int) -> None:
        nodes_to_analyze = deque[ValueConsumer]()
        nodes_to_analyze.append(self.root_node)

        while len(nodes_to_analyze) > 0:
            node = nodes_to_analyze.popleft()
            if node.dependencies_updated_for_tick(tick):
                node.update(tick)

                if isinstance(node, ValueGenerator):
                    for child in node.bound_children:
                        nodes_to_analyze.append(child)
