"""Автосервис - консольный проект на ООП (всё в одном файле).

Запуск:   python autoservice.py        - сам сервис (команда help покажет всё)
Тесты:    python autoservice.py test   - 29 проверок через assert
"""
import json
import os
import random
import re
import sys
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime


# ======================================================================
# ЧАСТЬ 1. Собственные исключения (ошибки)
# Свои классы ошибок: программа сообщает о проблеме понятным текстом и не падает.
# ======================================================================

class ProjectError(Exception):
    """Общий предок всех ошибок автосервиса."""


class InvalidCommandError(ProjectError):
    """Неизвестная команда или неверное число аргументов."""


class ValidationError(ProjectError):
    """Некорректные данные (номер, количество, имя...)."""


class NotFoundError(ProjectError):
    """Машина, заказ, деталь или работа не найдены."""


class OutOfStockError(ProjectError):
    """На складе не хватает детали."""


class NoMechanicError(ProjectError):
    """В штате нет механика нужной специализации."""


class InvalidStateError(ProjectError):
    """Действие недопустимо в текущем состоянии заказа или счёта."""


class WarrantyError(ProjectError):
    """Гарантия не применима (истекла или не распространяется)."""


class StorageError(ProjectError):
    """Ошибка сохранения или загрузки файла."""


# ======================================================================
# ЧАСТЬ 2. Справочные данные (константы, прайс, детали, штат)
# Всё, что можно менять без правки логики, собрано в словарях и списках.
# ======================================================================

WARRANTY_TICKS = 48        # гарантия на выполненный заказ (в тактах)
SUPPLIER_DELAY = 3         # за сколько тактов поставщик привозит деталь
BREAKDOWN_TICKS = 2        # простой механика при поломке инструмента
SHIPMENT_DELAY_EXTRA = 2   # на сколько тактов поставщик задерживает поставку

PARTS = {
    "oil_filter": {"title": "Масляный фильтр", "price": 2500},
    "engine_oil": {"title": "Моторное масло, 1 л", "price": 3000},
    "spark_plug": {"title": "Свеча зажигания", "price": 2000},
    "timing_belt": {"title": "Ремень ГРМ", "price": 15000},
    "brake_pads": {"title": "Тормозные колодки", "price": 12000},
    "shock_absorber": {"title": "Амортизатор", "price": 25000},
    "battery": {"title": "Аккумулятор", "price": 45000},
    "alternator": {"title": "Генератор", "price": 80000},
}

# Стартовый склад. Генератора нет специально - так видно заказ у поставщика.
INITIAL_STOCK = {
    "oil_filter": 5, "engine_oil": 12, "spark_plug": 8, "timing_belt": 1,
    "brake_pads": 2, "shock_absorber": 2, "battery": 1, "alternator": 0,
}

SPECIALIZATIONS = {
    "engine": "моторист",
    "electric": "автоэлектрик",
    "chassis": "специалист по ходовой",
}

# ключ работы: название, специализация, часы, нужные детали {ключ детали: количество}
WORKS = {
    "oil_change": {"title": "Замена масла", "spec": "engine", "hours": 1,
                   "parts": {"oil_filter": 1, "engine_oil": 4}},
    "spark_plugs": {"title": "Замена свечей", "spec": "engine", "hours": 1,
                    "parts": {"spark_plug": 4}},
    "timing_belt": {"title": "Замена ремня ГРМ", "spec": "engine", "hours": 4,
                    "parts": {"timing_belt": 1}},
    "alternator": {"title": "Замена генератора", "spec": "electric", "hours": 3,
                   "parts": {"alternator": 1}},
    "battery": {"title": "Замена аккумулятора", "spec": "electric", "hours": 1,
                "parts": {"battery": 1}},
    "diagnostics": {"title": "Диагностика электрики", "spec": "electric", "hours": 1,
                    "parts": {}},
    "brake_pads": {"title": "Замена колодок", "spec": "chassis", "hours": 2,
                   "parts": {"brake_pads": 1}},
    "shock_absorbers": {"title": "Замена амортизаторов", "spec": "chassis", "hours": 3,
                        "parts": {"shock_absorber": 2}},
}

# Штат по умолчанию: (имя, специализация)
DEFAULT_STAFF = [
    ("Ержан", "engine"),
    ("Данияр", "engine"),
    ("Айгерим", "electric"),
    ("Алишер", "chassis"),
]


def money(amount):
    """20500 -> '20500 тг'."""
    return f"{amount} тг"


# ======================================================================
# ЧАСТЬ 3. Класс Part - вид детали (название, цена)
# ======================================================================

class Part:
    """Вид детали: ключ, название и цена. Сколько штук - хранит склад."""

    def __init__(self, key, title, price):
        self._key = key
        self._title = title
        self._price = price

    @classmethod
    def from_key(cls, key):
        """Альтернативный конструктор: деталь из каталога (раздел 11.2)."""
        if key not in PARTS:
            raise NotFoundError(f"Детали «{key}» нет в каталоге (список - команда stock)")
        return cls(key, PARTS[key]["title"], PARTS[key]["price"])

    @classmethod
    def from_dict(cls, data):
        return cls(data["key"], data["title"], data["price"])

    @property
    def key(self):
        return self._key

    @property
    def title(self):
        return self._title

    @property
    def price(self):
        return self._price

    def describe(self):
        return f"{self._title} [{self._key}], цена {self._price} тг"

    def to_dict(self):
        return {"key": self._key, "title": self._title, "price": self._price}

    def __str__(self):
        return self._title

    def __eq__(self, other):
        return isinstance(other, Part) and self._key == other._key


# ======================================================================
# ЧАСТЬ 4. Класс Car - автомобиль клиента
# ======================================================================

class Car:
    """Автомобиль клиента."""

    def __init__(self, plate, model, owner):
        self._plate = Car.check_plate(plate)
        if model.strip() == "" or owner.strip() == "":
            raise ValidationError("Нужно указать модель и владельца")
        self._model = model.strip()
        self._owner = owner.strip()

    @staticmethod
    def check_plate(plate):
        """Госномер: 4-10 букв/цифр. Возвращает номер в верхнем регистре (раздел 11.3)."""
        plate = plate.strip().upper()
        if not plate.isalnum() or len(plate) < 4 or len(plate) > 10:
            raise ValidationError(f"Некорректный госномер «{plate}» (нужно 4-10 букв и цифр)")
        return plate

    @property
    def plate(self):
        return self._plate

    @property
    def model(self):
        return self._model

    @property
    def owner(self):
        return self._owner

    def describe(self):
        return f"{self._model} [{self._plate}], владелец: {self._owner}"

    def to_dict(self):
        return {"plate": self._plate, "model": self._model, "owner": self._owner}

    @classmethod
    def from_dict(cls, data):
        return cls(data["plate"], data["model"], data["owner"])

    def __str__(self):
        return f"{self._model} [{self._plate}]"

    def __eq__(self, other):
        return isinstance(other, Car) and self._plate == other._plate


# ======================================================================
# ЧАСТЬ 5. Класс Warehouse - склад деталей и заказы у поставщика
# ======================================================================

