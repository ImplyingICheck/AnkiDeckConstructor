# Copyright 2023 The Gaggle Authors. All Rights Reserved.
#
# This file is part of Gaggle.
#
# Gaggle is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Gaggle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Gaggle. If not, see <https://www.gnu.org/licenses/>.
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# Bug when using open() with **kwargs. Fixed in 2.17.5
# pylint: disable=unspecified-encoding
# pylint: disable=line-too-long
import collections
import csv
import io
import warnings
from typing import cast

import pytest
import pytest_cases.filters
# pytest_cases.fixture used as helper functions. Must be imported otherwise, the
# function is not discovered during test collection.
from test_gaggle.case_ankicard import *  # pylint: disable=wildcard-import,unused-wildcard-import # pyright: ignore [reportMissingImports]
from .conftest import new_header_gaggle_format, new_field_names_remove_reserved, falsy_values_hashable  # pylint: disable=relative-beyond-top-level

from gaggle import gaggle
from gaggle import exceptions

_CASES = 'test_gaggle.case_ankicard'

TSV_FILE_ENCODING = gaggle._ANKI_EXPORT_ENCODING
TSV_FILE_DIALECT = gaggle._ANKI_EXPORT_CONTENT_DIALECT
EXCLUSIVE_OPEN_PARAMS = gaggle.EXCLUSIVE_OPEN_PARAMS
READ_PARAMS = gaggle.READ_PARAMS
WRITE_PARAMS: gaggle.OpenOptions = {
    'mode': 'w',
    'encoding': TSV_FILE_ENCODING,
    'newline': ''
}


@pytest_cases.fixture
@pytest_cases.parametrize('property_name', [
    'guid',
    'note_type',
    'deck_name',
    'tags',
])
def reserved_names_as_property_name(property_name):
  return property_name


@pytest_cases.fixture
@pytest_cases.parametrize(
    'field_name', [falsy_values_hashable, 'This field name does not exist'])
def nonexistent_field_names(field_name):
  return field_name


@pytest_cases.fixture
@pytest_cases.parametrize_with_cases(
    'anki_card_components',
    cases=_CASES,
    has_tag=['WellFormed', 'AnkiCardComponents'])
def generate_field_dict_well_formed(anki_card_components):
  generated_field_dict = gaggle._generate_field_dict(
      anki_card_components.field_names, anki_card_components.fields,
      anki_card_components.reserved_names,
      set(anki_card_components.reserved_names.values()))
  components = anki_card_components
  return generated_field_dict, components


@pytest_cases.fixture
@pytest_cases.parametrize_with_cases(
    'anki_card_components_constructor',
    cases=_CASES,
    has_tag=['AnkiCardComponentsConstructor'])
def generate_unique_field_names_constructor(anki_card_components_constructor,):

  def generate_unique_field_names_helper(field_names=None):
    anki_card_components = anki_card_components_constructor(
        field_names=field_names)
    return list(
        gaggle._generate_unique_field_names(
            anki_card_components.field_names, anki_card_components.fields,
            anki_card_components.reserved_names,
            set(anki_card_components.reserved_names.values()))
    ), anki_card_components.expected_field_names

  return generate_unique_field_names_helper


@pytest.mark.filterwarnings('ignore')
@pytest_cases.parametrize_with_cases(
    'fields',
    cases=_CASES,
    has_tag=['Fields'],
    prefix='fields',
)
@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    filter=pytest_cases.filters.has_tag('FieldNames')
    & ~pytest_cases.filters.has_tag('UsageBeforeAssignment'),
    prefix='field_names',
)
@pytest_cases.parametrize_with_cases(
    'has_html',
    cases=_CASES,
    has_tag=['HasHtml', 'Well-Formed'],
    prefix='has_html',
)
@pytest_cases.parametrize_with_cases(
    'tags_idx',
    cases=_CASES,
    has_tag=['TagsIdx'],
    prefix='tags_idx',
)
@pytest_cases.parametrize_with_cases(
    'note_type_idx',
    cases=_CASES,
    has_tag=['NoteTypeIdx'],
    prefix='note_type_idx',
)
@pytest_cases.parametrize_with_cases(
    'deck_idx',
    cases=_CASES,
    has_tag=['GuidIdx'],
    prefix='guid_idx',
)
@pytest_cases.parametrize_with_cases(
    'guid_idx',
    cases=_CASES,
    has_tag=['DeckIdx'],
    prefix='deck_idx',
)
def test_anki_card_init_generic_arguments(
    fields,
    field_names,
    has_html,
    tags_idx,
    note_type_idx,
    deck_idx,
    guid_idx,
):
  card = gaggle.AnkiCard(fields, field_names, has_html, tags_idx, note_type_idx,
                         deck_idx, guid_idx)
  assert card


