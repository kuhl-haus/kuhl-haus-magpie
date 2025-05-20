import traceback
from abc import ABC, abstractmethod

from time import sleep
from logging import Logger


class CanaryScript(ABC):
    logger: Logger

    def __init__(
        self,
        logger: Logger,
        delay: int,
        count: int
    ):
        """
        Initializes and handles invocation of the abstract invoke method based on
        provided delay and count. If count is less than zero, the invocation will
        repeat indefinitely with the specified delay. For positive count, the
        invocation will be carried out that many times with the given delay.

        Args:
            logger (Logger): Logger instance for logging or monitoring purposes.
            delay (int): Time delay in seconds between consecutive invocations.
            count (int): Number of times to invoke the private method. If negative,
                it will invoke indefinitely.
        """
        self.logger = logger
        self.delay = delay
        self.count = count
        if count < 0:
            while True:
                self.__do_invoke()
                sleep(delay)
        while count > 0:
            self.__do_invoke()
            if count <= 1:
                break
            sleep(delay)
            count -= 1

    @abstractmethod
    def invoke(self):
        """
        Represents an abstract method that enforces implementation in subclasses.

        This method serves as a contract that must be fulfilled by any subclass
        implementing it. Subclasses are expected to provide their specific
        implementation for this method to define and execute their own
        unique behavior.

        Raises:
            NotImplementedError: If the method is called on the base class
                                 and no overriding implementation exists.
        """
        pass

    def __do_invoke(self):
        """
        Handles the invocation of a method and logs any unhandled exceptions.

        This method attempts to call a concrete method, `invoke`, implemented in subclasses. If an
        exception occurs during the invocation, the error is logged along with
        the traceback for debugging purposes.

        Raises:
            Exception: Logs any unhandled exceptions raised during the invocation.
        """
        try:
            self.invoke()
        except Exception as e:
            self.logger.error(
                f"Unhandled exception raised ({repr(e)})\r\n"
                f"{traceback.format_exc()}"
            )
