# Copyright (c) 2022 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Handle writing of inherited statements to markdown."""
import logging
import pathlib
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import trestle.common.const as const
import trestle.core.generators as gens
import trestle.oscal.ssp as ssp
from trestle.common.err import TrestleError
from trestle.core.markdown.docs_markdown_node import DocsMarkdownNode
from trestle.core.markdown.markdown_api import MarkdownAPI
from trestle.core.markdown.md_writer import MDWriter

logger = logging.getLogger(__name__)

component_mapping_default: List[Dict[str, str]] = [{'name': const.REPLACE_ME}]


class LeveragedStatements(ABC):
    """Abstract class for managing leveraged statements."""

    def __init__(self):
        """Initialize the class."""
        self._md_file: Optional[MDWriter] = None
        self.header_comment_dict: Dict[str, str] = {
            const.TRESTLE_LEVERAGING_COMP_TAG: const.YAML_LEVERAGING_COMP_COMMENT,
            const.TRESTLE_STATEMENT_TAG: const.YAML_LEVERAGED_COMMENT
        }
        self.merged_header_dict: Dict[str, Any] = {
            const.TRESTLE_STATEMENT_TAG: '', const.TRESTLE_LEVERAGING_COMP_TAG: component_mapping_default
        }

    @abstractmethod
    def write_statement_md(self, leveraged_statement_file: pathlib.Path) -> None:
        """Write inheritance information to a single markdown file."""


class StatementTree(LeveragedStatements):
    """Concrete class for managing provided and responsibility statements."""

    def __init__(
        self, provided_uuid: str, provided_description: str, responsibility_uuid: str, responsibility_description: str
    ):
        """Initialize the class."""
        self.provided_uuid = provided_uuid
        self.provided_description = provided_description
        self.responsibility_uuid = responsibility_uuid
        self.responsibility_description = responsibility_description
        self.satisfied_description = ''
        super().__init__()

    def write_statement_md(self, leveraged_statement_file: pathlib.Path) -> None:
        """Write a provided and responsibility statements to a markdown file."""
        self._md_file = MDWriter(leveraged_statement_file, self.header_comment_dict)

        if self._md_file.exists():
            return self.update_statement_md(leveraged_statement_file)

        self._add_generated_content()
        self._md_file.write_out()

    def update_statement_md(self, leveraged_statement_file: pathlib.Path) -> None:
        """Update provided and responsibility statements in a markdown file."""
        md_reader = InheritanceMarkdownReader(leveraged_statement_file)

        self.merged_header_dict[const.TRESTLE_LEVERAGING_COMP_TAG] = md_reader.get_leveraged_component_header_value()

        satisfied_description = md_reader.get_satisfied_description()
        if satisfied_description is not None:
            self.satisfied_description = satisfied_description

        self._add_generated_content()
        self._md_file.write_out()

    def _add_generated_content(self):
        statement_dict: Dict[str, str] = {
            const.PROVIDED_UUID: self.provided_uuid, const.RESPONSIBILITY_UUID: self.responsibility_uuid
        }

        self.merged_header_dict[const.TRESTLE_STATEMENT_TAG] = statement_dict
        self._md_file.add_yaml_header(self.merged_header_dict)

        self._md_file.new_header(level=1, title=const.PROVIDED_STATEMENT_DESCRIPTION)
        self._md_file.new_line(self.provided_description)
        self._md_file.new_header(level=1, title=const.RESPONSIBILITY_STATEMENT_DESCRIPTION)
        self._md_file.new_line(self.responsibility_description)
        self._md_file.new_header(level=1, title=const.SATISFIED_STATEMENT_DESCRIPTION)
        self._md_file.new_line(const.SATISFIED_STATEMENT_COMMENT)
        self._md_file.new_line(self.satisfied_description)


class StatementProvided(LeveragedStatements):
    """Concrete class for managing provided statements."""

    def __init__(self, provided_uuid: str, provided_description: str):
        """Initialize the class."""
        self.provided_uuid = provided_uuid
        self.provided_description = provided_description
        super().__init__()

    def write_statement_md(self, leveraged_statement_file: pathlib.Path) -> None:
        """Write provided statements to a markdown file."""
        self._md_file = MDWriter(leveraged_statement_file, self.header_comment_dict)

        if self._md_file.exists():
            return self.update_statement_md(leveraged_statement_file)

        self._add_generated_content()
        self._md_file.write_out()

    def update_statement_md(self, leveraged_statement_file: pathlib.Path) -> None:
        """Update provided statements in a markdown file."""
        md_reader = InheritanceMarkdownReader(leveraged_statement_file)

        self.merged_header_dict[const.TRESTLE_LEVERAGING_COMP_TAG] = md_reader.get_leveraged_component_header_value()

        self._add_generated_content()
        self._md_file.write_out()

    def _add_generated_content(self):
        self.merged_header_dict[const.TRESTLE_STATEMENT_TAG] = {const.PROVIDED_UUID: self.provided_uuid}
        self._md_file.add_yaml_header(self.merged_header_dict)

        self._md_file.new_header(level=1, title=const.PROVIDED_STATEMENT_DESCRIPTION)
        self._md_file.new_line(self.provided_description)


