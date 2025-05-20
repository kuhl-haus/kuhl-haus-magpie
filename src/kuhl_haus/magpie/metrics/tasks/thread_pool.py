import sys
import traceback
from logging import Logger
from threading import BoundedSemaphore, RLock, Thread
from time import sleep
from typing import Callable, Dict, Union


class ThreadPool:
    size: int
    idle_time_out: int
    clean_up_sleep: float

    def __init__(self, logger: Logger, size: int = 10, idle_time_out: int = 360, clean_up_sleep: float = 0.250):
        """
        TODO: Replace a bunch of this with ThreadPoolExecutor
        https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor

        :param logger:
        :param size:
        """
        self.__logger = logger
        self.size = size
        self.idle_time_out = idle_time_out
        self.clean_up_sleep = clean_up_sleep
        self.__mutex = RLock()
        self.__thread_pool = BoundedSemaphore(value=size)
        self.__threads: Dict[str, Thread] = {}
        self.__cleanup_thread = Thread(target=self.__cleanup_threads, daemon=True)
        self.__cleanup_thread.start()

    @property
    def thread_count(self) -> int:
        with self.__mutex:
            return len(self.__threads)

    @property
    def clean_up_thread_is_alive(self):
        return self.__cleanup_thread.is_alive()

    def start_task(
        self,
        task_name: str,
        target: Union[Callable[..., object], None],
        kwargs: dict,
        blocking: bool = False,
    ):
        with self.__mutex:
            if task_name in self.__threads:
                if self.__threads[task_name].is_alive():
                    return
                else:
                    del self.__threads[task_name]
        if self.__thread_pool.acquire(blocking=blocking):
            try:
                with self.__mutex:
                    self.__threads[task_name] = Thread(target=target, kwargs=kwargs, daemon=True)
                    self.__threads[task_name].start()
            except Exception as e:
                print(f"Unhandled exception raised:{repr(e)}")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(
                    exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout
                )
                self.__logger.error(
                    "Unhandled exception raised:%s", repr(e), exc_info=e, stack_info=True
                )
            finally:
                self.__notify_cleanup()

    def __notify_cleanup(self):
        if self.clean_up_thread_is_alive:
            self.__logger.debug("Cleanup thread is alive... not starting a new thread.")
            return
        self.__logger.debug("Cleanup thread is not alive... starting a new thread.")
        self.__cleanup_thread = Thread(target=self.__cleanup_threads, daemon=True)
        self.__cleanup_thread.start()

    def __cleanup_threads(self):
        idle_timer = self.idle_time_out
        while idle_timer > 0:
            deleted_threads = []
            restart_idle_time_out_counter = False
            with self.__mutex:
                for task_name, thread in self.__threads.items():
                    if not thread.is_alive():
                        deleted_threads.append(task_name)
                        self.__thread_pool.release()
                for task_name in deleted_threads:
                    del self.__threads[task_name]
                    restart_idle_time_out_counter = True
            if restart_idle_time_out_counter:
                idle_timer = self.idle_time_out
            elif self.thread_count < 1 and not deleted_threads:
                # No threads in pool and none were deleted; decrementing idle timer
                idle_timer -= 1
            sleep(self.clean_up_sleep)