class Warehouse:
    """Склад деталей. Заказы у поставщика приезжают с задержкой."""

    def __init__(self, initial_stock):
        self._parts = {}      # ключ -> Part
        self._stock = {}      # ключ -> сколько штук на складе
        for key in PARTS:
            self._parts[key] = Part.from_key(key)
            self._stock[key] = 0
        self._incoming = []   # поставки: {"key": ..., "qty": ..., "arrive_at": ...}
        for key in initial_stock:
            if initial_stock[key] > 0:
                self.add(key, initial_stock[key])

    @staticmethod
    def check_qty(qty):
        if not isinstance(qty, int) or qty <= 0:
            raise ValidationError("Количество должно быть целым числом больше нуля")

    def _check_key(self, key):
        if key not in self._parts:
            raise NotFoundError(f"Детали «{key}» нет в каталоге (список - команда stock)")

    # ---------- запросы ----------
    def part(self, key):
        self._check_key(key)
        return self._parts[key]

    def available(self, key):
        self._check_key(key)
        return self._stock[key]

    def incoming_qty(self, key):
        """Сколько штук детали уже едет от поставщика."""
        self._check_key(key)
        total = 0
        for shipment in self._incoming:
            if shipment["key"] == key:
                total += shipment["qty"]
        return total

    @property
    def shipments(self):
        return list(self._incoming)

    @property
    def shipments_count(self):
        return len(self._incoming)

    def missing(self, needs):
        """Чего не хватает с учётом склада и уже заказанного: {ключ: сколько докупить}."""
        result = {}
        for key in needs:
            lack = needs[key] - self.available(key) - self.incoming_qty(key)
            if lack > 0:
                result[key] = lack
        return result

    # ---------- изменения ----------
    def add(self, key, qty):
        self._check_key(key)
        Warehouse.check_qty(qty)
        self._stock[key] += qty

    def take(self, key, qty):
        Warehouse.check_qty(qty)
        if self.available(key) < qty:
            raise OutOfStockError(
                f"На складе {self.available(key)} шт. «{self._parts[key].title}», нужно {qty}")
        self._stock[key] -= qty

    def try_take(self, needs):
        """Всё или ничего: списывает набор деталей, только если хватает на все."""
        for key in needs:
            Warehouse.check_qty(needs[key])
            if self.available(key) < needs[key]:
                return False
        for key in needs:
            self._stock[key] -= needs[key]
        return True

    def order_from_supplier(self, key, qty, now, delay):
        """Заказ у поставщика. Возвращает такт, на котором деталь приедет."""
        self._check_key(key)
        Warehouse.check_qty(qty)
        arrive_at = now + delay
        self._incoming.append({"key": key, "qty": qty, "arrive_at": arrive_at})
        return arrive_at

    def delay_shipment(self, index, extra):
        """Сдвигает поставку на extra тактов. Возвращает (название, новый такт)."""
        shipment = self._incoming[index]
        shipment["arrive_at"] += extra
        return self._parts[shipment["key"]].title, shipment["arrive_at"]

    def update(self, now):
        """Один такт: приехавшие поставки попадают на склад."""
        events = []
        still_on_the_way = []
        for shipment in self._incoming:
            if shipment["arrive_at"] <= now:
                self._stock[shipment["key"]] += shipment["qty"]
                title = self._parts[shipment["key"]].title
                events.append(f"Поставка: {title} x{shipment['qty']} поступила на склад")
            else:
                still_on_the_way.append(shipment)
        self._incoming = still_on_the_way
        return events

    # ---------- представление ----------
    def describe(self):
        lines = ["Склад:"]
        for key in self._parts:
            lines.append(f"  {self._parts[key].title} [{key}]: {self._stock[key]} шт.")
        if len(self._incoming) > 0:
            lines.append("В пути от поставщика:")
            for shipment in self._incoming:
                title = self._parts[shipment["key"]].title
                lines.append(f"  {title} x{shipment['qty']} - прибудет на такте {shipment['arrive_at']}")
        return "\n".join(lines)

    def to_dict(self):
        return {"stock": dict(self._stock), "incoming": list(self._incoming)}

    @classmethod
    def from_dict(cls, data):
        warehouse = cls({})
        for key in data["stock"]:
            warehouse._check_key(key)
            warehouse._stock[key] = data["stock"][key]
        for shipment in data["incoming"]:
            warehouse._check_key(shipment["key"])
            warehouse._incoming.append(dict(shipment))
        return warehouse

    def __str__(self):
        return f"Склад ({sum(self._stock.values())} шт. деталей)"

    def __getitem__(self, key):
        """warehouse['oil_filter'] - сколько штук на складе (раздел 10.5)."""
        return self.available(key)


# ======================================================================
# ЧАСТЬ 6. Класс Job - одна работа в заказ-наряде
# ======================================================================

class Job:
    """Одна работа в заказ-наряде (например, «замена масла»)."""

    def __init__(self, key, title, specialization, hours, parts):
        if specialization not in SPECIALIZATIONS:
            raise ValidationError(f"Неизвестная специализация «{specialization}»")
        if not isinstance(hours, int) or hours <= 0:
            raise ValidationError("Длительность работы - целое число часов больше нуля")
        self._key = key
        self._title = title
        self._specialization = specialization
        self._hours = hours
        self._parts = dict(parts)
        self._remaining = hours     # сколько часов осталось
        self._reserved = False      # детали для работы уже списаны со склада
        self._order_id = None
        self._mechanic = None       # имя механика
        self._rate = 0              # ставка механика на момент назначения

    @classmethod
    def from_work(cls, key):
        """Альтернативный конструктор: работа из прайса по ключу."""
        if key not in WORKS:
            raise NotFoundError(f"Работы «{key}» нет в прайсе (список - команда works)")
        work = WORKS[key]
        return cls(key, work["title"], work["spec"], work["hours"], work["parts"])

    @classmethod
    def from_dict(cls, data):
        job = cls(data["key"], data["title"], data["specialization"],
                  data["hours"], data["parts"])
        job._remaining = data["remaining"]
        job._reserved = data["reserved"]
        job._order_id = data["order_id"]
        job._mechanic = data["mechanic"]
        job._rate = data["rate"]
        return job

    # ---------- чтение состояния ----------
    @property
    def key(self):
        return self._key

    @property
    def title(self):
        return self._title

    @property
    def specialization(self):
        return self._specialization

    @property
    def hours(self):
        return self._hours

    @property
    def parts(self):
        return dict(self._parts)

    @property
    def remaining(self):
        return self._remaining

    @property
    def done(self):
        return self._remaining == 0

    @property
    def reserved(self):
        return self._reserved

    @property
    def order_id(self):
        return self._order_id

    @property
    def mechanic(self):
        return self._mechanic

    @property
    def rate(self):
        return self._rate

    @property
    def labor_cost(self):
        return self._hours * self._rate

    # ---------- изменение состояния - только через методы ----------
    def bind(self, order_id):
        self._order_id = order_id

    def reserve(self):
        self._reserved = True

    def assign(self, mechanic_name, rate):
        if not self._reserved:
            raise InvalidStateError("Нельзя назначить механика: детали ещё не списаны")
        self._mechanic = mechanic_name
        self._rate = rate

    def work(self, hours):
        if not self._reserved or self._mechanic is None:
            raise InvalidStateError("Работа не может идти без деталей и механика")
        self._remaining = max(0, self._remaining - hours)

    # ---------- представление ----------
    def state_text(self):
        if self.done:
            return "готово"
        if not self._reserved:
            return "ждёт деталей"
        return f"у механика {self._mechanic}, осталось {self._remaining} ч"

    def describe(self):
        spec = SPECIALIZATIONS[self._specialization]
        return f"{self._title} [{spec}, {self._hours} ч]: {self.state_text()}"

    def to_dict(self):
        return {"key": self._key, "title": self._title,
                "specialization": self._specialization, "hours": self._hours,
                "parts": dict(self._parts), "remaining": self._remaining,
                "reserved": self._reserved, "order_id": self._order_id,
                "mechanic": self._mechanic, "rate": self._rate}

    def __str__(self):
        return self._title


# ======================================================================
# ЧАСТЬ 7. Employee (абстрактный) -> Mechanic -> EngineMechanic / ElectricMechanic / ChassisMechanic
# ======================================================================

class Employee(ABC):
    """Абстрактный сотрудник: у каждого типа своя ставка за час (раздел 9)."""

    def __init__(self, name):
        if name.strip() == "":
            raise ValidationError("Имя сотрудника не может быть пустым")
        self._name = name.strip()

    @property
    def name(self):
        return self._name

    @abstractmethod
    def hourly_rate(self):
        pass


