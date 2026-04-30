# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm integration tests."""

import logging
import socket
import time
import typing
from collections.abc import Generator

import jubilant
import pytest
import requests

logger = logging.getLogger(__name__)

# Timeout for juju wait operations in seconds
JUJU_WAIT_TIMEOUT = 1200

# Mattermost listens on port 8080 inside the workload container
MATTERMOST_PORT = 8080

# Admin user created once during app fixture setup so it is always the first
# user registered (= system admin) before any test creates Mattermost users.
ADMIN_EMAIL = "ci-admin@test.local"
ADMIN_USERNAME = "ciadmin"
ADMIN_PASSWORD = "CiAdmin1234!"


def _wait_for_http_ready(address: str, timeout: int = 300) -> None:
    """Block until Mattermost responds HTTP 200, or raise TimeoutError."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            if requests.get(address, timeout=5).status_code == 200:
                return
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(3)
    raise TimeoutError(f"Mattermost at {address} not ready after {timeout}s")


def _ensure_admin_user(address: str) -> None:
    """Create the admin user if it doesn't already exist (idempotent)."""
    resp = requests.post(
        f"{address}/api/v4/users",
        json={
            "email": ADMIN_EMAIL,
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD,
        },
        timeout=30,
    )
    # 201 = created, 400 = already exists — both are acceptable
    if resp.status_code not in (201, 400):
        resp.raise_for_status()


APP_NAME = "mattermost-k8s"


@pytest.fixture(scope="session", name="charm")
def charm_fixture(pytestconfig: pytest.Config):
    """Get value from parameter charm-file."""
    charm = pytestconfig.getoption("--charm-file")
    use_existing = pytestconfig.getoption("--use-existing", default=False)
    if not use_existing:
        assert charm, "--charm-file must be set"
    return charm


@pytest.fixture(scope="session")
def charm_resources(pytestconfig: pytest.Config) -> dict[str, str]:
    """The OCI resources for the charm."""
    rock_image_uri = pytestconfig.getoption("--mattermost-image")
    if not rock_image_uri:
        pytest.fail("--mattermost-image must be set")

    return {"app-image": rock_image_uri}


@pytest.fixture(scope="session", name="juju")
def juju_fixture(
    request: pytest.FixtureRequest,
) -> Generator[jubilant.Juju, None, None]:
    """Pytest fixture that wraps :meth:`jubilant.with_model`."""

    def show_debug_log(juju: jubilant.Juju):
        """Show debug log.

        Args:
            juju: the Juju object.
        """
        if request.session.testsfailed:
            log = juju.debug_log(limit=1000)
            print(log, end="")

    use_existing = request.config.getoption("--use-existing", default=False)
    if use_existing:
        juju = jubilant.Juju()
        yield juju
        show_debug_log(juju)
        return

    model = request.config.getoption("--model")
    if model:
        juju = jubilant.Juju(model=model)
        yield juju
        show_debug_log(juju)
        return

    keep_models = typing.cast(bool, request.config.getoption("--keep-models"))
    with jubilant.temp_model(keep=keep_models) as juju:
        juju.wait_timeout = 10 * 60
        yield juju
        show_debug_log(juju)
        return


@pytest.fixture(scope="session", name="app")
def app_fixture(
    juju: jubilant.Juju,
    pytestconfig: pytest.Config,
    charm: str,
    charm_resources: dict[str, str],
):
    """Deploy the Mattermost charm and its required relations.

    Deploys postgresql-k8s, the mattermost-k8s charm, integrates them,
    and waits for all units to become active.
    """
    # Deploy self-signed-certificates for TLS
    juju.deploy("self-signed-certificates")
    juju.wait(
        lambda status: jubilant.all_active(status, "self-signed-certificates"),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # Detect Juju major version to choose the right PostgreSQL channel
    juju_major = juju.version().major

    if juju_major >= 4:
        pg_channel = "16/edge"
        pg_base = "ubuntu@24.04"
        is_force = True
    else:
        pg_channel = "14/stable"
        pg_base = "ubuntu@22.04"
        is_force = False

    # Deploy PostgreSQL
    juju.deploy(
        "postgresql-k8s",
        channel=pg_channel,
        base=pg_base,
        trust=True,
        config={"profile": "testing"},
        force=is_force,
    )
    juju.integrate(
        "postgresql-k8s:client-certificates" if juju_major >= 4 else "postgresql-k8s",
        "self-signed-certificates:certificates",
    )
    juju.wait(
        lambda status: jubilant.all_active(status, "postgresql-k8s"),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # Deploy the Mattermost charm
    juju.deploy(
        charm=charm,
        app=APP_NAME,
        resources=charm_resources,
    )
    juju.wait(lambda status: jubilant.all_waiting(status, APP_NAME))

    # Integrate with PostgreSQL
    juju.integrate(APP_NAME, "postgresql-k8s:database")
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)

    yield APP_NAME


@pytest.fixture(scope="session")
def mattermost_address(app: str, juju: jubilant.Juju) -> str:
    """Get the Mattermost address and port."""
    status = juju.status()
    address = status.apps[app].address or status.apps[app].units[app + "/0"].address
    return f"http://{address}:{MATTERMOST_PORT}"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Pytest hook to set the test rep_* attribute for abort_on_fail."""
    _ = call
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def abort_on_fail(request: pytest.FixtureRequest):
    """Fixture which aborts other tests in module after first fails."""
    abort_on_fail = request.node.get_closest_marker("abort_on_fail")
    if abort_on_fail and getattr(request.module, "__aborted__", False):
        pytest.xfail("abort_on_fail")
    _ = yield
    if abort_on_fail and request.node.rep_call.failed:
        request.module.__aborted__ = True


def _host_ip() -> str | None:
    """Return the host's primary outbound IP, reachable from microk8s pods."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:  # noqa: BLE001
        return None


@pytest.fixture(scope="session")
def s3_address(pytestconfig: pytest.Config) -> str | None:
    """Provide the S3 service IP address for integration tests.

    Defaults to the host's primary IP so microk8s pods can reach radosgw
    on the runner without needing --s3-address to be passed explicitly.
    """
    return pytestconfig.getoption("--s3-address") or _host_ip()


def generate_s3_config(s3_address: str) -> dict:
    """Generate S3 config for MicroCeph radosgw based tests."""
    return {
        "access-key": "my-lovely-key",
        "secret-key": "this-is-very-secret",
        "bucket": "mattermost-test",
        "region": "us-east-1",
        "path": "mattermost",
        "endpoint": f"http://{s3_address}:7480",
    }
