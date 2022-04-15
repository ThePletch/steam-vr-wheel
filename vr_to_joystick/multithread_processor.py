from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any

from vr_to_joystick.nodes.value_generator import ValueConsumer, ValueGenerator


def handler(tick: int, node_analysis_queue: Queue[ValueConsumer]) -> None:
    while not node_analysis_queue.empty():
        node = node_analysis_queue.get(block=True, timeout=1)
        print(f"Is {repr(node)} ready?")
        if node.dependencies_updated_for_tick(tick):
            print(f"{repr(node)} is ready.")
            node.update(tick)

            if isinstance(node, ValueGenerator):
                for child in node.bound_children:
                    node_analysis_queue.put(child)
        else:
            print(f"{repr(node)} is not ready.")

        node_analysis_queue.task_done()


####
# Doesn't actually parallelize anything due to Python's GIL preventing
#   true multithreading with shared memory.
# Until conversion to Cython or similar, recommended to use SerialProcessor,
#   since the overhead of handling threads makes this slower than serial.
####
@dataclass
class MultithreadProcessor:
    root_node: ValueGenerator[Any]
    handler_count: int = 2

    def process_for_tick(self, tick: int) -> None:
        node_analysis_queue = Queue[ValueConsumer]()
        node_analysis_queue.put(self.root_node)

        handlers = [
            Thread(target=handler, args=[tick, node_analysis_queue])
            for _ in range(self.handler_count)
        ]

        print("starting handlers")
        for t in handlers:
            t.start()

        node_analysis_queue.join()

        for t in handlers:
            t.join()
