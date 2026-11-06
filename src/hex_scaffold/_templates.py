"""Source templates for the generated hexagonal module.

Placeholders: ``@PKG@`` (package), ``@NAME@`` (module name), ``@ENTITY@`` (entity class).
Docstring quotes are written as three single quotes and converted when rendering, so the
templates can live in ordinary triple-double-quoted strings.
"""

from __future__ import annotations

_PACKAGE_INIT = """'''@NAME@ module following the hexagonal layout (ports and adapters).'''

from __future__ import annotations
"""

_DOMAIN_INIT = """'''Domain layer: entities and domain errors; imports nothing from other layers.'''

from __future__ import annotations

from @PKG@.domain.errors import NotFoundError
from @PKG@.domain.model import @ENTITY@

__all__ = ["NotFoundError", "@ENTITY@"]
"""

_MODEL = """'''Domain model.'''

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class @ENTITY@:
    '''Domain entity identified by ``id``.'''

    id: str
"""

_ERRORS = """'''Domain errors.'''

from __future__ import annotations


class NotFoundError(Exception):
    '''Raised when an entity does not exist.'''

    def __init__(self, entity_id: str) -> None:
        super().__init__(f"not found: {entity_id}")
        self.entity_id = entity_id
"""

_APPLICATION_INIT = """'''Application layer: ports and services; depends only on the domain.'''

from __future__ import annotations

from @PKG@.application.ports import @ENTITY@Repository
from @PKG@.application.service import @ENTITY@Service

__all__ = ["@ENTITY@Repository", "@ENTITY@Service"]
"""

_PORTS = """'''Ports: the interfaces the application needs from the outside world.'''

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from @PKG@.domain.model import @ENTITY@


class @ENTITY@Repository(Protocol):
    '''Storage port for the domain entity.'''

    def get(self, entity_id: str) -> @ENTITY@:
        '''Return the entity or raise ``NotFoundError``.'''

    def add(self, entity: @ENTITY@) -> None:
        '''Store or replace the entity.'''

    def list(self) -> Sequence[@ENTITY@]:
        '''Return all entities sorted by id.'''
"""

_SERVICE = """'''Application service: use cases written against the port.'''

from __future__ import annotations

from collections.abc import Sequence

from @PKG@.application.ports import @ENTITY@Repository
from @PKG@.domain.model import @ENTITY@


class @ENTITY@Service:
    '''Use cases; the storage port is injected through the constructor.'''

    def __init__(self, repository: @ENTITY@Repository) -> None:
        self._repository = repository

    def create(self, entity_id: str) -> @ENTITY@:
        '''Create, store and return a new entity.'''
        entity = @ENTITY@(id=entity_id)
        self._repository.add(entity)
        return entity

    def get(self, entity_id: str) -> @ENTITY@:
        '''Return the entity or raise ``NotFoundError``.'''
        return self._repository.get(entity_id)

    def list_all(self) -> Sequence[@ENTITY@]:
        '''Return every entity sorted by id.'''
        return self._repository.list()
"""

_ADAPTERS_INIT = """'''Adapters layer: implementations of the application ports.'''

from __future__ import annotations

from @PKG@.adapters.in_memory import InMemory@ENTITY@Repository

__all__ = ["InMemory@ENTITY@Repository"]
"""

_IN_MEMORY = """'''In-memory adapter, useful for tests and prototypes.'''

from __future__ import annotations

from collections.abc import Sequence

from @PKG@.domain.errors import NotFoundError
from @PKG@.domain.model import @ENTITY@


class InMemory@ENTITY@Repository:
    '''Dict-backed implementation of ``@ENTITY@Repository``.'''

    def __init__(self) -> None:
        self._items: dict[str, @ENTITY@] = {}

    def get(self, entity_id: str) -> @ENTITY@:
        '''Return the entity or raise ``NotFoundError``.'''
        try:
            return self._items[entity_id]
        except KeyError:
            raise NotFoundError(entity_id) from None

    def add(self, entity: @ENTITY@) -> None:
        '''Store or replace the entity.'''
        self._items[entity.id] = entity

    def list(self) -> Sequence[@ENTITY@]:
        '''Return all entities sorted by id.'''
        return [self._items[key] for key in sorted(self._items)]
"""

_TEST = """'''Tests for the @NAME@ service; they use only the in-memory adapter.'''

from __future__ import annotations

from @PKG@.adapters.in_memory import InMemory@ENTITY@Repository
from @PKG@.application.service import @ENTITY@Service
from @PKG@.domain.errors import NotFoundError
from @PKG@.domain.model import @ENTITY@


def make_service() -> @ENTITY@Service:
    return @ENTITY@Service(InMemory@ENTITY@Repository())


def test_create_then_get() -> None:
    service = make_service()
    created = service.create("a1")
    assert created == @ENTITY@(id="a1")
    assert service.get("a1") == created


def test_get_missing_raises_not_found() -> None:
    service = make_service()
    try:
        service.get("missing")
    except NotFoundError as error:
        assert error.entity_id == "missing"
    else:
        raise AssertionError("NotFoundError was not raised")


def test_list_all_is_sorted_by_id() -> None:
    service = make_service()
    service.create("b")
    service.create("a")
    assert [item.id for item in service.list_all()] == ["a", "b"]
"""

FILE_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("@PKG@/__init__.py", _PACKAGE_INIT),
    ("@PKG@/domain/__init__.py", _DOMAIN_INIT),
    ("@PKG@/domain/model.py", _MODEL),
    ("@PKG@/domain/errors.py", _ERRORS),
    ("@PKG@/application/__init__.py", _APPLICATION_INIT),
    ("@PKG@/application/ports.py", _PORTS),
    ("@PKG@/application/service.py", _SERVICE),
    ("@PKG@/adapters/__init__.py", _ADAPTERS_INIT),
    ("@PKG@/adapters/in_memory.py", _IN_MEMORY),
    ("tests/test_@NAME@_service.py", _TEST),
)


def render(template: str, *, package: str, name: str, entity: str) -> str:
    """Fill the placeholders of ``template`` and restore the docstring quotes."""
    text = template.replace("@ENTITY@", entity)
    text = text.replace("@PKG@", package).replace("@NAME@", name)
    return text.replace("'''", '"""')
