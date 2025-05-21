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
