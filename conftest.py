import os
from activitypub_testsuite.interfaces import ServerTestSupport
from activitypub_testsuite.fixtures import *
import pytest

from firm.server.config import ServerConfig, MemoryStoreConfig
import firm.server.server
from firm.core.store.memory import MemoryResourceStore

from starlette.testclient import TestClient
from httpx import Request as HTTPXRequest, Response as HTTPXResponse
from pytest_httpx import HTTPXMock

from firm_aptesting.support import FirmServerTestSupport  # noqa
from firm_aptesting.support import FirmRemoteCommunicator
import asyncio

def pytest_configure(config):
    # pkg_dir = os.path.dirname(os.path.realpath(__file__))
    # install_fedi_tests(os.path.join(pkg_dir, "tests"))  # noqa: F405
    config.option.json_report_file = "test-report.json"


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
def remote_communicator(server_support) -> FirmRemoteCommunicator:
    return server_support.communicator

@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    return False

# @pytest.fixture(autouse=True)
# def setup_httpx_mock(httpx_mock: HTTPXMock, remote_communicator: FirmRemoteCommunicator):
#     def _handle_request(request: HTTPXRequest) -> HTTPXResponse:
#         return remote_communicator.handle_request(request)
#     httpx_mock.add_callback(_handle_request)


@pytest.fixture
def server_config(tmp_path) -> ServerConfig:
    return ServerConfig(
        [
            "https://server.test",
        ],
        store=MemoryStoreConfig(files=tmp_path),
    )


@pytest.fixture
def server_app(server_config):
    firm.server.server._app = None
    app = firm.server.server.app_factory(server_config)
    # Setup the lifespan context
    lifespan = app.router.lifespan_context(app)
    
    # Define the startup function that will be run
    async def async_startup():
        async with lifespan:
            pass  # Startup is done, but keep context active
    asyncio.run(async_startup())
    return app


@pytest.fixture
def test_client(server_app) -> TestClient:
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


