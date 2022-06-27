from clilib.util.logging import Logging
import threading


class EventManager:
    """
    Store and manage events and handlers. Call your event handler object to trigger an event.
    Example:
    ```
    event_manager = EventManager()
    event_manager.on("my_event", my_event_handler)
    event_manager("my_event", {"my_data": "my_value"})
    ```
    """
    def __init__(self, debug: bool = False):
        self.logger = Logging(log_name="clilib", log_desc="EventManager", debug=debug).get_logger()
        self.event_handlers = {}

    def __call__(self, event_name: str, event_data: dict):
        """
        Call event handlers
        :param event_name: Event name to trigger
        :param event_data: Data to pass to handlers
        :return:
        """
        if not isinstance(event_data, dict):
            self.logger.error("Invalid event data: {}".format(event_data))
            return None
        if event_name not in self.event_handlers:
            self.logger.warn("Unknown event: {}".format(event_name))
            return None
        for handler in self.event_handlers[event_name]:
            try:
                handler(event_data)
                return True
            except Exception as e:
                self.logger.error("Error calling handler: {}".format(e))

    def on(self, event_name: str, handler):
        """
        Add an event handler.
        
        Alias for add
        :param event_name: Event name
        :param handler: Event handler
        :return:
        """
        self.add(event_name, handler)

    def add(self, event_name: str, handler):
        """
        Add an event handler
        :param event_name: Event name
        :param handler: Event handler
        :return:
        """
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)

    def remove(self, event_name: str, handler):
        """
        Remove an event handler
        :param event_name: Event name
        :param handler: Event handler
        :return:
        """
        if event_name not in self.event_handlers:
            return
        self.event_handlers[event_name].remove(handler)