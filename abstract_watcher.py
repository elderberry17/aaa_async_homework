import abc
import asyncio
from typing import Coroutine, Any

"""
Описание задачи:
    Необходимо реализовать планировщик, позволяющий запускать и отслеживать фоновые корутины.
    Планировщик должен обеспечивать:
        - возможность планирования новой задачи
        - отслеживание состояния завершенных задач (сохранение результатов их выполнения)
        - отмену незавершенных задач перед остановкой работы планировщика

    Ниже представлен интерфейс, которому должна соответствовать ваша реализация.

    Обратите внимание, что перед завершением работы планировщика, все запущенные им корутины должны быть
    корректным образом завершены.

    В папке tests вы найдете тесты, с помощью которых мы будем проверять работоспособность вашей реализации

"""


class AbstractRegistrator(abc.ABC):
    """
    Сохраняет результаты работы завершенных задач.
    В тестах мы передадим в ваш Watcher нашу реализацию Registrator и проверим корректность сохранения результатов.
    """

    @abc.abstractmethod
    def register_value(self, value: Any) -> None:
        # Store values returned from done task
        ...

    @abc.abstractmethod
    def register_error(self, error: BaseException) -> None:
        # Store exceptions returned from done task
        ...


class AbstractWatcher(abc.ABC):
    """
    Абстрактный интерфейс, которому должна соответствовать ваша реализация Watcher.
    При тестировании мы рассчитываем на то, что этот интерфейс будет соблюден.
    """

    def __init__(self, registrator: AbstractRegistrator):
        self.registrator = registrator  # we expect to find registrator here

    @abc.abstractmethod
    async def start(self) -> None:
        # Good idea is to implement here all necessary for start watcher :)
        ...

    @abc.abstractmethod
    async def stop(self) -> None:
        # Method will be called on the end of the Watcher's work
        ...

    @abc.abstractmethod
    def start_and_watch(self, coro: Coroutine) -> None:
        # Start new task and put to watching
        ...


class StudentWatcher(AbstractWatcher):
    def __init__(self, registrator: AbstractRegistrator, ttl=10):
        super().__init__(registrator)
        self.registrator = registrator
        # список активных задач
        self.active_tasks = []
        # время на жизнь задачи (по дефолту 10 секунд)
        self.ttl = ttl

    async def start(self) -> None:
        for task in self.active_tasks:
            task.cancel()
            self.delete_from_tasks(task)

    def delete_from_tasks(self, task):
        try:
            self.active_tasks.remove(task)
        except:
            pass

    async def stop(self) -> None:
        done, pending = await asyncio.wait(self.active_tasks, timeout=self.ttl)
        for task in done:
            try:
                self.registrator.register_value(task.result())
            except Exception as error:
                self.registrator.register_error(error)
            self.delete_from_tasks(task)

        for task in pending:
            task.cancel()
            self.delete_from_tasks(task)

    def start_and_watch(self, coro: Coroutine) -> None:
        new_task = asyncio.create_task(coro)
        self.active_tasks.append(new_task)
