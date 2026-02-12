# filepath: /src/fedfred/fraser/objects.py
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

from typing import List, Optional, Union
from dataclasses import dataclass

@dataclass
class PhysicalDescription:
    form: Optional[str]
    digital_origin: Optional[str]

@dataclass
class Location:
    api_url: str
    url: str

@dataclass
class OriginInfo:
    date_issued: Optional[List[str]]
    issuance: Optional[str]
    frequency: Optional[str]

@dataclass
class NameInfo:
    role: Optional[str]
    record_info: Optional['RecordInfo']
    name_part: str

@dataclass
class Classification:
    authority: str

@dataclass
class TitleInfo:
    title: str

@dataclass
class RecordInfo:
    record_identifier: Optional[Union[List[str], int]]
    record_type: Optional[str]
    record_updated_date: Optional[str]
    record_creation_date: Optional[str]

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
    geographic: Optional[List[Geographic]]
    topic: Optional[List[Topic]]
    theme: Optional[List[Theme]]

@dataclass
class Record:
    identifier: str
    format: str
    limit: int
    start: int
    page: int
    fields: str
    subject: Optional[Subject]
    title_info: Optional[List[TitleInfo]]
    access_condition: str
    language: List[str]
    abstract: List[str]
    type_of_resource: str
    related_item: Optional[List[RecordInfo]]
    classification: Optional[List[Classification]]
    record_info: Optional[RecordInfo]
    name: Optional[List[NameInfo]]
    genre: List[str]
    origin_info: Optional[OriginInfo]
    location: Optional[Location]
    physical_description: Optional[PhysicalDescription]

@dataclass
class Title:
    records: List[Record]
    limit: int
    start: int
    page: int
