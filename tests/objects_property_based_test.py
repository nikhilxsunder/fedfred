# filepath: /test/objects_property_based_test.py
#
# Copyright (c) 2025 Nikhil Sunder
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
Comprehensive property based tests for the objects module.
"""

from hypothesis import given, strategies as st
from fedfred.objects import Category, Series, Tag, Release, ReleaseDate, Source, Element, VintageDate, SeriesGroup
from fedfred.__about__ import __title__, __version__, __author__, __license__, __copyright__, __description__, __url__

@given(
    id=st.integers(min_value=1, max_value=1000),
    name=st.text(min_size=1, max_size=50),
    parent_id=st.one_of(st.none(), st.integers(min_value=1, max_value=1000)),
)
def test_category_initialization(id, name, parent_id):
    category = Category(id=id, name=name, parent_id=parent_id)
    assert category.id == id
    assert category.name == name
    assert category.parent_id == parent_id

@given(
    id=st.text(min_size=1, max_size=50),
    title=st.text(min_size=1, max_size=50),
    observation_start=st.text(min_size=1, max_size=50),
    observation_end=st.text(min_size=1, max_size=50),
    frequency=st.text(min_size=1, max_size=50),
    frequency_short=st.text(min_size=1, max_size=50),
    units=st.text(min_size=1, max_size=50),
    units_short=st.text(min_size=1, max_size=50),
    seasonal_adjustment=st.text(min_size=1, max_size=50),
    seasonal_adjustment_short=st.text(min_size=1, max_size=50),
    last_updated=st.text(min_size=1, max_size=50),
    popularity=st.integers(min_value=1, max_value=1000),
    realtime_start=st.one_of(st.text(min_size=1, max_size=50), st.none()),
    realtime_end=st.one_of(st.text(min_size=1, max_size=50), st.none()),
    group_popularity=st.one_of(st.integers(min_value=1, max_value=1000), st.none()),
    notes=st.one_of(st.text(min_size=1, max_size=50), st.none()),
)
def test_series_initialization(
    id,
    title,
    observation_start,
    observation_end,
    frequency,
    frequency_short,
    units,
    units_short,
    seasonal_adjustment,
    seasonal_adjustment_short,
    last_updated,
    popularity,
    realtime_start,
    realtime_end,
    group_popularity,
    notes
):
    series = Series(
        id=id,
        title=title,
        observation_start=observation_start,
        observation_end=observation_end,
        frequency=frequency,
        frequency_short=frequency_short,
        units=units,
        units_short=units_short,
        seasonal_adjustment=seasonal_adjustment,
        seasonal_adjustment_short=seasonal_adjustment_short,
        last_updated=last_updated,
        popularity=popularity,
        realtime_start=realtime_start,
        realtime_end=realtime_end,
        group_popularity=group_popularity,
        notes=notes
    )

    assert series.id == id
    assert series.title == title
    assert series.observation_start == observation_start
    assert series.observation_end == observation_end
    assert series.frequency == frequency
    assert series.frequency_short == frequency_short
    assert series.units == units
    assert series.units_short == units_short
    assert series.seasonal_adjustment == seasonal_adjustment
    assert series.seasonal_adjustment_short == seasonal_adjustment_short
    assert series.last_updated == last_updated
    assert series.popularity == popularity
    assert series.realtime_start == realtime_start
    assert series.realtime_end == realtime_end
    assert series.group_popularity == group_popularity

@given(
    name=st.text(min_size=1, max_size=50),
    group_id=st.text(min_size=1, max_size=50),
    created=st.text(min_size=1, max_size=50),
    popularity=st.integers(min_value=1, max_value=1000),
    series_count=st.integers(min_value=1, max_value=1000),
    notes=st.one_of(st.text(min_size=1, max_size=50), st.none())
)
def test_tag_initialization(
    name,
    group_id,
    created,
    popularity,
    series_count,
    notes
):
    tag = Tag(
        name=name,
        group_id=group_id,
        created=created,
        popularity=popularity,
        series_count=series_count,
        notes=notes
    )

    assert tag.name == name
    assert tag.group_id == group_id
    assert tag.created == created
    assert tag.popularity == popularity
    assert tag.series_count == series_count
    assert tag.notes == notes

@given(
    id=st.integers(min_value=1, max_value=1000),
    realtime_start=st.text(min_size=1, max_size=50),
    realtime_end=st.text(min_size=1, max_size=50),
    name=st.text(min_size=1, max_size=50),
    press_release=st.booleans(),
    link=st.one_of(st.text(min_size=1, max_size=50), st.none()),
    notes=st.one_of(st.text(min_size=1, max_size=50), st.none()),
)
def test_release_initialization(
    id,
    realtime_start,
    realtime_end,
    name,
    press_release,
    link,
    notes
):
    release = Release(
        id=id,
        realtime_start=realtime_start,
        realtime_end=realtime_end,
        name=name,
        press_release=press_release,
        link=link,
        notes=notes
    )

    assert release.id == id
    assert release.realtime_start == realtime_start
    assert release.realtime_end == realtime_end
    assert release.name == name
    assert release.press_release == press_release
    assert release.link == link
    assert release.notes == notes

@given(
    release_id=st.integers(min_value=1, max_value=1000),
    date=st.text(min_size=1, max_size=50),
    release_name=st.one_of(st.text(min_size=1, max_size=50), st.none()),
)
def test_release_date_initialization(
    release_id,
    date,
    release_name
):
    release_date = ReleaseDate(
        release_id=release_id,
        date=date,
        release_name=release_name
    )

    assert release_date.release_id == release_id
    assert release_date.date == date
    assert release_date.release_name == release_name

@given(
    id=st.integers(min_value=1, max_value=1000),
    realtime_start=st.text(min_size=1, max_size=50),
    realtime_end=st.text(min_size=1, max_size=50),
    name=st.text(min_size=1, max_size=50),
    link=st.one_of(st.text(min_size=1, max_size=50), st.none()),
    notes=st.one_of(st.text(min_size=1, max_size=50), st.none()),
)
def test_source_initialization(
    id,
    realtime_start,
    realtime_end,
    name,
    link,
    notes
):
    source = Source(
        id=id,
        realtime_start=realtime_start,
        realtime_end=realtime_end,
        name=name,
        link=link,
        notes=notes
    )

    assert source.id == id
    assert source.realtime_start == realtime_start
    assert source.realtime_end == realtime_end
    assert source.name == name
    assert source.link == link
    assert source.notes == notes

@given(
    element_id=st.integers(min_value=1, max_value=1000),
    release_id=st.integers(min_value=1, max_value=1000),
    series_id=st.text(min_size=1, max_size=50),
    parent_id=st.integers(min_value=1, max_value=1000),
    line=st.text(min_size=1, max_size=50),
    type=st.text(min_size=1, max_size=50),
    name=st.text(min_size=1, max_size=50),
    level=st.text(min_size=1, max_size=50),
    children=st.one_of(st.lists(st.builds(Element)), st.none()),
)
def test_element_initialization(
    element_id,
    release_id,
    series_id,
    parent_id,
    line,
    type,
    name,
    level,
    children
):
    element = Element(
        element_id=element_id,
        release_id=release_id,
        series_id=series_id,
        parent_id=parent_id,
        line=line,
        type=type,
        name=name,
        level=level,
        children=children
    )

    assert element.element_id == element_id
    assert element.release_id == release_id
    assert element.series_id == series_id
    assert element.parent_id == parent_id
    assert element.line == line
    assert element.type == type
    assert element.name == name
    assert element.level == level
    assert element.children == children

@given(
    vintage_date=st.text(min_size=1, max_size=50),
)
def test_vintage_date_initialization(vintage_date):
    vintage = VintageDate(
        vintage_date=vintage_date
    )

    assert vintage.vintage_date == vintage_date

@given(
    title=st.text(min_size=1, max_size=50),
    region_type=st.text(min_size=1, max_size=50),
    series_group=st.text(min_size=1, max_size=50),
    season=st.text(min_size=1, max_size=50),
    units=st.text(min_size=1, max_size=50),
    frequency=st.text(min_size=1, max_size=50),
    min_date=st.text(min_size=1, max_size=50),
    max_date=st.text(min_size=1, max_size=50),
)
def test_series_group_initialization(
    title,
    region_type,
    series_group,
    season,
    units,
    frequency,
    min_date,
    max_date
):
    series_groups = SeriesGroup(
        title=title,
        region_type=region_type,
        series_group=series_group,
        season=season,
        units=units,
        frequency=frequency,
        min_date=min_date,
        max_date=max_date
    )

    assert series_groups.title == title
    assert series_groups.region_type == region_type
    assert series_groups.series_group == series_group
    assert series_groups.season == season
    assert series_groups.units == units
    assert series_groups.frequency == frequency
    assert series_groups.min_date == min_date
    assert series_groups.max_date == max_date