class Mechanic(Employee):
    """Механик с очередью работ. Конкретные виды механиков - ниже."""

    specialization = ""   # атрибут класса, в потомках переопределяется (раздел 5)

    def __init__(self, name):
        super().__init__(name)
        self._queue = []          # работы, которые механик делает по порядку
        self._downtime = 0        # сколько тактов ещё простаивает (сломан инструмент)
        self._hours_worked = 0

    @classmethod
    def create(cls, name, specialization):
        """Альтернативный конструктор: нужный подкласс по названию специализации."""
        if specialization not in MECHANIC_CLASSES:
            raise NotFoundError(f"Неизвестная специализация «{specialization}»")
        return MECHANIC_CLASSES[specialization](name)

    @classmethod
    def from_dict(cls, data, orders):
        """orders - словарь {номер: заказ}: по нему очередь снова связывается с работами."""
        mechanic = cls.create(data["name"], data["specialization"])
        mechanic._downtime = data["downtime"]
        mechanic._hours_worked = data["hours_worked"]
        for ref in data["queue"]:
            order = orders[ref["order_id"]]
            mechanic._queue.append(order.job(ref["work"]))
        return mechanic

    # ---------- состояние ----------
    @property
    def is_broken(self):
        return self._downtime > 0

    @property
    def remaining_hours(self):
        total = 0
        for job in self._queue:
            total += job.remaining
        return total

    @property
    def load(self):
        """Нагрузка = часы в очереди + простой. По ней выбирают наименее занятого."""
        return self.remaining_hours + self._downtime

    # ---------- действия ----------
    def assign(self, job):
        if job.specialization != self.specialization:
            raise ValidationError(
                f"{self._name} ({SPECIALIZATIONS[self.specialization]}) не делает работу «{job.title}»")
        job.assign(self._name, self.hourly_rate())
        self._queue.append(job)

    def break_tool(self, ticks):
        if not isinstance(ticks, int) or ticks <= 0:
            raise ValidationError("Время простоя - целое число тактов больше нуля")
        self._downtime += ticks

    def update(self, now):
        """Один такт: механик чинит инструмент или работает над первой работой в очереди."""
        events = []
        if self._downtime > 0:
            self._downtime -= 1
            if self._downtime == 0:
                events.append(f"{self._name} починил инструмент и вернулся к работе")
            return events
        if len(self._queue) == 0:
            return events
        job = self._queue[0]
        job.work(1)
        self._hours_worked += 1
        if job.done:
            self._queue.pop(0)
            events.append(f"{self._name} закончил «{job.title}» (заказ №{job.order_id})")
        return events

    # ---------- представление ----------
    def describe(self):
        text = (f"{self._name} - {SPECIALIZATIONS[self.specialization]}, "
                f"{self.hourly_rate()} тг/ч, работ в очереди: {len(self)}, "
                f"осталось часов: {self.remaining_hours}")
        if self.is_broken:
            text += f", инструмент сломан (простой ещё {self._downtime} т.)"
        return text

    def to_dict(self):
        queue = []
        for job in self._queue:
            queue.append({"order_id": job.order_id, "work": job.key})
        return {"name": self._name, "specialization": self.specialization,
                "downtime": self._downtime, "hours_worked": self._hours_worked,
                "queue": queue}

    def __str__(self):
        return f"{self._name} ({SPECIALIZATIONS[self.specialization]})"

    def __len__(self):
        return len(self._queue)

    def __lt__(self, other):
        return self.load < other.load


class EngineMechanic(Mechanic):
    specialization = "engine"

    def hourly_rate(self):
        return 6000


class ElectricMechanic(Mechanic):
    specialization = "electric"

    def hourly_rate(self):
        return 7000


class ChassisMechanic(Mechanic):
    specialization = "chassis"

    def hourly_rate(self):
        return 5000


MECHANIC_CLASSES = {
    "engine": EngineMechanic,
    "electric": ElectricMechanic,
    "chassis": ChassisMechanic,
}


# ======================================================================
# ЧАСТЬ 8. Класс RepairOrder - заказ-наряд (машина + работы)
# ======================================================================

class RepairOrder:
    """Заказ-наряд: машина + набор работ. Детали списываются под каждую работу."""

    NEW = "new"
    WAITING_PARTS = "waiting_parts"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CLOSED = "closed"

    LABELS = {
        "new": "новый",
        "waiting_parts": "ждёт деталей",
        "in_progress": "в работе",
        "done": "выполнен, ждёт оплаты",
        "closed": "закрыт",
    }

    def __init__(self, order_id, car, jobs, created_at, is_warranty=False, parent_id=None):
        if len(jobs) == 0:
            raise ValidationError("В заказе должна быть хотя бы одна работа")
        self._id = order_id
        self._car = car
        self._jobs = list(jobs)
        for job in self._jobs:
            job.bind(order_id)
        self._created_at = created_at
        self._is_warranty = is_warranty
        self._parent_id = parent_id
        self._status = RepairOrder.NEW
        self._completed_at = None

    @classmethod
    def from_dict(cls, data, cars):
        """cars - словарь {госномер: Car}: по нему восстанавливается машина заказа."""
        jobs = []
        for job_data in data["jobs"]:
            jobs.append(Job.from_dict(job_data))
        order = cls(data["id"], cars[data["car"]], jobs, data["created_at"],
                    data["is_warranty"], data["parent_id"])
        order._status = data["status"]
        order._completed_at = data["completed_at"]
        return order

    # ---------- чтение ----------
    @property
    def id(self):
        return self._id

    @property
    def car(self):
        return self._car

    @property
    def jobs(self):
        return tuple(self._jobs)

    @property
    def status(self):
        return self._status

    @property
    def status_text(self):
        return RepairOrder.LABELS[self._status]

    @property
    def is_warranty(self):
        return self._is_warranty

    @property
    def parent_id(self):
        return self._parent_id

    @property
    def warranty_until(self):
        if self._completed_at is None:
            return None
        return self._completed_at + WARRANTY_TICKS

    def under_warranty(self, now):
        return self._completed_at is not None and now <= self.warranty_until

    def job(self, key):
        for job in self._jobs:
            if job.key == key:
                return job
        raise NotFoundError(f"В заказе №{self._id} нет работы «{key}»")

    # ---------- смена статуса - только через методы ----------
    def mark_waiting(self):
        if self._status not in (RepairOrder.NEW, RepairOrder.WAITING_PARTS):
            raise InvalidStateError(f"Заказ №{self._id} уже {self.status_text}")
        self._status = RepairOrder.WAITING_PARTS

    def mark_in_progress(self):
        if self._status not in (RepairOrder.NEW, RepairOrder.WAITING_PARTS):
            raise InvalidStateError(f"Заказ №{self._id} уже {self.status_text}")
        self._status = RepairOrder.IN_PROGRESS

    def close(self):
        if self._status != RepairOrder.DONE:
            raise InvalidStateError(f"Закрыть можно только выполненный заказ (сейчас: {self.status_text})")
        self._status = RepairOrder.CLOSED

    def update(self, now):
        """Один такт: если все работы готовы - заказ выполнен."""
        if self._status == RepairOrder.IN_PROGRESS:
            all_done = True
            for job in self._jobs:
                if not job.done:
                    all_done = False
            if all_done:
                self._status = RepairOrder.DONE
                self._completed_at = now
                return [f"Заказ №{self._id} выполнен, гарантия до такта {self.warranty_until}"]
        return []

    # ---------- представление ----------
    def describe(self):
        title = f"Заказ №{self._id}"
        if self._is_warranty:
            title += f" (гарантийный, по заказу №{self._parent_id})"
        lines = [f"{title}: {self._car}",
                 f"  Статус: {self.status_text}; создан на такте {self._created_at}"]
        if self._completed_at is not None:
            lines.append(f"  Выполнен на такте {self._completed_at}, гарантия до такта {self.warranty_until}")
        for job in self._jobs:
            lines.append(f"  - {job.describe()}")
        return "\n".join(lines)

    def to_dict(self):
        jobs = []
        for job in self._jobs:
            jobs.append(job.to_dict())
        return {"id": self._id, "car": self._car.plate, "jobs": jobs,
                "created_at": self._created_at, "is_warranty": self._is_warranty,
                "parent_id": self._parent_id, "status": self._status,
                "completed_at": self._completed_at}

    def __str__(self):
        mark = " (гарантия)" if self._is_warranty else ""
        return f"№{self._id}{mark} {self._car} - {self.status_text}, работ: {len(self)}"

    def __len__(self):
        return len(self._jobs)

    def __iter__(self):
        return iter(self._jobs)


# ======================================================================
# ЧАСТЬ 9. Класс Invoice - счёт по выполненному заказу
# ======================================================================

