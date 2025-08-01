# -*- coding: utf-8 -*-
"""Compile HTML data for Help, Abbreviations, Thanks & Bibliography."""

import csv
from typing import Dict, List, Tuple

from mako.template import Template
from minify_html import minify
from sqlalchemy.orm import Session

from tools.css_manager import CSSManager
from tools.goldendict_exporter import DictEntry
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dict, read_tsv_dot_dict
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces


class Abbreviation:
    """defining the abbreviations.tsv columns"""

    def __init__(
        self,
        abbrev,
        meaning,
        pali,
        example,
        information,
    ):
        self.abbrev = abbrev
        self.meaning = meaning
        self.pali = pali
        self.example = example
        self.information = information

    def __repr__(self) -> str:
        return f"Abbreviation: {self.abbrev} {self.meaning} {self.pali} ..."


class Help:
    """defining the help.tsv columns"""

    def __init__(
        self,
        help,
        meaning,
    ):
        self.help = help
        self.meaning = meaning

    def __repr__(self) -> str:
        return f"Help: {self.help} {self.meaning}  ..."


def generate_help_html(
    __db_session__: Session,
    pth: ProjectPaths,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generating html of all help files used in the dictionary"""
    pr.green("generating help html")

    size_dict = default_rendered_sizes()

    # 1. abbreviations
    # 2. contextual help
    # 3. thank yous
    # 4. bibliography

    header_templ = Template(filename=str(pth.dpd_header_plain_templ_path))
    header = str(header_templ.render())

    # Add Variables and fonts
    css_manager = CSSManager()
    header = css_manager.update_style(header, "secondary")

    help_data_list: List[DictEntry] = []

    abbrev = add_abbrev_html(pth, header)
    help_data_list.extend(abbrev)
    size_dict["help"] += len(str(abbrev))

    help_html = add_help_html(pth, header)
    help_data_list.extend(help_html)
    size_dict["help"] += len(str(help_html))

    bibliography = add_bibliography(pth, header)
    help_data_list.extend(bibliography)
    size_dict["help"] += len(str(bibliography))

    thanks = add_thanks(pth, header)
    help_data_list.extend(thanks)
    size_dict["help"] += len(str(thanks))

    pr.yes(len(help_data_list))
    return help_data_list, size_dict


def add_abbrev_html(
    pth: ProjectPaths,
    header: str,
) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.abbreviations_tsv_path
    rows = read_tsv_dict(file_path)

    rows2 = []
    with open(pth.abbreviations_tsv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows2.append(row)

    assert rows == rows2

    def _csv_row_to_abbreviations(x: Dict[str, str]) -> Abbreviation:
        return Abbreviation(
            abbrev=x["abbrev"],
            meaning=x["meaning"],
            pali=x["pāli"],
            example=x["example"],
            information=x["explanation"],
        )

    items = list(map(_csv_row_to_abbreviations, rows))

    for i in items:
        html = ""
        html += "<body>"
        html += render_abbrev_templ(pth, i)
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        word = i.abbrev

        res = DictEntry(
            word=word,
            definition_html=html,
            definition_plain="",
            synonyms=[],
        )

        help_data_list.append(res)

    return help_data_list


def add_help_html(
    pth: ProjectPaths,
    header: str,
) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.help_tsv_path
    rows = read_tsv_dict(file_path)

    rows2 = []
    with open(pth.help_tsv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows2.append(row)

    assert rows == rows2

    def _csv_row_to_help(x: Dict[str, str]) -> Help:
        return Help(
            help=x["help"],
            meaning=x["meaning"],
        )

    items = list(map(_csv_row_to_help, rows))

    for i in items:
        html = ""
        html += "<body>"
        html += render_help_templ(pth, i)
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        word = i.help

        res = DictEntry(
            word=word,
            definition_html=html,
            definition_plain="",
            synonyms=[],
        )

        help_data_list.append(res)

    return help_data_list


def add_bibliography(pth: ProjectPaths, header: str) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.bibliography_tsv_path
    bibliography_dict = read_tsv_dot_dict(file_path)

    html = ""
    html += "<body>"
    html += "<div class='tertiary'>"
    html += "<h2>Bibliography</h1>"

    # i = current item, n = next item
    for x in range(len(bibliography_dict)):
        i = bibliography_dict[x]
        if x + 1 > len(bibliography_dict) - 1:
            break
        else:
            n = bibliography_dict[x + 1]

        if i.category:
            html += f"<h3>{i.category}</h3>"
            html += "<ul>"
        if i.surname:
            html += f"<li><b>{i.surname}</b>"
        if i.firstname:
            html += f", {i.firstname}"
        if i.year:
            html += f", {i.year}"
        if i.title:
            html += f". <i>{i.title}</i>"
        if i.city and i.publisher:
            html += f", {i.city}: {i.publisher}"
        if not i.city and i.publisher:
            html += f", {i.publisher}"
        if i.site:
            html += (
                f", accessed through <a href='{i.site}'  target='_blank'>{i.site}</a>"
            )
        if i.surname:
            html += "</li>"

        if n.category:
            html += "</ul>"

    html += "</div></body></html>"

    html = squash_whitespaces(header) + minify(html)

    synonyms = ["dpd bibliography", "bibliography", "bib"]

    res = DictEntry(
        word="bibliography",
        definition_html=html,
        definition_plain="",
        synonyms=synonyms,
    )

    help_data_list.append(res)

    return help_data_list


def add_thanks(pth: ProjectPaths, header: str) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.thanks_tsv_path
    thanks = read_tsv_dot_dict(file_path)

    html = ""
    html += "<body>"
    html += "<div class='tertiary'>"

    # i = current item, n = next item
    for x in range(len(thanks)):
        i = thanks[x]
        if x + 1 > len(thanks) - 1:
            break
        else:
            n = thanks[x + 1]

        if i.category:
            html += f"<h2>{i.category}</h2>"
            html += f"<p>{i.what}</p>"
            html += "<ul>"
        if i.who:
            html += f"<li><b>{i.who}</b>"
        if i.where:
            html += f" {i.where}"
        if i.what and not i.category:
            html += f" {i.what}"
        if i.who:
            html += "</li>"

        if n.category:
            html += "</ul>"

    html += "</div></body></html>"

    html = squash_whitespaces(header) + minify(html)

    synonyms = ["dpd thanks", "thankyou", "thanks", "anumodana"]

    res = DictEntry(
        word="thanks",
        definition_html=html,
        definition_plain="",
        synonyms=synonyms,
    )

    help_data_list.append(res)

    return help_data_list


def render_abbrev_templ(
    pth: ProjectPaths,
    i: Abbreviation,
) -> str:
    """render html of abbreviations"""

    abbrev_templ = Template(filename=str(pth.abbrev_templ_path))

    return str(abbrev_templ.render(i=i))


def render_help_templ(
    pth: ProjectPaths,
    i: Help,
) -> str:
    """render html of help"""

    help_templ = Template(filename=str(pth.help_templ_path))

    return str(help_templ.render(i=i))
