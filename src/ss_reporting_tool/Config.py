import os, logging
import toml
from datetime import datetime, timezone
import concurrent.futures, threading


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


class Config:
    def __init__(self) -> None:
        import argparse
        from ss_reporting_tool.Table import Table

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
        args = argparser.parse_args()

        self.function = args.func
        self.threadcount = args.threadcount

        self.path = os.path.abspath(os.path.expanduser(args.config))

        with open(args.config, "r") as conf:
            self._config = toml.load(conf)

        self.tables = []

        if isinstance(self._config, dict):
            for k, v in self._config["env"].items():
                os.environ[k] = v
            if self._config.get("verbose", False):
                self.verbose = True
            self.data_dir = self._config.get("data_dir", "./data")
            if not os.path.exists(self.data_dir):
                os.mkdir(self.data_dir)
            elif os.path.isfile(self.data_dir):
                print(f"Error: data dir exists as file")
                exit()

            self.target_folder = self._config.get("env", {}).get("target_folder")
            for k, v in self._config["tables"].items():
                table_id = v.get("id", None)
                target_id = v.get("target_id", None)  # Get target_id from config
                table_src = (
                    os.path.join(self.data_dir, v["src"])
                    if os.path.isfile(os.path.join(self.data_dir, v["src"]))
                    else ""
                )
                table_name = k
                table_refresh = v.get("date", datetime.now())
                table_tags = set(v.get("tags", None))  # Get target_id from config
                self.tables.append(
                    Table(
                        table_id,
                        self.target_folder,
                        target_id,
                        table_name,
                        table_tags,
                        table_src,
                        self.data_dir,
                        table_refresh,
                    )
                )
        self.verbose = self.verbose or args.verbose
        if self.verbose:
            logging.basicConfig(
                filename=os.path.join(self.data_dir, "sheet.log"),
                filemode="w",
                level=logging.INFO,
            )

    def serialize(self) -> None:
        table_dict = {table.name: table for table in self.tables}
        for k1, v1 in self._config.items():
            if k1 == "tables":
                for k2, v2 in v1.items():
                    if k2 in table_dict:
                        v2["id"] = table_dict[k2].id
                        if not table_dict[
                            k2
                        ].update_refresh:  # not sure this and the next line are necessary
                            table_dict[k2].update_refresh
                        v2["date"] = table_dict[k2].last_update

        with open(self.path, "w") as conf:
            encoder = TomlLineBreakPreservingEncoder()
            toml.dump(self._config, conf, encoder=encoder)


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


CFG = Config()
