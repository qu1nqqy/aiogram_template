from dishka import make_async_container, AsyncContainer

from .providers.core import CoreProvider
from .providers.repos import RepositoryProvider
from .providers.services import ServiceProvider


def get_container() -> AsyncContainer:
    return make_async_container(
        CoreProvider(),
        RepositoryProvider(),
        ServiceProvider(),
    )