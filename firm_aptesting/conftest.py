import os
from activitypub_testsuite.interfaces import ServerTestSupport
from activitypub_testsuite.fixtures import *
import pytest

from firm_aptesting.support import FirmServerTestSupport  # noqa
from firm_server.config import ServerConfig
import firm_server.server
from firm.store.memory import MemoryResourceStore

from starlette.testclient import TestClient

def pytest_configure(config):
    pkg_dir = os.path.dirname(os.path.realpath(__file__))
    install_fedi_tests(os.path.join(pkg_dir, "tests"))  # noqa: F405
    config.option.json_report_file = 'test-report.json'

@pytest.fixture(scope="session")
def server_test_directory():
    return os.path.dirname(__file__)

@pytest.fixture
def server_support(
    local_base_url,
    local_get_json,
    remote_base_url,
    request,
) -> ServerTestSupport:
    return FirmServerTestSupport(
        local_base_url,
        remote_base_url,
        request,
    )

@pytest.fixture
def server_store():
    return MemoryResourceStore()

@pytest.fixture
def server_config(server_store):
    return ServerConfig([
        "https://server.test",
    ], server_store)


@pytest.fixture
def server_app(server_config, server_store):
    firm_server.server._app = None
    return firm_server.server.app_factory(server_config, server_store)

@pytest.fixture
def test_client(server_app) -> TestClient:
    #     app: ASGIApp,
    #     base_url: str = "http://testserver",
    #     raise_server_exceptions: bool = True,
    #     root_path: str = "",
    #     backend: typing.Literal["asyncio", "trio"] = "asyncio",
    #     backend_options: dict[str, typing.Any] | None = None,
    #     cookies: httpx._types.CookieTypes | None = None,
    #     headers: dict[str, str] | None = None,
    #     follow_redirects: bool = True,
    return TestClient(server_app, base_url="https://server.test")

#
# activitypub-testsuite optional fixture overrides
#

@pytest.fixture
def instance_metadata():
    return {
        "name": "Firm",
        "software": "firm",
    }

@pytest.fixture
def local_base_url(test_client):
    return test_client.base_url

@pytest.fixture
def local_get(test_client: TestClient):
    def _get(url: str, media_type: str = "application/json"):
        response = test_client.get(url, headers={"Accept": media_type})
        response.raise_for_status()
        return response

    return _get