class Invoice:
    """Счёт по выполненному заказу: список строк [описание, сумма]."""

    def __init__(self, order_id, lines, issued_at, paid_at=None):
        self._order_id = order_id
        self._lines = lines
        self._issued_at = issued_at
        self._paid_at = paid_at

    @classmethod
    def from_order(cls, order, issued_at):
        """Счёт из заказа: работа = часы x ставка механика, детали - по каталожной цене."""
        lines = []
        for job in order:
            lines.append([f"Работа: {job.title} ({job.hours} ч x {job.rate} тг)", job.labor_cost])
            for key in job.parts:
                qty = job.parts[key]
                part = PARTS[key]
                lines.append([f"Деталь: {part['title']} x{qty}", part["price"] * qty])
        if order.is_warranty:
            subtotal = 0
            for line in lines:
                subtotal += line[1]
            lines.append(["Гарантийный случай - за счёт сервиса", -subtotal])
        return cls(order.id, lines, issued_at)

    @classmethod
    def from_dict(cls, data):
        return cls(data["order_id"], data["lines"], data["issued_at"], data["paid_at"])

    @property
    def order_id(self):
        return self._order_id

    @property
    def total(self):
        total = 0
        for line in self._lines:
            total += line[1]
        return total

    @property
    def paid(self):
        return self._paid_at is not None

    def pay(self, now):
        if self.paid:
            raise InvalidStateError(f"Счёт по заказу №{self._order_id} уже оплачен")
        self._paid_at = now

    def describe(self):
        lines = [f"Счёт по заказу №{self._order_id} (выписан на такте {self._issued_at})"]
        for title, amount in self._lines:
            lines.append(f"  {title}: {amount} тг")
        state = "оплачен" if self.paid else "не оплачен"
        lines.append(f"  ИТОГО: {self.total} тг ({state})")
        return "\n".join(lines)

    def to_dict(self):
        return {"order_id": self._order_id, "lines": self._lines,
                "issued_at": self._issued_at, "paid_at": self._paid_at}

    def __str__(self):
        state = "оплачен" if self.paid else "не оплачен"
        return f"Счёт по заказу №{self._order_id}: {self.total} тг ({state})"


# ======================================================================
# ЧАСТЬ 10. Класс Garage - главная «система» (всё хранит и создаёт)
# ======================================================================