@pytest_cases.parametrize_with_cases(
    'anki_card', cases=_CASES, has_tag=['FullySpecified', 'AnkiCard'])
def test_reserved_names_specified_returns_value(
    anki_card,
    reserved_names_as_property_name,
):
  assert hasattr(anki_card, reserved_names_as_property_name)


@pytest_cases.parametrize_with_cases(
    'anki_card', cases=_CASES, has_tag=['Minimum', 'AnkiCard'])
def test_reserved_names_not_specified_raises_key_error(
    anki_card,
    reserved_names_as_property_name,
):
  with pytest.raises(KeyError):
    hasattr(anki_card, reserved_names_as_property_name)


@pytest.mark.filterwarnings('ignore')
@pytest_cases.parametrize_with_cases(
    'anki_card_components',
    cases=_CASES,
    has_tag=['WellFormed', 'AnkiCardComponents'])
def test_get_field_existing_field(anki_card_components,):
  anki_card = anki_card_components.new_anki_card()
  for expected_field_name, expected_field_value in zip(
      anki_card_components.expected_field_names,
      anki_card_components.fields,
      strict=True,
  ):
    assert anki_card.get_field(expected_field_name) == expected_field_value


@pytest.mark.filterwarnings('ignore')
@pytest_cases.parametrize_with_cases(
    'anki_card', cases=_CASES, has_tag=['WellFormed', 'AnkiCard'])
def test_get_field_non_existing_field(anki_card, nonexistent_field_names):
  with pytest.raises(KeyError):
    anki_card.get_field(nonexistent_field_names)


@pytest.mark.filterwarnings('ignore')
@pytest_cases.parametrize_with_cases(
    'anki_card_components',
    cases=_CASES,
    has_tag=['WellFormed', 'AnkiCardComponents'])
def test_as_str_list_content_matches(anki_card_components):
  anki_card = anki_card_components.new_anki_card()
  test_set = collections.Counter(anki_card.as_str_list())
  expected_set = collections.Counter(anki_card_components.expected_fields)
  assert test_set == expected_set


@pytest.mark.filterwarnings('ignore')
@pytest_cases.parametrize_with_cases(
    'anki_card_components',
    cases=_CASES,
    has_tag=['WellFormed', 'AnkiCardComponents'])
def test_as_str_list_order_matches(anki_card_components):
  anki_card = anki_card_components.new_anki_card()
  expected_fields = anki_card_components.expected_fields
  assert anki_card.as_str_list() == expected_fields


# TODO: Reformat as Open File, Write to Output Stream, Close Output Stream tests
@pytest_cases.parametrize_with_cases(
    'anki_card_components',
    cases=_CASES,
    has_tag=['WellFormed', 'AnkiCardComponents'])
def test_write_as_tsv_csv_writer_one_line(
    tmp_path,
    anki_card_components,
):
  file = tmp_path / 'test_write_as_tsv_csv_writer_one_line.txt'
  anki_card = anki_card_components.new_anki_card()
  expected_write_output = anki_card_components.expected_fields
  with open(file, **WRITE_PARAMS) as f:
    w = csv.writer(f, dialect=TSV_FILE_DIALECT)
    anki_card.write_as_tsv(w)
  with open(file, **READ_PARAMS) as f:
    r = csv.reader(f, dialect=TSV_FILE_DIALECT)
    test_card = next(r)
    assert test_card == expected_write_output


# TODO: Reformat as Open File, Write to Output Stream, Close Output Stream tests
@pytest_cases.parametrize_with_cases(
    'anki_card_components',
    cases=_CASES,
    has_tag=['WellFormed', 'AnkiCardComponents'])
def test_write_as_tsv_csv_writer_multiple_lines(
    tmp_path,
    anki_card_components,
):
  file = tmp_path / 'test_write_as_tsv_csv_writer_multiple_lines.txt'
  anki_card = anki_card_components.new_anki_card()
  expected_write_output = anki_card_components.expected_fields
  with open(file, **WRITE_PARAMS) as f:
    w = csv.writer(f, dialect=TSV_FILE_DIALECT)
    anki_card.write_as_tsv(w)
    anki_card.write_as_tsv(w)
  with open(file, **READ_PARAMS) as f:
    r = csv.reader(f, dialect=TSV_FILE_DIALECT)
    for test_card in r:
      assert test_card == expected_write_output


