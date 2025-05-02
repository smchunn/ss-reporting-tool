# ss-reporting-tool/src/ss_reporting_tool/Config.py
import os, logging
from types import UnionType
import toml
from datetime import datetime, timezone
import concurrent.futures, threading
from typing import List, Dict, Callable, Union, Set, Optional, IO
from dataclasses import dataclass, field
from ss_reporting_tool import CFG, CFG_PATH



class TomlLineBreakPreservingEncoder(toml.TomlEncoder):
    def __init__(self, _dict=dict, preserve=False):
        super(TomlLineBreakPreservingEncoder, self).__init__(_dict, preserve)

    def dump_list(self, v):
        retval = "[\n"
        for u in v:
            if isinstance(u, str) and "\n" in u:
                retval += (
                    '  """' + u.replace('"""', '\\"""').replace("\\", "\\\\") + '""",\n'
                )
            else:
                retval += " " + str(self.dump_value(u)) + ","
        retval += " ]"
        return retval


@dataclass
class CliArgs:
    function: str
    config_path: str
    threadcount: int = 8
    verbose: bool = False
    debug: bool = False


@dataclass
class Config:
    from ss_reporting_tool.Table import Table

    function: str
    threadcount: int = 8
    verbose: bool = False
    debug: bool = False
    env: Dict[str, str] = field(default_factory=dict)
    data_dir: Optional[str] = None
    tables: List[Table] = field(default_factory=list)  # forward reference
    config_path: Optional[str] = None


    @staticmethod
    def from_dict(args: CliArgs, config_dict: Dict) -> "Config":
        env = config_dict.get("env", {})
        data_dir = config_dict.get("data_dir")
        new_cfg = Config(
            function=args.function,
            threadcount=args.threadcount,
            verbose=args.verbose,
            debug=args.debug,
            env=env,
            data_dir=data_dir,
            tables=[],
            config_path=args.config_path,
        )
        new_cfg.setup_environment()
        new_cfg.setup_data_directory()
        new_cfg.initialize_tables(config_dict)
        new_cfg.setup_logging()
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

    def initialize_tables(self, config_dict: Dict):
        from ss_reporting_tool.Table import Table

        target_folder = self.env.get("target_folder")
        data_dir = self.data_dir or ""
        for k, v in config_dict.get("tables", {}).items():
            table_id = v.get("id")
            target_id = v.get("target_id")
            table_src = os.path.join(data_dir, v["src"]) if "src" in v else ""
            table_name = k
            table_refresh = v.get("date", datetime.now())
            table_tags = set(v.get("tags", []))
            self.tables.append(
                Table(
                    table_name,
                    table_id,
                    target_folder,
                    target_id,
                    table_src,
                    data_dir,
                    table_refresh,
                    table_tags,
                )
            )

    def setup_logging(self):
        if not self.data_dir:
            logging.basicConfig(
                level=(
                    logging.DEBUG
                    if self.debug
                    else (logging.INFO if self.verbose else logging.WARNING)
                ),
            )
            return
        logging.basicConfig(
            filename=os.path.join(self.data_dir, "sheet.log"),
            filemode="w",
            level=(
                logging.DEBUG
                if self.debug
                else (logging.INFO if self.verbose else logging.WARNING)
            ),
        )
    def to_dict(self) -> Dict:
        # Compose top-level keys
        config_dict = {
            "verbose": self.verbose,
            "threadcount": self.threadcount,
        }

        if self.data_dir:
            config_dict["data_dir"] = self.data_dir

        # Add env dict if present
        if self.env:
            config_dict["env"] = self.env

        # Add tables as nested dicts
        tables_dict = {}
        for table in self.tables:
            tables_dict[table.name] = {
                "src": os.path.relpath(table.src, self.data_dir) if table.src else "",
                "id": table.id,
                "target_id": table.target_id,
                "date": table.last_update.strftime("%Y-%m-%d") if isinstance(table.last_update, datetime) else str(table.last_update),
                "tags": list(table.tags) if table.tags else [],
            }
            # Remove empty values if desired
            tables_dict[table.name] = {k: v for k, v in tables_dict[table.name].items() if v}

        if tables_dict:
            config_dict["tables"] = tables_dict

        return config_dict
    def serialize(self, fp: Optional[IO]=None):
        config_dict = self.to_dict()
        encoder = TomlLineBreakPreservingEncoder()
        if fp:
            toml.dump(config_dict, fp, encoder=encoder)
        elif CFG_PATH:
            with open(CFG_PATH, "r") as f:
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


def threader(func, tables, threadcount):
    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        for table in tables:
            func(table)
    elif len(tables) == 1:
        func(tables[0])
    else:
        with concurrent.futures.ThreadPoolExecutor(threadcount) as executor:
            futures = [executor.submit(func, table) for table in tables]

            for x, _ in enumerate(concurrent.futures.as_completed(futures)):
                print(f"thread no. {x} returned")


def scheduler(count, interval, func, *args, **kwargs):
    def wrapper():
        nonlocal count
        if count > 0:
            func(args, kwargs)
            count -= 1
            if count > 0:
                threading.Timer(interval, wrapper).start()

    wrapper()