class Garage:
    """Главный класс-«система» (композиция, раздел 12).

    Склад и механиков Garage создаёт сам; машины, заказы и счета хранит у себя.
    """

    EVENT_KINDS = ("breakdown", "delay")

    def __init__(self, log_file=None, seed=None, event_chance=0.1,
                 supplier_delay=SUPPLIER_DELAY, staff=None, initial_stock=None):
        if event_chance < 0 or event_chance > 1:
            raise ValidationError("Вероятность события - число от 0 до 1")
        if staff is None:
            staff = DEFAULT_STAFF
        if initial_stock is None:
            initial_stock = INITIAL_STOCK
        self._now = 0
        self._cash = 0
        self._next_order_id = 1
        self._event_chance = event_chance
        self._supplier_delay = supplier_delay
        self._rng = random.Random(seed)     # свой генератор: при одном seed события повторяются
        self._log_file = log_file
        self._events = []                   # сообщения, которые ещё не показаны пользователю
        # объекты создаёт сам Garage
        self._warehouse = Warehouse(initial_stock)
        self._mechanics = []
        for name, specialization in staff:
            self._mechanics.append(Mechanic.create(name, specialization))
        self._cars = {}       # госномер -> Car
        self._orders = {}     # номер -> RepairOrder
        self._invoices = {}   # номер заказа -> Invoice

    # ---------- чтение состояния ----------
    @property
    def now(self):
        return self._now

    @property
    def cash(self):
        return self._cash

    @property
    def warehouse(self):
        return self._warehouse

    @property
    def mechanics(self):
        return tuple(self._mechanics)

    @property
    def cars(self):
        return tuple(self._cars.values())

    @property
    def orders(self):
        return tuple(self._orders.values())

    def get_car(self, plate):
        key = plate.strip().upper()
        if key not in self._cars:
            raise NotFoundError(f"Автомобиль «{key}» не найден (список - команда cars)")
        return self._cars[key]

    def get_order(self, order_id):
        if order_id not in self._orders:
            raise NotFoundError(f"Заказ №{order_id} не найден (список - команда orders)")
        return self._orders[order_id]

    def invoice_for(self, order_id):
        return self._invoices.get(order_id)

    # ---------- журнал событий ----------
    def _emit(self, message):
        """Записывает событие в файл журнала (с датой и временем) и копит для показа."""
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] [такт {self._now}] {message}"
        if self._log_file:
            try:
                with open(self._log_file, "a", encoding="utf-8") as file:
                    file.write(line + "\n")
            except OSError:
                pass     # проблема с журналом не должна ронять сервис
        self._events.append(message)
        return message

    def drain_events(self):
        events = self._events
        self._events = []
        return events

    def log_tail(self, count):
        if not self._log_file:
            return []
        try:
            with open(self._log_file, encoding="utf-8") as file:
                lines = file.read().splitlines()
        except OSError:
            return []
        return lines[-count:]

    # ---------- машины и заказы ----------
    def add_car(self, plate, model, owner):
        car = Car(plate, model, owner)
        if car.plate in self._cars:
            raise ValidationError(f"Автомобиль {car.plate} уже принят")
        self._cars[car.plate] = car
        self._emit(f"Принят автомобиль: {car.describe()}")
        return car

    def create_order(self, plate, works):
        car = self.get_car(plate)
        if len(works) == 0:
            raise ValidationError("Укажите хотя бы одну работу")
        if len(set(works)) != len(works):
            raise ValidationError("Одна и та же работа указана дважды")
        jobs = []
        for key in works:
            job = Job.from_work(key)
            self._check_specialization(job.specialization)
            jobs.append(job)
        order = RepairOrder(self._next_order_id, car, jobs, self._now)
        self._next_order_id += 1
        self._orders[order.id] = order
        self._emit(f"Создан заказ-наряд №{order.id}: {car}, работ: {len(order)}")
        return order

    def _check_specialization(self, specialization):
        for mechanic in self._mechanics:
            if mechanic.specialization == specialization:
                return
        raise NoMechanicError(f"В штате нет механика со специализацией «{specialization}»")

    def _pick_mechanic(self, specialization):
        """Из механиков нужной специализации выбираем наименее загруженного (через __lt__)."""
        best = None
        for mechanic in self._mechanics:
            if mechanic.specialization == specialization:
                if best is None or mechanic < best:
                    best = mechanic
        if best is None:
            raise NoMechanicError(f"В штате нет механика со специализацией «{specialization}»")
        return best

    def start_order(self, order_id):
        order = self.get_order(order_id)
        if order.status not in (RepairOrder.NEW, RepairOrder.WAITING_PARTS):
            raise InvalidStateError(f"Заказ №{order.id} уже {order.status_text}")
        self._try_start(order)
        return order

    def _try_start(self, order):
        """Для каждой работы: берём детали и отдаём механику, а если деталей нет - заказываем."""
        for job in order.jobs:
            if job.reserved:
                continue
            if self._warehouse.try_take(job.parts):
                job.reserve()
                mechanic = self._pick_mechanic(job.specialization)
                mechanic.assign(job)
                self._emit(f"Заказ №{order.id}: «{job.title}» передана механику {mechanic.name}")
            else:
                self._order_missing(order, job)
        all_reserved = True
        for job in order.jobs:
            if not job.reserved:
                all_reserved = False
        if all_reserved:
            order.mark_in_progress()
        else:
            order.mark_waiting()

    def _order_missing(self, order, job):
        missing = self._warehouse.missing(job.parts)
        for key in missing:
            arrive_at = self._warehouse.order_from_supplier(
                key, missing[key], self._now, self._supplier_delay)
            title = self._warehouse.part(key).title
            self._emit(f"Заказ №{order.id}: для «{job.title}» не хватает «{title}» - "
                       f"заказано у поставщика x{missing[key]}, прибудет на такте {arrive_at}")

    def order_part(self, key, qty):
        """Ручной заказ детали у поставщика."""
        arrive_at = self._warehouse.order_from_supplier(key, qty, self._now, self._supplier_delay)
        title = self._warehouse.part(key).title
        self._emit(f"Заказано у поставщика: {title} x{qty}, прибудет на такте {arrive_at}")
        return arrive_at

    def pay(self, order_id):
        order = self.get_order(order_id)
        invoice = self._invoices.get(order_id)
        if invoice is None:
            raise InvalidStateError(f"По заказу №{order_id} счёт ещё не выписан (заказ не выполнен)")
        invoice.pay(self._now)
        self._cash += invoice.total
        order.close()
        self._emit(f"Оплачен счёт по заказу №{order_id}: {invoice.total} тг")
        return invoice

    def claim_warranty(self, order_id, work):
        """Гарантийный ремонт: повтор работы за счёт сервиса, если гарантия не истекла."""
        order = self.get_order(order_id)
        if order.is_warranty:
            raise WarrantyError("На гарантийный ремонт повторная гарантия не распространяется")
        if order.status not in (RepairOrder.DONE, RepairOrder.CLOSED):
            raise InvalidStateError("Гарантия действует только на выполненные заказы")
        if not order.under_warranty(self._now):
            raise WarrantyError(f"Гарантия по заказу №{order.id} истекла на такте "
                                f"{order.warranty_until} (сейчас такт {self._now})")
        order.job(work)     # проверяем, что такая работа была в заказе
        warranty_order = RepairOrder(self._next_order_id, order.car, [Job.from_work(work)],
                                     self._now, True, order.id)
        self._next_order_id += 1
        self._orders[warranty_order.id] = warranty_order
        self._emit(f"Гарантийный случай по заказу №{order.id}: создан заказ №{warranty_order.id}")
        self._try_start(warranty_order)
        return warranty_order

    # ---------- время и события ----------
    def tick(self, count):
        if not isinstance(count, int) or count < 1 or count > 1000:
            raise ValidationError("Число тактов - целое число от 1 до 1000")
        for _ in range(count):
            self._step()
        return self._now

    def _step(self):
        self._now += 1
        # Полиморфизм: у склада, механиков и заказов своя версия update()
        everything = [self._warehouse] + self._mechanics + list(self._orders.values())
        for thing in everything:
            for message in thing.update(self._now):
                self._emit(message)
        self._issue_invoices()
        for order in list(self._orders.values()):
            if order.status == RepairOrder.WAITING_PARTS:
                self._try_start(order)
        if self._rng.random() < self._event_chance:
            self.trigger_event(None)

    def _issue_invoices(self):
        for order in list(self._orders.values()):
            if order.status == RepairOrder.DONE and order.id not in self._invoices:
                invoice = Invoice.from_order(order, self._now)
                self._invoices[order.id] = invoice
                self._emit(f"Выписан счёт по заказу №{order.id}: {invoice.total} тг")
                if invoice.total == 0:      # гарантийный заказ - платить нечего
                    invoice.pay(self._now)
                    order.close()

    def trigger_event(self, kind):
        """Событие мира: поломка инструмента или задержка поставки.

        Возвращает текст события или None, если событие не случилось (нет подходящей цели).
        """
        handlers = {"breakdown": self._event_breakdown, "delay": self._event_delay}
        if kind is None:
            kind = self._rng.choice(self.EVENT_KINDS)
        if kind not in handlers:
            raise InvalidCommandError(
                f"Неизвестное событие «{kind}». Доступны: {', '.join(self.EVENT_KINDS)}")
        return handlers[kind]()

    def _event_breakdown(self):
        busy = []
        for mechanic in self._mechanics:
            if len(mechanic) > 0 and not mechanic.is_broken:
                busy.append(mechanic)
        if len(busy) == 0:
            return None
        mechanic = self._rng.choice(busy)
        mechanic.break_tool(BREAKDOWN_TICKS)
        return self._emit(f"СОБЫТИЕ: у механика {mechanic.name} сломался инструмент, "
                          f"простой {BREAKDOWN_TICKS} такта")

    def _event_delay(self):
        count = self._warehouse.shipments_count
        if count == 0:
            return None
        index = self._rng.randrange(count)
        title, arrive_at = self._warehouse.delay_shipment(index, SHIPMENT_DELAY_EXTRA)
        return self._emit(f"СОБЫТИЕ: поставщик задерживает «{title}», новая дата - такт {arrive_at}")

    # ---------- отчёты ----------
    def describe(self):
        active = 0
        for order in self._orders.values():
            if order.status in (RepairOrder.IN_PROGRESS, RepairOrder.WAITING_PARTS):
                active += 1
        return (f"Автосервис | такт {self._now} | касса {self._cash} тг | "
                f"машин: {len(self._cars)} | заказов: {len(self._orders)} (активных: {active})")

    def full_report(self):
        """Полиморфизм: describe() вызывается у объектов разных классов в одном цикле."""
        everything = ([self, self._warehouse] + self._mechanics + list(self._cars.values())
                      + list(self._orders.values()) + list(self._invoices.values()))
        lines = []
        for thing in everything:
            lines.append(thing.describe())
        return "\n".join(lines)

    def __str__(self):
        return f"Garage(такт={self._now}, касса={self._cash})"

    # ---------- сохранение и загрузка (JSON) ----------
    def to_dict(self):
        return {
            "now": self._now, "cash": self._cash, "next_order_id": self._next_order_id,
            "warehouse": self._warehouse.to_dict(),
            "mechanics": [m.to_dict() for m in self._mechanics],
            "cars": [c.to_dict() for c in self._cars.values()],
            "orders": [o.to_dict() for o in self._orders.values()],
            "invoices": [i.to_dict() for i in self._invoices.values()],
        }

    def _restore(self, data):
        """Всё собираем во временные переменные: при ошибке текущее состояние не портится."""
        try:
            warehouse = Warehouse.from_dict(data["warehouse"])
            cars = {}
            for item in data["cars"]:
                car = Car.from_dict(item)
                cars[car.plate] = car
            orders = {}
            for item in data["orders"]:
                order = RepairOrder.from_dict(item, cars)
                orders[order.id] = order
            mechanics = []
            for item in data["mechanics"]:
                mechanics.append(Mechanic.from_dict(item, orders))
            invoices = {}
            for item in data["invoices"]:
                invoice = Invoice.from_dict(item)
                invoices[invoice.order_id] = invoice
            now = data["now"]
            cash = data["cash"]
            next_order_id = data["next_order_id"]
        except (KeyError, TypeError, ValueError, IndexError, AttributeError):
            raise StorageError("Файл состояния повреждён или имеет неверный формат")
        except NotFoundError as error:
            raise StorageError(f"Файл состояния повреждён: {error}")
        self._warehouse = warehouse
        self._cars = cars
        self._orders = orders
        self._mechanics = mechanics
        self._invoices = invoices
        self._now = now
        self._cash = cash
        self._next_order_id = next_order_id
        self._events = []

    @classmethod
    def from_dict(cls, data, **kwargs):
        garage = cls(**kwargs)
        garage._restore(data)
        return garage

    def save(self, path):
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)
        except OSError:
            raise StorageError(f"Не удалось сохранить файл «{path}»")
        self._emit(f"Состояние сохранено в {path}")

    def load(self, path):
        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            raise StorageError(f"Файл «{path}» не найден")
        except (OSError, ValueError):       # json.JSONDecodeError - разновидность ValueError
            raise StorageError(f"Не удалось прочитать «{path}»: это не корректный JSON")
        self._restore(data)
        self._emit(f"Состояние загружено из {path} (такт {self._now})")


# ======================================================================
# ЧАСТЬ 11. Класс Console - ввод команд пользователя + сценарий demo
# ======================================================================

STATE_FILE = "garage_state.json"
LOG_FILE = "garage_log.txt"