# TODO: Reformat as Open File, Write to Output Stream, Close Output Stream tests
@pytest_cases.parametrize_with_cases(
    'anki_card', cases=_CASES, has_tag=['WellFormed', 'AnkiCard'])
def test_write_as_tsv_no_write_permission_raises_unsupported_operation(
    tmp_path, anki_card):
  file = tmp_path / ('test_write_as_tsv_no_write_permission_raises_unsupported_'
                     'operation.txt')
  try:
    open(file, **EXCLUSIVE_OPEN_PARAMS)  #pylint: disable='consider-using-with'
  except:  # pylint: disable='bare-except'
    pytest.fail('Test file could not be created. Required to simulate improper '
                'file permissions.')
  with open(file, **READ_PARAMS) as f:
    w = csv.writer(f, dialect=TSV_FILE_DIALECT)
    with pytest.raises(io.UnsupportedOperation):
      anki_card.write_as_tsv(w)


def has_html_expected_bool(has_html_as_string):
  if has_html_as_string == 'true':
    return True
  elif has_html_as_string == 'false':
    return False
  else:
    raise ValueError


@pytest_cases.parametrize_with_cases(
    'has_html',
    cases=_CASES,
    has_tag=['HasHtml', 'Well-Formed'],
    prefix='has_html')
def test_parse_anki_header_bool_valid_input(has_html):
  expected_bool = has_html_expected_bool(has_html)
  assert gaggle._parse_anki_header_bool(has_html) == expected_bool


@pytest_cases.parametrize_with_cases(
    'has_html',
    cases=_CASES,
    has_tag=['HasHtml', 'Malformed'],
    prefix='has_html')
def test_parse_anki_header_bool_invalid_value_raises_value_error(has_html):
  with pytest.raises(ValueError):
    gaggle._parse_anki_header_bool(has_html)


@pytest.mark.filterwarnings('ignore')
def test_generate_field_dict_returns_ordered_dict(
    generate_field_dict_well_formed,):
  field_dict, anki_card_components = generate_field_dict_well_formed
  del anki_card_components  # Unused
  assert isinstance(field_dict, collections.OrderedDict)


@pytest.mark.filterwarnings('ignore')
def test_generate_field_dict_preserves_order_fields(
    generate_field_dict_well_formed,):
  field_dict, anki_card_components = generate_field_dict_well_formed
  expected_values = anki_card_components.expected_fields
  for test_value, expected_value in zip(field_dict.values(), expected_values):
    assert test_value == expected_value


@pytest.mark.filterwarnings('ignore')
def test_generate_field_dict_preserves_order_field_names(
    generate_field_dict_well_formed,):
  field_dict, anki_card_components = generate_field_dict_well_formed
  expected_names = anki_card_components.expected_field_names
  for test_value, expected_name in zip(field_dict.keys(), expected_names):
    assert test_value == expected_name


@pytest.mark.filterwarnings('ignore')
@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    filter=~pytest_cases.filters.has_tag('UsageBeforeAssignment'),
    prefix='field_names')
def test_generate_unique_field_names_length_matches_fields_length(
    field_names,
    generate_unique_field_names_constructor,
):
  """This test also guarantees that generated field_names are unique."""
  test_field_names, expected_field_names = generate_unique_field_names_constructor(
      field_names)
  assert len(test_field_names) == len(expected_field_names)


@pytest.mark.filterwarnings('ignore')
@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    filter=~pytest_cases.filters.has_tag('UsageBeforeAssignment'),
    prefix='field_names',
)
def test_generate_unique_field_names_replaces_field_names(
    field_names,
    generate_unique_field_names_constructor,
):
  test_field_names, expected_field_names = generate_unique_field_names_constructor(
      field_names)
  assert test_field_names == expected_field_names


@pytest_cases.parametrize_with_cases(
    'field_names', cases=_CASES, has_tag=['Well-Formed'], prefix='field_names')
def test_generate_unique_field_names_well_formed_no_warnings(
    field_names,
    generate_unique_field_names_constructor,
):
  with warnings.catch_warnings():
    warnings.simplefilter('error')
    generate_unique_field_names_constructor(field_names)


@pytest_cases.parametrize_with_cases(
    'field_names', cases=_CASES, has_tag=['Surplus'], prefix='field_names')
def test_generate_unique_field_names_longer_field_names_raises_leftover_argument_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.LeftoverArgumentWarning):
    generate_unique_field_names_constructor(field_names=field_names)


