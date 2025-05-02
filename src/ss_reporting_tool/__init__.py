from ss_reporting_tool.Config import Config, CliArgs, load_config_dict_from_path

CFG: Config
CFG_PATH: str


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
    args = argparser.parse_args()
    return CliArgs(args.func, args.config, args.threadcount, args.verbose, args.debug)


def setup():
    global CFG, CFG_PATH
    args = cli_args()
    CFG_PATH = args.config_path
    config_dict = load_config_dict_from_path(CFG_PATH)
    CFG = Config.from_dict(args, config_dict)