# Сценарий для команды demo
DEMO_SCRIPT = [
    "status",
    "add_car 777AAA02 Toyota_Camry Алмас Серикбаев",
    "add_car 123BBB02 Hyundai_Solaris Мадина",
    "add_car 777aaa02 Kia_Rio Дубликат",
    "works",
    "new_order 777AAA02 oil_change spark_plugs",
    "new_order 123BBB02 alternator brake_pads",
    "new_order 123BBB02 car_wash",
    "start 1",
    "start 2",
    "team",
    "stock",
    "event delay",
    "tick 1",
    "orders",
    "show 1",
    "pay 1",
    "event breakdown",
    "tick 4",
    "orders",
    "tick 3",
    "show 2",
    "pay 2",
    "warranty 1 oil_change",
    "tick 1",
    "show 3",
    "start 99",
    "tick abc",
    "fly_to_moon",
    "tick 60",
    "warranty 1 spark_plugs",
    "save",
    "load",
    "status",
]


class Console:
    """Консольный интерфейс. Команды разбираются через словарь {имя: метод}."""

    def __init__(self, state_file=STATE_FILE, log_file=LOG_FILE, seed=None,
                 event_chance=0.1, autoload=True):
        self._state_file = state_file
        self._log_file = log_file
        self._running = True
        self.startup_message = ""
        self._garage = Garage(log_file=log_file, seed=seed, event_chance=event_chance)

        # Парсер: вместо цепочки if/elif - словарь "команда" -> метод
        self._commands = {
            "help": self.cmd_help,
            "status": self.cmd_status,
            "report": self.cmd_report,
            "works": self.cmd_works,
            "stock": self.cmd_stock,
            "team": self.cmd_team,
            "cars": self.cmd_cars,
            "add_car": self.cmd_add_car,
            "new_order": self.cmd_new_order,
            "orders": self.cmd_orders,
            "show": self.cmd_show,
            "start": self.cmd_start,
            "tick": self.cmd_tick,
            "pay": self.cmd_pay,
            "warranty": self.cmd_warranty,
            "order_part": self.cmd_order_part,
            "event": self.cmd_event,
            "log": self.cmd_log,
            "save": self.cmd_save,
            "load": self.cmd_load,
            "demo": self.cmd_demo,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }
        # Сколько аргументов допустимо: (минимум, максимум). Нет в словаре - аргументов быть не должно.
        self._arg_limits = {
            "add_car": (3, 99), "new_order": (2, 99), "show": (1, 1), "start": (1, 1),
            "tick": (0, 1), "pay": (1, 1), "warranty": (2, 2), "order_part": (2, 2),
            "event": (0, 1), "log": (0, 1),
        }

        if autoload and state_file and os.path.exists(state_file):
            try:
                self._garage.load(state_file)
                self._garage.drain_events()
                self.startup_message = f"Состояние автоматически загружено из {state_file}"
            except ProjectError as error:
                self.startup_message = f"Автозагрузка не удалась: {error}"

    # ---------- служебное ----------
    @property
    def garage(self):
        return self._garage

    @property
    def running(self):
        return self._running

    @property
    def command_names(self):
        return sorted(self._commands)

    @staticmethod
    def _to_int(text, what):
        try:
            return int(text)
        except ValueError:
            raise ValidationError(f"{what} должно быть целым числом, получено «{text}»")

    def _help_line(self, name):
        """Первая строка docstring метода - это и есть справка по команде."""
        return self._commands[name].__doc__.strip().splitlines()[0]

    def _sibling(self, filename):
        """Путь к файлу рядом с файлом состояния."""
        if self._state_file:
            return os.path.join(os.path.dirname(self._state_file), filename)
        return filename

    # ---------- разбор строки ----------
    def execute(self, line):
        words = line.split()
        if len(words) == 0:
            return ""
        name = words[0].lower()
        args = words[1:]
        try:
            if name not in self._commands:
                raise InvalidCommandError(f"Неизвестная команда «{name}». Список команд - help")
            low, high = self._arg_limits.get(name, (0, 0))
            if len(args) < low or len(args) > high:
                raise InvalidCommandError(
                    f"Неверное число аргументов. Формат: {self._help_line(name)}")
            text = self._commands[name](args)
        except ProjectError as error:
            text = f"Ошибка: {error}"
        except Exception as error:      # программа не должна падать ни при каком вводе
            text = f"Непредвиденная ошибка: {error}"
        parts = []
        if text:
            parts.append(text)
        for event in self._garage.drain_events():
            parts.append(f"  >> {event}")
        return "\n".join(parts)

    def run(self):
        print("=== Автосервис === (help - список команд, exit - выход)")
        if self.startup_message:
            print(self.startup_message)
        while self._running:
            try:
                line = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            result = self.execute(line)
            if result:
                print(result)

    # ---------- команды ----------
    # Первая строка docstring: "формат - описание". Из неё автоматически строится help.
    def cmd_help(self, args):
        """help - список команд"""
        lines = ["Команды:"]
        for name in sorted(self._commands):
            line = self._help_line(name)
            if line.startswith(name):       # quit - псевдоним exit, второй раз его не показываем
                lines.append("  " + line)
        return "\n".join(lines)

    def cmd_status(self, args):
        """status - сводка по сервису"""
        return self._garage.describe()

    def cmd_report(self, args):
        """report - полный отчёт по всем объектам"""
        return self._garage.full_report()

    def cmd_works(self, args):
        """works - прайс работ"""
        lines = ["Прайс работ (ключ: название, специализация, длительность, детали):"]
        for key in WORKS:
            work = WORKS[key]
            parts = []
            for part_key in work["parts"]:
                parts.append(f"{PARTS[part_key]['title']} x{work['parts'][part_key]}")
            parts_text = ", ".join(parts) if parts else "без деталей"
            lines.append(f"  {key}: {work['title']} [{SPECIALIZATIONS[work['spec']]}, "
                         f"{work['hours']} ч] - {parts_text}")
        return "\n".join(lines)

    def cmd_stock(self, args):
        """stock - склад и поставки"""
        return self._garage.warehouse.describe()

    def cmd_team(self, args):
        """team - механики и их загрузка"""
        lines = []
        for mechanic in self._garage.mechanics:
            lines.append(mechanic.describe())
        return "\n".join(lines)

    def cmd_cars(self, args):
        """cars - принятые автомобили"""
        if len(self._garage.cars) == 0:
            return "Автомобилей пока нет"
        lines = []
        for car in self._garage.cars:
            lines.append(car.describe())
        return "\n".join(lines)

    def cmd_add_car(self, args):
        """add_car <номер> <модель> <владелец...> - принять авто (в модели вместо пробела _)"""
        car = self._garage.add_car(args[0], args[1].replace("_", " "), " ".join(args[2:]))
        return f"Принят: {car.describe()}"

    def cmd_new_order(self, args):
        """new_order <номер> <работа...> - создать заказ-наряд (ключи работ - команда works)"""
        order = self._garage.create_order(args[0], args[1:])
        return f"Создан заказ №{order.id}. Запустите: start {order.id}"

    def cmd_orders(self, args):
        """orders - список заказов"""
        if len(self._garage.orders) == 0:
            return "Заказов пока нет"
        lines = []
        for order in self._garage.orders:
            lines.append(str(order))
        return "\n".join(lines)

    def cmd_show(self, args):
        """show <номер заказа> - подробности заказа и счёт"""
        number = self._to_int(args[0], "Номер заказа")
        text = self._garage.get_order(number).describe()
        invoice = self._garage.invoice_for(number)
        if invoice is not None:
            text += "\n" + invoice.describe()
        return text

    def cmd_start(self, args):
        """start <номер заказа> - запустить: списать детали, раздать механикам"""
        order = self._garage.start_order(self._to_int(args[0], "Номер заказа"))
        return f"Заказ №{order.id}: {order.status_text}"

    def cmd_tick(self, args):
        """tick [N] - пропустить N тактов (1 такт = 1 час), по умолчанию 1"""
        count = 1
        if len(args) == 1:
            count = self._to_int(args[0], "Число тактов")
        return f"Сейчас такт {self._garage.tick(count)}"

    def cmd_pay(self, args):
        """pay <номер заказа> - оплатить счёт"""
        invoice = self._garage.pay(self._to_int(args[0], "Номер заказа"))
        return str(invoice)

    def cmd_warranty(self, args):
        """warranty <номер заказа> <работа> - гарантийный случай"""
        new_order = self._garage.claim_warranty(self._to_int(args[0], "Номер заказа"), args[1])
        return f"Создан гарантийный заказ №{new_order.id}: {new_order.status_text}"

    def cmd_order_part(self, args):
        """order_part <деталь> <количество> - заказать деталь у поставщика"""
        arrive_at = self._garage.order_part(args[0], self._to_int(args[1], "Количество"))
        return f"Поставка ожидается на такте {arrive_at}"

    def cmd_event(self, args):
        """event [breakdown|delay] - вызвать событие вручную (без аргумента - случайное)"""
        kind = None
        if len(args) == 1:
            kind = args[0]
        message = self._garage.trigger_event(kind)
        if message is None:
            return "Событие не сработало: нет подходящей цели"
        return ""       # само событие покажется строкой «>>» ниже

    def cmd_log(self, args):
        """log [N] - последние N строк журнала, по умолчанию 10"""
        count = 10
        if len(args) == 1:
            count = self._to_int(args[0], "Число строк")
        lines = self._garage.log_tail(count)
        if len(lines) == 0:
            return "Журнал пуст"
        return "\n".join(lines)

    def cmd_save(self, args):
        """save - сохранить состояние в JSON"""
        if not self._state_file:
            raise StorageError("Файл состояния не задан")
        self._garage.save(self._state_file)
        return f"Сохранено в {self._state_file}"

    def cmd_load(self, args):
        """load - загрузить состояние из JSON"""
        if not self._state_file:
            raise StorageError("Файл состояния не задан")
        self._garage.load(self._state_file)
        return f"Загружено из {self._state_file}"

    def cmd_demo(self, args):
        """demo - проиграть демо-сценарий (на отдельном сервисе, ваши данные не трогает)"""
        log_path = self._sibling("demo_log.txt")
        if os.path.exists(log_path):
            os.remove(log_path)
        sandbox = Console(state_file=self._sibling("demo_state.json"), log_file=log_path,
                          seed=7, event_chance=0.0, autoload=False)
        out = ["=== ДЕМО ==="]
        for line in DEMO_SCRIPT:
            out.append(f"> {line}")
            result = sandbox.execute(line)
            if result:
                out.append(result)
        out.append("=== конец демо ===")
        return "\n".join(out)

    def cmd_exit(self, args):
        """exit - выход (quit - то же самое)"""
        self._running = False
        return "До свидания!"


