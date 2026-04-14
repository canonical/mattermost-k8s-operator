# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm integration tests."""

import logging
import typing
from collections.abc import Generator

import jubilant
import pytest

logger = logging.getLogger(__name__)

# Timeout for juju wait operations in seconds
JUJU_WAIT_TIMEOUT = 1200

# Mattermost listens on port 8080 inside the workload container
MATTERMOST_PORT = 8080

APP_NAME = "mattermost-k8s"


@pytest.fixture(scope="module", name="charm")
def charm_fixture(pytestconfig: pytest.Config):
    """Get value from parameter charm-file."""
    charm = pytestconfig.getoption("--charm-file")
    use_existing = pytestconfig.getoption("--use-existing", default=False)
    if not use_existing:
        assert charm, "--charm-file must be set"
    return charm


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module", name="app")
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

    # Deploy PostgreSQL
    juju.deploy(
        "postgresql-k8s",
        channel="14/stable",
        base="ubuntu@22.04",
        trust=True,
        config={"profile": "testing"},
    )
    juju.integrate("postgresql-k8s", "self-signed-certificates:certificates")
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


@pytest.fixture(scope="module")
def mattermost_address(app: str, juju: jubilant.Juju) -> str:
    """Get the Mattermost application IP address and port."""
    status = juju.status()
    app_ip = status.apps[app].address
    return f"http://{app_ip}:{MATTERMOST_PORT}"


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
