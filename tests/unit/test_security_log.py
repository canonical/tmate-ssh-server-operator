# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm security log unit tests."""

import json
import re
from unittest.mock import MagicMock

import security_log

# Need access to the logger subclass under test.
# pylint: disable=protected-access


def test_utc_owasp_logger_emits_nested_utc_json():
    """
    arrange: a _UTCOWASPLogger whose underlying logger is replaced with a mock.
    act: emit a sys_startup security event.
    assert: the record is JSON nested under owasp_event, carries the OWASP fields,
        and its timestamp is RFC3339 UTC ("Z"), so SIEM ingestion sees a
        consistent UTC-aligned schema regardless of the host timezone.
    """
    logger = security_log._UTCOWASPLogger(appid=security_log.APPID)
    logger.logger = MagicMock()

    logger.sys_startup(userid="tmate-ssh-server/0", description="started")

    args, kwargs = logger.logger.log.call_args
    payload = json.loads(args[1])
    event = payload[security_log.NESTED_JSON_KEY]
    assert event["appid"] == "canonical.tmate-ssh-server"
    assert event["type"] == "security"
    assert event["event"] == "sys_startup:tmate-ssh-server/0"
    assert event["level"] == "WARNING"
    assert event["description"] == "started"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", event["datetime"])
    assert kwargs["extra"][security_log.NESTED_JSON_KEY] == event
