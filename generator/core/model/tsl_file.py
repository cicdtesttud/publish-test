from __future__ import annotations

import copy
import datetime
import os.path
from pathlib import Path

from jinja2 import Template

from generator.core.tsl_config import config
from generator.utils.log_utils import LogInit
from generator.utils.requirement import requirement
from generator.utils.yaml_utils import YamlDataType


class TSLHeaderFile:
    """
    Helper class for the generator used to populate the header_file template.
    """
    @LogInit()
    def __init__(self, filename: Path, data_dict: YamlDataType) -> None:
        self.__filename = filename
        self.__data_dict = copy.deepcopy(data_dict)
        if "tsl_predefined_file_includes" not in self.__data_dict:
            self.__data_dict["tsl_predefined_file_includes"] = []

    @property
    def data(self) -> YamlDataType:
        return self.__data_dict

    @property
    def file_name(self) -> Path:
        return self.__filename

    def __eq__(self, other):
        if isinstance(other, TSLHeaderFile):
            # if the include_guard is the same, the header file must be the same
            return self.__data_dict["tsl_include_guard"] == other.data["tsl_include_guard"]
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.__data_dict["tsl_include_guard"])

    def add_file_include(self, header_file: TSLHeaderFile) -> None:
        if header_file not in self.__data_dict["tsl_file_includes"]:
            self.__data_dict["tsl_file_includes"].append(header_file)
    
    def add_predefined_tsl_file_include(self, header_file_str: str) -> None:
        if header_file_str not in self.__data_dict["tsl_predefined_file_includes"]:
            self.__data_dict["tsl_predefined_file_includes"].append(header_file_str)

    def add_include(self, include: str) -> None:
        if include not in self.__data_dict["includes"]:
            self.__data_dict["includes"].append(include)

    def import_includes(self, data_dict: YamlDataType) -> None:
        if "includes" in data_dict:
            for include_str in data_dict["includes"]:
                self.add_include(include_str)

    def add_code(self, code: str) -> None:
        self.__data_dict["codes"].append(code)

    def add_code_to_be_rendered(self, code: str) -> None:
        self.__data_dict["codes"].append(Template(code).render(self.__data_dict))

    def get_relative_file_name(self) -> Path:
        return self.__filename

    def render(self) -> str:
        # includes = copy.deepcopy(self.__data_dict["includes"])
        current_path: Path = self.file_name.parent
        tsl_file_includes = [f"\"{Path(os.path.relpath(Path(included_file.file_name), current_path))}\"" for included_file in self.__data_dict["tsl_file_includes"]]
        self.__data_dict["includes"].extend([tsl_include for tsl_include in tsl_file_includes if tsl_include not in self.__data_dict["includes"]])
        self.__data_dict["includes"].extend(self.__data_dict["tsl_predefined_file_includes"])
        return config.get_template("core::header_file").render(self.__data_dict)

    def render_to_file(self) -> None:
        self.__filename.write_text(self.render())

    @staticmethod
    def create_include_guard(filename: Path) -> str:
        subst_filename: str = config.include_guard_regex.sub("_", str(filename).upper())
        return f"TUD_D2RG_TSL{subst_filename}"

    @staticmethod
    @requirement(filename="NotNone", data_dict="NotNone")
    def create_from_dict(filename: Path, data_dict: YamlDataType) -> TSLHeaderFile:
        new_data_dict: YamlDataType = {
            # "file_name": filename,
            "year": datetime.date.today().year,
            "date": datetime.date.today(),
            "file_description": data_dict["description"] if "description" in data_dict else "",
            "git_information": config.git_config_as_list,
            "file_name": filename,


            "git_version_str" : config.get_version_str,
            "tsl_include_guard": TSLHeaderFile.create_include_guard(filename),
            "tsl_namespace": config.get_config_entry("namespace"),
            "tsl_file_includes": [],
            "includes": [],
            "codes": []
        }
        return TSLHeaderFile(filename, {**new_data_dict, **data_dict})


class TSLSourceFile:
    @LogInit()
    def __init__(self, filename: Path, data_dict: YamlDataType) -> None:
        self.__filename = filename
        self.__data_dict = copy.deepcopy(data_dict)

    @property
    def data(self) -> YamlDataType:
        return self.__data_dict

    @property
    def file_name(self) -> Path:
        return self.__filename

    def __eq__(self, other):
        if isinstance(other, TSLSourceFile):
            # if the include_guard is the same, the header file must be the same
            return self.file_name == other.file_name
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(str(self.__filename))

    def add_include(self, include: str) -> None:
        if include not in self.__data_dict["includes"]:
            self.__data_dict["includes"].append(include)

    def add_file_include(self, header_file: TSLHeaderFile) -> None:
        if header_file not in self.__data_dict["tsl_file_includes"]:
            self.__data_dict["tsl_file_includes"].append(header_file)

    def import_includes(self, data_dict: YamlDataType) -> None:
        if "includes" in data_dict:
            for include_str in data_dict["includes"]:
                self.add_include(include_str)

    def add_code(self, code: str) -> None:
        self.__data_dict["codes"].append(code)

    def get_relative_file_name(self) -> Path:
        return self.__filename

    def render(self) -> str:
        current_path: Path = self.file_name.parent
        tsl_file_includes = [f"\"{Path(os.path.relpath(Path(included_file.file_name), current_path))}\"" for
                             included_file in self.__data_dict["tsl_file_includes"]]
        self.__data_dict["includes"].extend(
            [tsl_include for tsl_include in tsl_file_includes if tsl_include not in self.__data_dict["includes"]])
        return config.get_template("core::source_file").render(self.__data_dict)

    def render_to_file(self) -> None:
        self.__filename.write_text(self.render())

    @staticmethod
    @requirement(filename="NotNone", data_dict="NotNone")
    def create_from_dict(filename: Path, data_dict: YamlDataType) -> TSLSourceFile:
        new_data_dict: YamlDataType = {
            "file_name": filename,
            "tsl_license": config.get_template("license").render({"year": datetime.date.today().year}),
            "tsl_file_doxygen": config.get_template("core::doxygen_file").render(
                {
                    "file_name": filename,
                    "date": datetime.date.today(),
                    "file_description": data_dict["description"] if "description" in data_dict else ""
                }
            ),
            "tsl_namespace": config.get_config_entry("namespace"),
            "tsl_file_includes": [],
            "includes": [],
            "codes": []
        }
        return TSLSourceFile(filename, {**new_data_dict, **data_dict})
