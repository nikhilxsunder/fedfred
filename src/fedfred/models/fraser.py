# filepath: /src/fedfred/models/fraser.py
#
# Copyright (c) 2026 Nikhil Sunder
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from dataclasses import dataclass
from typing import Optional


@dataclass
class PhysicalDescription:
    form: str | None
    digital_origin: str | None


@dataclass
class Location:
    api_url: str
    url: str


@dataclass
class OriginInfo:
    date_issued: list[str] | None
    issuance: str | None
    frequency: str | None


@dataclass
class NameInfo:
    role: str | None
    record_info: Optional["RecordInfo"]
    name_part: str


@dataclass
class Classification:
    authority: str


@dataclass
class TitleInfo:
    title: str


@dataclass
class RecordInfo:
    record_identifier: list[str] | int | None
    record_type: str | None
    record_updated_date: str | None
    record_creation_date: str | None


@dataclass
class Theme:
    theme: str
    record_info: RecordInfo


@dataclass
class Topic:
    topic: str
    record_info: RecordInfo


@dataclass
class Geographic:
    geographic: str
    record_info: RecordInfo


@dataclass
class Subject:
    geographic: list[Geographic] | None
    topic: list[Topic] | None
    theme: list[Theme] | None


@dataclass
class Record:
    identifier: str
    format: str
    limit: int
    start: int
    page: int
    fields: str
    subject: Subject | None
    title_info: list[TitleInfo] | None
    access_condition: str
    language: list[str]
    abstract: list[str]
    type_of_resource: str
    related_item: list[RecordInfo] | None
    classification: list[Classification] | None
    record_info: RecordInfo | None
    name: list[NameInfo] | None
    genre: list[str]
    origin_info: OriginInfo | None
    location: Location | None
    physical_description: PhysicalDescription | None


@dataclass
class Title:
    records: list[Record]
    limit: int
    start: int
    page: int