@pytest_cases.parametrize_with_cases(
    'field_names', cases=_CASES, has_tag=['Surplus'], prefix='field_names')
def test_generate_unique_field_names_longer_field_names_multiple_extra_raises_one_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.LeftoverArgumentWarning) as record:
    generate_unique_field_names_constructor(field_names=field_names)
  assert len(record) == 1


@pytest_cases.parametrize_with_cases(
    'field_names', cases=_CASES, has_tag=['Surplus'], prefix='field_names')
def test_generate_unique_field_names_longer_field_names_multiple_extra_returns_all_extra(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.LeftoverArgumentWarning) as record:
    test_field_names, expected_field_names = generate_unique_field_names_constructor(
        field_names)
    del test_field_names  # unused
  surplus_starting_index = len(expected_field_names)
  warning = record[0].message
  warning = cast(exceptions.LeftoverArgumentWarning, warning)
  actual_extra_field_names = warning.leftovers
  expected_extra_field_names = ' '.join(field_names[surplus_starting_index:])
  assert actual_extra_field_names == expected_extra_field_names


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['HeaderNameMismatch'],
    prefix='field_names')
def test_generate_unique_field_names_mismatched_reserved_name_raises_header_field_name_mismatch_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.HeaderFieldNameMismatchWarning):
    generate_unique_field_names_constructor(field_names=field_names)


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['HeaderNameMismatch'],
    prefix='field_names')
def test_generate_unique_field_names_multiple_mismatched_reserved_name_raises_multiple_header_field_name_mismatch_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.HeaderFieldNameMismatchWarning) as record:
    test_field_names, expected_field_names = generate_unique_field_names_constructor(
        field_names)
    del test_field_names  # unused
  # Right hand side is the number of field_names which were altered
  number_mismatches = len(set(expected_field_names) - set(field_names))
  assert len(record) == number_mismatches


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['DuplicateReservedFieldNames'],
    prefix='field_names')
def test_generate_unique_field_names_duplicate_reserved_name_raises_duplicate_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.DuplicateWarning):
    generate_unique_field_names_constructor(field_names=field_names)


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['DuplicateReservedFieldNames'],
    prefix='field_names')
def test_generate_unique_field_names_multiple_duplicate_reserved_name_raises_multiple_duplicate_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.DuplicateWarning) as record:
    test_field_names, expected_field_names = generate_unique_field_names_constructor(
        field_names)
    del test_field_names  # unused
  number_duplicate = len(expected_field_names) - len(set(field_names))
  assert len(record) == number_duplicate


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['UsageAfterAssignment'],
    prefix='field_names')
def test_generate_unique_field_names_duplicate_default_name_after_assignment_raises_duplicate_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.DuplicateWarning):
    generate_unique_field_names_constructor(field_names=field_names)


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['UsageAfterAssignment'],
    prefix='field_names')
def test_generate_unique_field_names_multiple_duplicate_default_name_after_assignment_raises_multiple_duplicate_warning(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.warns(exceptions.DuplicateWarning) as record:
    test_field_names, expected_field_names = generate_unique_field_names_constructor(
        field_names)
    del test_field_names  # unused
  number_duplicate = len(expected_field_names) - len(set(field_names))
  assert len(record) == number_duplicate


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['UsageBeforeAssignment'],
    prefix='field_names')
def test_generate_unique_field_names_duplicate_default_name_before_assignment_raises_value_error(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.raises(ValueError):
    generate_unique_field_names_constructor(field_names=field_names)


@pytest_cases.parametrize_with_cases(
    'field_names',
    cases=_CASES,
    has_tag=['UsageBeforeAssignment'],
    prefix='field_names')
def test_generate_unique_field_names_multiple_duplicate_default_name_before_assignment_raises_single_value_error(
    field_names,
    generate_unique_field_names_constructor,
):
  with pytest.raises(ValueError):
    generate_unique_field_names_constructor(field_names=field_names)


@pytest_cases.parametrize('field_names',
                          [None, new_field_names_remove_reserved])
@pytest_cases.parametrize('header', [None, new_header_gaggle_format])
def test_create_cards_from_tsv_well_formed_arguments(
    case_anki_export_file_no_header_well_formed_content, field_names, header):
  # TODO: This is a minimal test suite for create_cards_from_tsv
  #   See: https://github.com/ImplyingICheck/Gaggle/issues/32
  test_file_path = case_anki_export_file_no_header_well_formed_content
  with open(test_file_path, **READ_PARAMS) as f:
    deck = gaggle.create_cards_from_tsv(
        f, field_names=field_names, header=header)
  assert deck