# ======================================================================
# ЧАСТЬ 12. Тесты (запуск: python autoservice.py test)
# ======================================================================

def make_garage(**kwargs):
    """Новый сервис без случайных событий; журнал - во временной папке."""
    folder = tempfile.mkdtemp()
    kwargs.setdefault("event_chance", 0)
    return Garage(log_file=os.path.join(folder, "log.txt"), **kwargs)


def make_console():
    folder = tempfile.mkdtemp()
    return Console(state_file=os.path.join(folder, "state.json"),
                   log_file=os.path.join(folder, "log.txt"), event_chance=0, autoload=False)


def expect_error(error_type, func, *args):
    """Проверяет, что вызов func(*args) бросает нужное исключение."""
    try:
        func(*args)
    except error_type:
        return
    except Exception as other:
        raise AssertionError(f"ожидалась {error_type.__name__}, а получена {type(other).__name__}")
    raise AssertionError(f"ожидалась {error_type.__name__}, но ошибки не было")


def garage_with_car():
    garage = make_garage()
    garage.add_car("777AAA02", "Camry", "Алмас")
    return garage


# ---------------- сценарии ----------------

def test_add_car_and_duplicate():
    garage = make_garage()
    car = garage.add_car("777aaa02", "Toyota Camry", "Алмас")
    assert car.plate == "777AAA02"                       # номер приведён к верхнему регистру
    assert garage.get_car("777AAA02") == car
    expect_error(ValidationError, garage.add_car, "777AAA02", "Kia Rio", "Другой")


def test_invalid_input_rejected():
    garage = make_garage()
    expect_error(ValidationError, garage.add_car, "!!", "Kia", "Иван")       # плохой номер
    expect_error(ValidationError, garage.add_car, "123ABC02", "", "Иван")    # пустая модель
    expect_error(NotFoundError, garage.get_car, "000XXX00")
    expect_error(NotFoundError, garage.get_order, 42)
    expect_error(ValidationError, garage.tick, 0)
    expect_error(ValidationError, garage.tick, "5")


def test_order_validation():
    garage = garage_with_car()
    expect_error(NotFoundError, garage.create_order, "777AAA02", ["car_wash"])
    expect_error(ValidationError, garage.create_order, "777AAA02", [])
    expect_error(ValidationError, garage.create_order, "777AAA02", ["oil_change", "oil_change"])
    expect_error(NotFoundError, garage.create_order, "000XXX00", ["oil_change"])


def test_order_in_stock_and_invoice():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change"])
    assert order.status == RepairOrder.NEW
    garage.start_order(order.id)
    assert order.status == RepairOrder.IN_PROGRESS
    assert garage.warehouse["oil_filter"] == 4           # деталь списана со склада
    garage.tick(1)
    assert order.status == RepairOrder.DONE
    invoice = garage.invoice_for(order.id)
    assert invoice.total == 6000 + 2500 + 4 * 3000       # работа + фильтр + 4 л масла
    garage.pay(order.id)
    assert garage.cash == invoice.total
    assert order.status == RepairOrder.CLOSED
    expect_error(InvalidStateError, garage.pay, order.id)   # повторная оплата


def test_pay_before_done_and_double_start_fail():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change"])
    garage.start_order(order.id)
    expect_error(InvalidStateError, garage.pay, order.id)           # счёта ещё нет
    expect_error(InvalidStateError, garage.start_order, order.id)   # уже запущен


def test_shortage_orders_from_supplier_with_delay():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["alternator"])   # генератора на складе нет
    garage.start_order(order.id)
    assert order.status == RepairOrder.WAITING_PARTS
    assert garage.warehouse.incoming_qty("alternator") == 1   # заказано у поставщика
    garage.tick(2)
    assert order.status == RepairOrder.WAITING_PARTS          # поставка ещё не приехала
    garage.tick(1)                                            # такт 3 - поставка
    assert order.status == RepairOrder.IN_PROGRESS
    assert garage.warehouse.incoming_qty("alternator") == 0
    garage.tick(3)                                            # работа длится 3 часа
    assert order.status == RepairOrder.DONE


def test_other_jobs_start_while_one_waits_for_part():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["alternator", "brake_pads"])
    garage.start_order(order.id)
    assert order.job("alternator").reserved is False
    assert order.job("brake_pads").reserved is True          # колодки не ждут генератор


def test_load_balancing_between_mechanics():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change", "spark_plugs"])
    garage.start_order(order.id)
    first, second = order.jobs
    assert first.mechanic != second.mechanic                 # два моториста - работы разошлись


def test_mechanic_specialization_respected():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["brake_pads", "battery"])
    garage.start_order(order.id)
    assert order.job("brake_pads").mechanic == "Алишер"      # ходовик
    assert order.job("battery").mechanic == "Айгерим"        # электрик
    chassis = Mechanic.create("Тест", "chassis")
    expect_error(ValidationError, chassis.assign, order.job("battery"))   # чужая специальность


def test_no_mechanic_for_specialization():
    garage = make_garage(staff=[("Ержан", "engine")])
    garage.add_car("777AAA02", "Camry", "Алмас")
    expect_error(NoMechanicError, garage.create_order, "777AAA02", ["battery"])


def test_warranty_valid_and_free():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change"])
    garage.start_order(order.id)
    garage.tick(1)
    garage.pay(order.id)
    claim = garage.claim_warranty(order.id, "oil_change")
    assert claim.is_warranty and claim.parent_id == order.id
    garage.tick(1)
    assert garage.invoice_for(claim.id).total == 0           # за счёт сервиса
    assert claim.status == RepairOrder.CLOSED
    expect_error(WarrantyError, garage.claim_warranty, claim.id, "oil_change")


def test_warranty_expired_and_invalid():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change"])
    expect_error(InvalidStateError, garage.claim_warranty, order.id, "oil_change")  # не выполнен
    garage.start_order(order.id)
    garage.tick(1)
    expect_error(NotFoundError, garage.claim_warranty, order.id, "battery")   # такой работы не было
    garage.tick(WARRANTY_TICKS + 1)
    expect_error(WarrantyError, garage.claim_warranty, order.id, "oil_change")  # срок вышел


