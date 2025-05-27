import os, logging
import toml, json
import ss_api
import polars as pl
from datetime import datetime, timezone
from typing import List, Dict, Callable, Union, Set
from ss_reporting_tool.Table import Table
from dataclasses import dataclass, field


class Summary(Table):

    def __init__(self, src, name, id, parent_id, last_update, tags, metadata) -> None:
        super().__init__(src, name, id, parent_id, last_update, tags, metadata)

    def buildSummary(self, *args, **kwargs):
        import importlib.util
        import sys

        def import_function_from_path(py_path, func_name):
            module_name = "_dynamic_module"
            spec = importlib.util.spec_from_file_location(module_name, py_path)
            if not spec or not spec.loader:
                return
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return getattr(module, func_name)

        path = self.metadata.get("path")
        func_name = self.metadata.get("function")
        if not func_name:
            raise ValueError("No function specified")
        func = import_function_from_path(path, func_name)
        if not func:
            return
        return func(*args, **kwargs)
