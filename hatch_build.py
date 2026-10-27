# coding: utf-8
"""Compile shipped gettext catalogs without importing Django or touching its databases."""

from pathlib import Path
from tempfile import TemporaryDirectory

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        self._translations = TemporaryDirectory(prefix="fallout-rpg-i18n-")
        temporary = Path(self._translations.name)
        root = Path(self.root)
        forced = build_data.setdefault("force_include", {})
        for source_directory in ("fallout/locale", "locale"):
            for source in sorted((root / source_directory).rglob("*.po")):
                relative = source.relative_to(root)
                destination = relative
                if self.target_name == "wheel" and source_directory == "locale":
                    destination = Path("rpg") / relative
                    forced[str(source)] = destination.as_posix()
                compiled = temporary / relative.with_suffix(".mo")
                compiled.parent.mkdir(parents=True, exist_ok=True)
                with source.open("rb") as stream:
                    catalog = read_po(
                        stream, locale=source.relative_to(root / source_directory).parts[0], abort_invalid=True
                    )
                errors = [(message.id, problems) for message, problems in catalog.check()]
                if errors:
                    raise ValueError(f"Invalid gettext catalog {relative}: {errors}")
                with compiled.open("wb") as stream:
                    write_mo(stream, catalog)
                forced[str(compiled)] = destination.with_suffix(".mo").as_posix()

    def finalize(self, version, build_data, artifact_path):
        self._translations.cleanup()
