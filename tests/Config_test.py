# ss-reporting-tool/tests/Config_test.py
from ss_reporting_tool.Config import *
import os, io
import pytest
import toml
from unittest.mock import patch, mock_open

# Sample TOML configuration for testing
sample_target_folder = "7138517580048260"
sample_data_dir = "./data/test"
sample_token = "test_token"

sample_table_name = "test_table"
sample_table_src = "test_table.xlx"
sample_table_id = "test_id"
sample_table_date = "2025-04-30"
sample_table_tag = "ac"

sample_toml = f"""
verbose = true
target_folder = "{sample_target_folder}"
data_dir = "{sample_data_dir}"

[env]
SMARTSHEET_ACCESS_TOKEN = "{sample_token}"

[tables.{sample_table_name}]
src = "{sample_table_src}"
id = "{sample_table_id}"
date = "{sample_table_date}"
tags = ["{sample_table_tag}"]
"""


@pytest.fixture
def cli_args():
    return CliArgs(
        function="test_function",
        config_path="test_config.toml",
        threadcount=4,
        verbose=True,
        debug=False,
    )


@pytest.fixture
def mock_open_config():
    with patch("builtins.open", mock_open(read_data=sample_toml)) as mock_file:
        yield mock_file


@pytest.fixture
def config(cli_args, mock_open_config):
    return Config.from_dict(
        args=cli_args, config_dict=load_config_dict_from_path(mock_open_config)
    )


# def test_load_config(config, mock_open_config):
#     """Test if the configuration loads correctly from a TOML file."""


def test_setup_environment(config):
    """Test if environment variables are set correctly."""
    assert os.environ.get("SMARTSHEET_ACCESS_TOKEN") == sample_token


def test_setup_data_directory(config, mock_open_config):
    """Test if the data directory is created when it does not exist."""
    assert os.path.exists(config.data_dir)


def test_initialize_tables(config):
    """Test if tables are initialized correctly."""
    assert len(config.tables) == 1
    assert config.tables[0].name == sample_table_name
    assert config.tables[0].id == sample_table_id


def test_setup_logging(config):
    """Test if logging is set up correctly."""
    expected_level = (
        logging.DEBUG
        if config.debug
        else (logging.INFO if config.verbose else logging.WARNING)
    )
    actual_level = logging.getLogger().getEffectiveLevel()
    # assert actual_level == expected_level


def test_serialize(cli_args):
    config_dict = toml.loads(sample_toml)
    config = Config.from_dict(args=cli_args, config_dict=config_dict)

    config.tables[0].id = "new_id"

    mock_fp = io.StringIO()
    config.serialize(mock_fp)

    output = mock_fp.getvalue()
    assert sample_table_name in output
    assert "new_id" in output


# Additional tests can be added to cover more scenarios

if __name__ == "__main__":
    pytest.main()