def test_warehouse_errors():
    warehouse = Warehouse({"battery": 1})
    assert warehouse["battery"] == 1 and warehouse["alternator"] == 0     # __getitem__
    expect_error(OutOfStockError, warehouse.take, "battery", 5)
    expect_error(ValidationError, warehouse.take, "battery", -1)
    expect_error(NotFoundError, warehouse.take, "rocket_engine", 1)
    assert warehouse.try_take({"battery": 2}) is False
    assert warehouse["battery"] == 1                         # всё или ничего


def test_magic_methods():
    assert Car("777AAA02", "Camry", "А") == Car("777aaa02", "Другая", "Б")   # __eq__
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change", "spark_plugs"])
    assert len(order) == 2                                                   # __len__
    assert [job.key for job in order] == ["oil_change", "spark_plugs"]       # __iter__
    busy = Mechanic.create("М1", "engine")
    free = Mechanic.create("М2", "engine")
    job = order.job("oil_change")
    job.reserve()
    busy.assign(job)
    assert free < busy and len(busy) == 1                                    # __lt__, __len__
    assert str(busy) and str(order) and str(garage) and str(garage.warehouse)  # __str__


def test_encapsulation():
    car = Car("777AAA02", "Camry", "Алмас")
    expect_error(AttributeError, setattr, car, "plate", "ХХХ")    # у property нет setter
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change"])
    expect_error(AttributeError, setattr, order, "status", "done")
    expect_error(InvalidStateError, order.close)                  # статус меняется только по правилам
    assert isinstance(order.jobs, tuple)                          # наружу отдаётся копия


def test_abstract_classes_cannot_be_created():
    expect_error(TypeError, Employee, "Ержан")
    expect_error(TypeError, Mechanic, "Ержан")       # hourly_rate не реализован
    assert issubclass(EngineMechanic, Mechanic) and issubclass(Mechanic, Employee)
    assert EngineMechanic("Ержан").hourly_rate() != ChassisMechanic("Алишер").hourly_rate()


def test_polymorphism():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change"])
    garage.start_order(order.id)
    garage.tick(1)
    report = garage.full_report()              # describe() у разных классов в одном цикле
    for word in ("Автосервис", "Склад", "Ержан", "Camry", "Счёт"):
        assert word in report
    for thing in [garage.warehouse] + list(garage.mechanics) + [order]:
        assert isinstance(thing.update(garage.now), list)     # update() у разных классов


def test_breakdown_event_delays_work():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["oil_change"])
    garage.start_order(order.id)
    assert "сломался" in garage.trigger_event("breakdown")
    garage.tick(2)
    assert order.status == RepairOrder.IN_PROGRESS            # механик чинит инструмент
    garage.tick(1)
    assert order.status == RepairOrder.DONE
    expect_error(InvalidCommandError, garage.trigger_event, "earthquake")


def test_delay_event_postpones_shipment():
    garage = make_garage()
    assert garage.trigger_event("delay") is None              # ничего не едет - события нет
    garage.order_part("battery", 2)
    before = garage.warehouse.shipments[0]["arrive_at"]
    garage.trigger_event("delay")
    assert garage.warehouse.shipments[0]["arrive_at"] > before


def test_random_events_repeat_with_same_seed():
    def run(seed):
        garage = make_garage(seed=seed, event_chance=0.5)
        garage.add_car("777AAA02", "Camry", "Алмас")
        garage.start_order(garage.create_order("777AAA02", ["alternator", "brake_pads"]).id)
        garage.tick(12)
        return garage.to_dict()
    assert run(3) == run(3)


def test_save_load_keeps_work_going():
    garage = garage_with_car()
    order = garage.create_order("777AAA02", ["alternator", "brake_pads"])
    garage.start_order(order.id)
    garage.tick(1)
    data = garage.to_dict()
    assert json.loads(json.dumps(data, ensure_ascii=False)) == data    # чистый JSON
    path = os.path.join(tempfile.mkdtemp(), "state.json")
    garage.save(path)
    restored = make_garage()
    restored.load(path)
    assert restored.to_dict() == data
    restored.tick(6)       # после загрузки очереди механиков продолжают работать
    assert restored.get_order(order.id).status == RepairOrder.DONE


def test_load_errors_keep_old_state():
    garage = garage_with_car()
    folder = tempfile.mkdtemp()
    expect_error(StorageError, garage.load, os.path.join(folder, "нет_файла.json"))
    broken = os.path.join(folder, "broken.json")
    with open(broken, "w", encoding="utf-8") as file:
        file.write("{ это не json")
    expect_error(StorageError, garage.load, broken)
    incomplete = os.path.join(folder, "incomplete.json")
    with open(incomplete, "w", encoding="utf-8") as file:
        file.write('{"now": 5}')
    expect_error(StorageError, garage.load, incomplete)
    assert len(garage.cars) == 1                              # прежнее состояние цело


def test_log_has_timestamps():
    garage = garage_with_car()
    garage.tick(1)
    lines = garage.log_tail(10)
    assert len(lines) > 0
    for line in lines:
        assert re.match(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[такт \d+\] ", line)


def test_console_errors_do_not_crash():
    console = make_console()
    assert "Неизвестная команда" in console.execute("fly_to_moon")
    assert "Формат: add_car" in console.execute("add_car 777AAA02")     # мало аргументов
    assert "Формат: tick" in console.execute("tick 1 2 3")              # много аргументов
    assert "Ошибка" in console.execute("tick abc")
    assert "Ошибка" in console.execute("start 99")
    assert "Ошибка" in console.execute("new_order 777AAA02 oil_change")  # машины нет
    assert console.execute("") == ""
    assert "Непредвиденная" not in console.execute("event earthquake")


def test_console_commands_with_arguments():
    console = make_console()
    assert "Принят" in console.execute("add_car 777AAA02 Toyota_Camry Алмас Серикбаев")
    assert "Серикбаев" in console.execute("cars")                       # владелец из нескольких слов
    assert "Создан заказ №1" in console.execute("new_order 777AAA02 oil_change")
    console.execute("start 1")
    console.execute("tick")
    assert "выполнен" in console.execute("orders")
    assert "оплачен" in console.execute("pay 1")


def test_help_is_built_from_command_dict():
    console = make_console()
    text = console.execute("help")
    for name in console.command_names:
        assert name in text
    assert "tick [N]" in text


def test_exit_command():
    console = make_console()
    assert console.running
    console.execute("exit")
    assert not console.running


def test_demo_runs_without_crashing():
    console = make_console()
    output = console.execute("demo")
    assert "Непредвиденная" not in output and "Traceback" not in output
    assert "конец демо" in output
    assert "Гарантия по заказу №1 истекла" in output
    assert len(console.garage.cars) == 0                      # основной сервис демо не затронул


def test_all_errors_share_base_class():
    for error_type in (InvalidCommandError, ValidationError, NotFoundError, OutOfStockError,
                       NoMechanicError, InvalidStateError, WarrantyError, StorageError):
        assert issubclass(error_type, ProjectError)


if __name__ == "__main__":
    names = sorted(name for name in globals() if name.startswith("test_"))
    failed = 0
    for name in names:
        try:
            globals()[name]()
            print(f"OK    {name}")
        except AssertionError as error:
            failed += 1
            print(f"FAIL  {name}: {error}")
    print(f"\nПройдено {len(names) - failed} из {len(names)}")


# ======================================================================
# ЧАСТЬ 13. Точка входа
# ======================================================================

def run_tests():
    names = sorted(name for name in globals() if name.startswith("test_"))
    failed = 0
    for name in names:
        try:
            globals()[name]()
            print(f"OK    {name}")
        except AssertionError as error:
            failed += 1
            print(f"FAIL  {name}: {error}")
    print(f"\nПройдено {len(names) - failed} из {len(names)}")


def main():
    if hasattr(sys.stdout, "reconfigure"):      # чтобы русский текст не ломался в консоли
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        Console().run()


if __name__ == "__main__":
    main()
