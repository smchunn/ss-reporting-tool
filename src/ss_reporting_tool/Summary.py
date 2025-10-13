import os, logging
import toml, json
import ss_api
import polars as pl
from datetime import datetime, timezone
from typing import List, Dict, Callable, Union, Set
from ss_reporting_tool.Table import Table
from dataclasses import dataclass, field

class Summary(Table):

    def __init__(self, cfg, src, name, id, last_update, tags, fleet, metadata) -> None:
        self.reports = set()
        super().__init__(cfg, name, id, None, last_update, tags, metadata)
        self.fleet = fleet
        self.settings = self.load_settings()

    def load_settings(self):
        settings_path = self.metadata.get("settings_path")
        if not settings_path:
            return {}
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            return settings
        except Exception as e:
            print(f"Failed to load settings from {settings_path}: {e}")
            return {}

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
        return func(self, *args, **kwargs)

    def build_layout(self):
        # Adjust layout data to focus on fleet and metrics, not columns
        if not self.settings:
            print("No settings loaded, cannot build layout.")
            return

        fleet = self.metadata.get("fleet")
        metrics = self.settings.get("metrics", [])

        print(f"Preparing layout data for summary: {self.name} with fleet: {fleet} and metrics: {metrics}")
        # Prepare layout data based on fleet and metrics
        self.layout_data = {
            "name": self.name,
            "fleet": fleet,
            "metrics": metrics,
            # Add other layout-related data as needed
        }

    def create_references(self):
        # Remove API calls from Summary class
        print(f"Preparing references data for summary: {self.name}")
        # Prepare references data or metadata
        self.references_data = {
            # Placeholder for references data
        }

    def insert_formulas(self):
        # Remove API calls from Summary class
        print(f"Preparing formulas data for summary: {self.name}")
        # Prepare formulas data or metadata
        self.formulas_data = {
            # Placeholder for formulas data
        }

    def build_and_refresh(self):
        self.build_layout()
        self.create_references()
        self.insert_formulas()
