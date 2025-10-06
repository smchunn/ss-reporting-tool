# ss-reporting-tool/src/ss_reporting_tool/Config.py
import os, logging
from types import UnionType
import toml
from datetime import datetime, timezone
import concurrent.futures, threading
from typing import List, Dict, Callable, Union, Set, Optional, IO
from dataclasses import dataclass, field
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Table import Table

import sys, re

if sys.version_info >= (3,):
    unicode = str


class InlineDict(dict):
    pass


class SSRTEncoder(toml.TomlEncoder):
    def __init__(self, _dict=dict):
        super().__init__(_dict, preserve=True)

    def dump_value(self, v):
        if isinstance(v, InlineDict):
            items = [f"{k} = {self.dump_value(val)}" for k, val in v.items()]
            return "{ " + ", ".join(items) + " }"
        return super().dump_value(v)


@dataclass
class CliArgs:
    function: str
    config_path: str
    threadcount: int = 8
    verbose: bool = False
    debug: bool = False
    match_column: Optional[str] = None
    update_column: Optional[str] = None


@dataclass
class Config:

    function: str
    threadcount: int = 8
    verbose: bool = False
    debug: bool = False
    env: Dict[str, str] = field(default_factory=dict)
    data_dir: Optional[str] = None
    settings_dir: Optional[str] = None
    target_folder: Optional[str] = None
    tables: List[Table] = field(default_factory=list)  # forward reference
    config_path: Optional[str] = None
    match_column: Optional[str] = None
    update_column: Optional[str] = None

    @staticmethod
    def from_dict(args: CliArgs, config_dict: Dict) -> "Config":
        env = config_dict.get("env", {})
        data_dir = config_dict.get("data_dir")
        settings_dir = config_dict.get("settings_dir")
        target_folder = config_dict.get("target_folder")
        new_cfg = Config(
            function=args.function,
            threadcount=args.threadcount,
            verbose=args.verbose,
            debug=args.debug,
            env=env,
            data_dir=data_dir,
            settings_dir=settings_dir,
            target_folder=target_folder,
            tables=[],
            config_path=args.config_path,
            match_column=args.match_column,
            update_column=args.update_column,
        )
        new_cfg.setup_environment()
        new_cfg.setup_data_directory()
        new_cfg.initialize_reports(config_dict)
        # new_cfg.initialize_summaries(config_dict)
        new_cfg.setup_logging()
        # Override match_column and update_column on reports if provided via CLI args
        if new_cfg.match_column or new_cfg.update_column:
            for table in new_cfg.tables:
                if isinstance(table, Report):
                    if new_cfg.match_column:
                        table.match_column = new_cfg.match_column
                    if new_cfg.update_column:
                        table.update_column = new_cfg.update_column
        return new_cfg

    def setup_environment(self):
        for k, v in self.env.items():
            os.environ[k] = v

    def setup_data_directory(self):
        if not self.data_dir:
            return
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        elif os.path.isfile(self.data_dir):
            raise RuntimeError(f"Error: data dir '{self.data_dir}' exists as a file.")

    def initialize_reports(self, config_dict: Dict):
        from ss_reporting_tool.Report import Report

        if not self.data_dir:
            logging.debug(f"failed attempt to load data dir {self.data_dir}")
            return

        for k, v in config_dict.get("reports", {}).items():
            table_id = v.get("id")
            target_folder = v.get("target_folder") or self.target_folder
            table_src = os.path.join(self.data_dir, v["src"]) if "src" in v else ""
            table_name = k
            table_refresh = v.get("date", datetime.now())
            table_primary_column = v.get("primary_column", 0)
            table_tags = set(v.get("tags", []))
            table_metadata = InlineDict(v.get("metadata", {}))
            match_column = v.get("match_column", None)
            update_column = v.get("update_column", None)
            self.tables.append(
                Report(
                    self,
                    table_name,
                    table_id,
                    target_folder,
                    table_refresh,
                    table_primary_column,
                    table_tags,
                    table_metadata,
                    table_src,
                    match_column,
                    update_column,
                )
            )
        for table in self.tables:
            if isinstance(table, Report):
                print(table)

    def setup_logging(self):
        print(f"{self.verbose=}, {self.debug=}")
        if not self.data_dir:
            logging.basicConfig(
                level=self.debug and logging.DEBUG or self.verbose and logging.INFO or logging.WARNING,
            )
            return
        logging.basicConfig(
            filename=os.path.join(self.data_dir, "sheet.log"),
            filemode="w",
            level=self.debug and logging.DEBUG or self.verbose and logging.INFO or logging.WARNING,
        )

    def to_dict(self) -> Dict:
        # Compose top-level keys
        config_dict = {
            "verbose": self.verbose,
            "threadcount": self.threadcount,
            "target_folder": self.target_folder or "",
        }

        if self.data_dir:
            config_dict["data_dir"] = self.data_dir

        if self.settings_dir:
            config_dict["settings_dir"] = self.settings_dir

        # Add env dict if present
        if self.env:
            config_dict["env"] = self.env

        reports_dict = {}
        for table in self.tables:
            if isinstance(table, Report):
                reports_dict[table.name] = table.to_dict()
                # print(type(table.metadata))

        if reports_dict:
            config_dict["reports"] = reports_dict

        return config_dict

    def serialize(self, fp: Optional[IO] = None):
        config_dict = self.to_dict()
        encoder = SSRTEncoder()
        if fp:
            toml.dump(config_dict, fp, encoder=encoder)
        elif self.config_path:
            with open(self.config_path, "w") as f:
                toml.dump(config_dict, f, encoder=encoder)


# --- Helper functions for TOML I/O ---
def load_config_dict_from_fp(fp: IO) -> Dict:
    return toml.load(fp)


def load_config_dict_from_path(path: str) -> Dict:
    with open(path, "r") as fp:
        return load_config_dict_from_fp(fp)


def dump_toml_dict_to_string(config_dict: Dict, encoder=None) -> str:
    """Serialize dict to TOML string."""
    return toml.dumps(config_dict, encoder=encoder)


def dump_toml_dict_to_fp(config_dict: Dict, fp: IO, encoder=None):
    """Serialize dict to TOML, writing to file-like object."""
    toml.dump(config_dict, fp, encoder=encoder)
    # ss_reporting_tool/src/ss_reporting_tool/__init__.py


def cli_args() -> CliArgs:
    import argparse

    argparser = argparse.ArgumentParser(add_help=True)
    argparser.add_argument("func", type=str, help="function to run: ")
    argparser.add_argument(
        "-c",
        "--config",
        type=str,
        help="path/to/config.toml",
        default="./config.toml",
    )
    argparser.add_argument("--verbose", action="store_true")
    argparser.add_argument("--threadcount", help="set # of threads", default=8)
    argparser.add_argument("--debug", action="store_true")
    argparser.add_argument("--match-column", type=str, help="column to match on")
    argparser.add_argument("--update-column", type=str, help="column to update")
    args = argparser.parse_args()
    return CliArgs(
        args.func,
        args.config,
        args.threadcount,
        args.verbose,
        args.debug,
        args.match_column,
        args.update_column,
    )


def setup():
    args = cli_args()
    config_dict = load_config_dict_from_path(args.config_path)
    return Config.from_dict(args, config_dict)
