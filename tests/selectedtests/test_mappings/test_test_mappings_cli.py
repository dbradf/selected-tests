import json

from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.test_mappings.cli import cli

NS = "selectedtests.test_mappings.cli"
MAPPINGS_NS = "selectedtests.test_mappings.mappings"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


def m_ns(relative_name):
    """Return a full name to mappings from a name relative to the tested module"s name space."""
    return MAPPINGS_NS + "." + relative_name
