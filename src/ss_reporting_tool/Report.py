import ss_api
import polars as pl
from typing import List, Dict, Callable, Union, Set, Optional
from ss_reporting_tool.Table import Table
from ss_reporting_tool.Utils import log
import datetime, os


class Report(Table):

    def __init__(
        self, cfg, name, id, parent_id, last_update, tags, metadata, target_id, src
    ) -> None:
        self.target_id: Optional[str] = target_id
        self.src: Optional[str] = src
        super().__init__(cfg, name, id, parent_id, last_update, tags, metadata)

    def load_from_file(self) -> None:
        if not self.src:
            log(f"failed attempt to load from file: {self.name} ")
            return
        self.data = pl.read_csv(self.src, separator=chr(31))

    def export_to_ss(self) -> None:
        if not self.src:
            log(f"failed attempt to load from file: {self.name} ")
            return

        result = ss_api.import_xlsx_sheet(self.name, self.src, self.folder_id)
        if result:
            self.id = str(result["result"]["id"])
            self.update_refresh()
            print(f"  {self.name}({self.id}): new table loaded")

            self.cfg.serialize()

    def to_dict(self) -> Dict:
        table_dict = super().to_dict()
        table_dict["src"] = (
            os.path.relpath(self.src, self.cfg.data_dir) if self.src else ""
        )
        table_dict["target_id"] = self.target_id
        return table_dict
