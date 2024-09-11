from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, cast, override
import uuid
import pytest

from activitypub_testsuite.http.client import HttpxServerTestSupport
from activitypub_testsuite.http.signatures import HTTPSignatureAuth
from activitypub_testsuite.interfaces import (
    Actor,
    HttpResponse,
    ServerTestSupport,
    RemoteRequest,
    RemoteResponse,
    RemoteCommunicator,
)
from activitypub_testsuite.support import BaseActor
from firm.interfaces import ResourceStore, FIRM_NS
from firm_server.config import ServerConfig
from starlette.testclient import TestClient


@dataclass
class StubHttpResponse:
    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status_code < 400

    @property
    def is_error(self) -> bool:
        return not self.is_success

    def json(self) -> Any:
        return self.data

    def raise_for_status(self):
        if self.is_error:
            raise Exception(f"HTTP Error: {self.status_code}")


class FirmLocalActor(BaseActor):
    def __init__(self, server: FirmServerTestSupport, profile: dict, auth: Any = None):
        super().__init__(profile, "https://server.test", auth)
        self.server = server

    def get_actor_uri(self, server, actor_name):
        """Get the URI for an actor based on an actor handle."""

    @override
    def post(
        self,
        url,
        data,
        exception=False,
        media_type: str | None = "application/activity+json",
    ) -> HttpResponse:
        if exception:
            raise Exception("Exception for testing")
        headers = {}
        if media_type:
            headers["Content-Type"] = media_type
        return self.server.client.post(url, json=data, headers=headers, auth=self.auth)

    @override
    def get(
        self,
        url,
        exception=False,
        media_type: str = "application/activity+json",
    ) -> HttpResponse:
        if exception:
            raise Exception("Exception for testing")
        return self.server.client.get(
            url, headers={"Accept": media_type}, auth=self.auth
        )

    def _save(self, resource: dict[str, Any]):
        async def _async_save():
            await self.server.store.put(resource)

        asyncio.run(_async_save())

    @override
    def setup_activity(
        self, properties: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Set up an activity so that it can be retrieved from a local/remote server."""
        raise NotImplementedError()

    # TODO Review the arguments for setup_object abstract method
    @override
    def setup_object(
        self,
        properties: dict[str, Any] | None = None,
        with_id: bool = True,
    ) -> dict[str, Any]:
        """Set up an object so that it can be retrieved from a local/remote server."""
        properties = properties or {}
        if with_id and "id" not in properties:
            properties["id"] = f"{self.base_url}/{uuid.uuid4()}"
        if "type" not in properties:
            properties["type"] = "Note"
        self._save(properties)
        return properties


class FirmRemoteActor(BaseActor):
    def __init__(self, server: FirmServerTestSupport, profile: dict, auth: Any = None):
        super().__init__(profile, "https://remote.test", auth)
        self.server = server

    # def get_actor_uri(self, server, actor_name):
    #     """Get the URI for an actor based on an actor handle."""

    @override
    def post(
        self,
        url,
        data,
        exception=False,
        media_type: str | None = "application/activity+json",
    ) -> HttpResponse:
        if exception:
            raise Exception("Exception for testing")
        headers = {}
        if media_type:
            headers["Content-Type"] = media_type
        return self.server.client.post(url, json=data, headers=headers, auth=self.auth)

    @override
    def get(
        self,
        url,
        exception=False,
        media_type: str = "application/activity+json",
    ) -> HttpResponse:
        if exception:
            raise Exception("Exception for testing")
        return self.server.client.get(
            url, headers={"Accept": media_type}, auth=self.auth
        )

    @override
    def setup_activity(
        self, properties: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Set up an activity so that it can be retrieved from a local/remote server."""
        if "id" not in properties:
            properties["id"] = f"{self.base_url}/{uuid.uuid4()}"
        if "actor" not in properties:
            properties["actor"] = self.id
        if "type" not in properties:
            properties["type"] = "Create"
        self._save(properties)
        return properties

    def _save(self, resource: dict[str, Any]):
        async def _async_save():
            await self.server.store.put(resource)

        asyncio.run(_async_save())

    @override
    def setup_object(
        self,
        properties: dict[str, Any] | None = None,
        with_id: bool = True,
    ) -> dict[str, Any]:
        properties = properties or {}
        if with_id and "id" not in properties:
            properties["id"] = f"{self.base_url}/{uuid.uuid4()}"
        """Set up an object so that it can be retrieved from a local/remote server."""
        return self._save(properties)


PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
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
sirZG/SM1YwT2G4YpPGy06Z0Fo3J
-----END PRIVATE KEY-----
"""

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAt7LSNwvSvjMMTrvzo8iv
YzEyGyYJJY3ofpS0lU28d5Wq03WyOJ1099rQ7vK5CrGgSouDgMEwLJoyPu78ynxJ
YcW+zp4+jqJEkqpuSPTcbPLWUhQZFUtVoFalwX2PKSe7OAnNL2mBkC6gwLJFvjm3
dUvmBUgPPSwizctbIJO1Z6Zjo6RSV2KMpJrTlJfMBfQZ8A1iDVPY0VIASwaCu6q8
/h9hSUZGKvotWHn8VZ9etfgf7YtZDMMSvh8jvaH+7fknR678yYbE4iOIpQFq7x4j
S3HIGfK00t8jfNdJoIzqX7hfnNtMaFOrK7ihYQY3KMKfbBBoTLovRw5VR43ea1Kx
lwc+iPNqGlfokyYI9Fpkh+3clMAeW5e7634GSU4BeWR3RXu4hKkcKw8jtYFcIXzO
MmxMu4I/9whKckeadjK4czVmfBeZBYVH4wkAd9o8J6tWqonXil2TqHQcp1iLDk3p
qUXtnqyQhrx3lkLu3tOkg2pjsqbTjGuQd8JBdOqqO1esmjSkJrhz8fN/kTWzpiDa
XG2JI9BfimwcqgndAMJH8OOuXAuSPPKN8kYeMJ/a61kD5B4nX6eI+cqKg/cPfGPa
pQE7GFSqaM79AL240M5yhoYhFLVGtqeg/vfEb/V1+hqdmTJmvANAvkrlmoxfcxdx
cF38UF2egml5YnqtcLl3/ukCAwEAAQ==
-----END PUBLIC KEY-----
"""


class FirmRemoteCommunicator(RemoteCommunicator):
    def __init__(self, server: FirmServerTestSupport):
        self.server = server

    @override
    def get_request(self, selector: Callable[..., RemoteRequest]):
        raise NotImplementedError()

    @override
    def get_most_recent_post(self):
        raise NotImplementedError


class FirmServerTestSupport(ServerTestSupport):
    def __init__(self, local_base_url, remote_base_url, request: pytest.FixtureRequest):
        super().__init__(local_base_url, remote_base_url, request)
        self.config = cast(ServerConfig, request.getfixturevalue("server_config"))
        self.store = cast(ResourceStore, request.getfixturevalue("server_store"))
        self.client = cast(TestClient, request.getfixturevalue("test_client"))
        self._communicator = FirmRemoteCommunicator(self)

    def _save(self, obj: dict[str, Any]):
        async def _async_save():
            await self.store.put(obj)

        asyncio.run(_async_save())

    def get_local_actor(self, actor_name: str = None) -> Actor:
        profile = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
            ],
            "id": "https://server.test/actor",
            # TODO check in webfinger server that type is available
            "type": "Person",
            "outbox": "https://server.test/actor/outbox",
            "inbox": "https://server.test/actor/inbox",
            "followers": "https://server.test/actor/followers",
            "preferredUsername": "actor",
            "alsoKnownAs": "acct:actor@server.test",
            "publicKey": {
                "id": "https://server.test/actor#main-key",
                "owner": "https://server.test/actor",
                "publicKeyPem": PUBLIC_KEY,
            },
        }  # TODO create an actor factory
        self._save(profile)
        self._save(
            {
                "id": "https://server.test/actor/outbox",
                "attributedTo": "https://server.test/actor",
                "type": "OrderedCollection",
                "totalItems": 0,
            }
        )
        self._save(
            {
                "id": "https://server.test/actor/inbox",
                "attributedTo": "https://server.test/actor",
                "type": "OrderedCollection",
                "totalItems": 0,
            }
        )
        self._save(
            {
                "id": "https://server.test/actor/followers",
                "attributedTo": "https://server.test/actor",
                "type": "Collection",
                "totalItems": 0,
            }
        )
        self._save(
            {
                "id": f"urn:uuid:{uuid.uuid4()}",
                "type": FIRM_NS.Credentials.value,
                "attributedTo": "https://server.test/actor",
                FIRM_NS.privateKey.value: PRIVATE_KEY,
            }
        )
        auth = HTTPSignatureAuth(profile["publicKey"]["id"], PRIVATE_KEY)
        return FirmLocalActor(self, profile, auth=auth)

    def get_remote_actor(self, actor_name: str | None = None) -> Actor:
        actor_name = actor_name or "remote"
        profile = {
            "id": f"https://remote.test/{actor_name}",
            "type": "Person",
            "outbox": f"https://remote.test/{actor_name}/outbox",
            "inbox": f"https://remote.test/{actor_name}/inbox",
            "publicKey": {
                "id": f"https://remote.test/{actor_name}#main-key",
                "owner": f"https://remote.test/{actor_name}",
                "publicKeyPem": PUBLIC_KEY,
            },
        }
        self._save(profile)
        self._save(
            {
                "id": f"urn:uuid:{uuid.uuid4()}",
                "type": FIRM_NS.Credentials.value,
                "attributedTo": f"https://remote.test/{actor_name}",
                FIRM_NS.privateKey.value: PRIVATE_KEY,
            }
        )
        auth = HTTPSignatureAuth(profile["publicKey"]["id"], PRIVATE_KEY)
        return FirmRemoteActor(self, profile, auth=auth)

    def get_unauthenticated_actor(self, actor_name: str | None = None) -> Actor:
        actor_name = actor_name or "unauthenticated"
        profile = {
            "id": f"https://remote.test/{actor_name}",
            "type": "Person",
            "outbox": f"https://remote.test/{actor_name}/outbox",
            "inbox": f"https://remote.test/{actor_name}/inbox",
            "publicKey": {
                "id": f"https://remote.test/{actor_name}#main-key",
                "owner": f"https://remote.test/{actor_name}",
                "publicKeyPem": PUBLIC_KEY,
            },
        }
        self._save(profile)
        self._save(
            {
                "id": f"urn:uuid:{uuid.uuid4()}",
                "type": FIRM_NS.Credentials.value,
                "attributedTo": f"https://remote.test/{actor_name}",
                FIRM_NS.privateKey.value: PRIVATE_KEY,
            }
        )
        return FirmRemoteActor(self, profile)

    def get_remote_communicator(self) -> RemoteCommunicator:
        return self._communicator