class StatementResponsibility(LeveragedStatements):
    """Concrete class for managing responsibility statements."""

    def __init__(self, responsibility_uuid: str, responsibility_description: str):
        """Initialize the class."""
        self.responsibility_uuid = responsibility_uuid
        self.responsibility_description = responsibility_description
        self.satisfied_description = ''
        super().__init__()

    def write_statement_md(self, leveraged_statement_file: pathlib.Path) -> None:
        """Write responsibility statements to a markdown file."""
        self._md_file = MDWriter(leveraged_statement_file, self.header_comment_dict)

        if self._md_file.exists():
            return self.update_statement_md(leveraged_statement_file)

        self._add_generated_content()
        self._md_file.write_out()

    def update_statement_md(self, leveraged_statement_file: pathlib.Path) -> None:
        """Update responsibility statements in a markdown file."""
        md_reader = InheritanceMarkdownReader(leveraged_statement_file)

        self.merged_header_dict[const.TRESTLE_LEVERAGING_COMP_TAG] = md_reader.get_leveraged_component_header_value()

        satisfied_description = md_reader.get_satisfied_description()
        if satisfied_description is not None:
            self.satisfied_description = satisfied_description

        self._add_generated_content()
        self._md_file.write_out()

    def _add_generated_content(self):
        self.merged_header_dict[const.TRESTLE_STATEMENT_TAG] = {const.RESPONSIBILITY_UUID: self.responsibility_uuid}
        self._md_file.add_yaml_header(self.merged_header_dict)

        self._md_file.new_header(level=1, title=const.RESPONSIBILITY_STATEMENT_DESCRIPTION)
        self._md_file.new_line(self.responsibility_description)
        self._md_file.new_header(level=1, title=const.SATISFIED_STATEMENT_DESCRIPTION)
        self._md_file.new_line(const.SATISFIED_STATEMENT_COMMENT)
        self._md_file.new_line(self.satisfied_description)


class InheritanceMarkdownReader:
    """Class to read leveraged statement information from Markdown."""

    def __init__(self, leveraged_statement_file: str):
        """Initialize the class."""
        # Save the file name for logging
        self._leveraged_statement_file = leveraged_statement_file

        md_api: MarkdownAPI = MarkdownAPI()

        yaml_header, inheritance_md = md_api.processor.process_markdown(leveraged_statement_file)
        self._yaml_header: Dict[str, Any] = yaml_header
        self._inheritance_md: DocsMarkdownNode = inheritance_md

    def process_leveraged_statement_markdown(
        self
    ) -> Optional[Tuple[List[str], Optional[ssp.Inherited], Optional[ssp.Satisfied]]]:
        """
        Read inheritance information from Markdown.

        Returns:
        Tuple: An list of mapped component titles, a satisfied statement and an inherited statement

        Notes:
            Returns inheritance information in the context of the leveraging SSP.
        """
        leveraging_comps: List[str] = []
        inherited_statement: Optional[ssp.Inherited] = None
        satisfied_statement: Optional[ssp.Satisfied] = None

        leveraging_comp_header_value: List[Dict[str, str]] = self._yaml_header[const.TRESTLE_LEVERAGING_COMP_TAG]

        # If there are no mapped components, return early
        if not leveraging_comp_header_value or leveraging_comp_header_value == component_mapping_default:
            return None
        else:
            for comp_dicts in leveraging_comp_header_value:
                for comp_title in comp_dicts.values():
                    leveraging_comps.append(comp_title)

        statement_info: Dict[str, str] = self._yaml_header[const.TRESTLE_STATEMENT_TAG]

        if const.PROVIDED_UUID in statement_info:
            # Set inherited

            provided_description = self.get_provided_description()
            if provided_description is None:
                raise TrestleError(f'Provided statement cannot be empty in {self._leveraged_statement_file}')

            inherited_statement = gens.generate_sample_model(ssp.Inherited)

            inherited_statement.description = provided_description
            inherited_statement.provided_uuid = statement_info[const.PROVIDED_UUID]

        if const.RESPONSIBILITY_UUID in statement_info:
            # Set satisfied
            satisfied_description = self.get_satisfied_description()
            if satisfied_description is None:
                raise TrestleError(f'Satisfied statement cannot be empty in {self._leveraged_statement_file}')

            satisfied_statement = gens.generate_sample_model(ssp.Satisfied)

            satisfied_statement.description = satisfied_description
            satisfied_statement.responsibility_uuid = statement_info[const.RESPONSIBILITY_UUID]

        return (leveraging_comps, inherited_statement, satisfied_statement)

    def get_satisfied_description(self) -> Optional[str]:
        """Return the satisfied description in the Markdown."""
        node = self._inheritance_md.get_node_for_key(const.SATISFIED_STATEMENT_DESCRIPTION, False)
        if node is not None:
            return self.strip_heading_and_comments(node.content.raw_text)
        else:
            return None

    def get_provided_description(self) -> Optional[str]:
        """Return the provided description in the Markdown."""
        node = self._inheritance_md.get_node_for_key(const.PROVIDED_STATEMENT_DESCRIPTION, False)
        if node is not None:
            return self.strip_heading_and_comments(node.content.raw_text)
        else:
            return None

    def get_leveraged_component_header_value(self) -> Dict[str, str]:
        """Provide the leveraged component value in the yaml header."""
        return self._yaml_header[const.TRESTLE_LEVERAGING_COMP_TAG]

    @staticmethod
    def strip_heading_and_comments(markdown_text: str) -> str:
        """Remove the heading and comments from lines to get the multi-line paragraph."""
        heading_pattern = r'^#+.*$'
        comment_pattern = r'<!--.*?-->'

        # Remove headings and comments
        markdown_text = re.sub(heading_pattern, '', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(comment_pattern, '', markdown_text, flags=re.DOTALL)

        markdown_text = '\n'.join(line.strip() for line in markdown_text.splitlines())

        # Remove consecutive empty lines
        markdown_text = re.sub(r'\n{2,}', '\n\n', markdown_text)

        return markdown_text.strip()
