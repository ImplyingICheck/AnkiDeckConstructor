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
import pytest_cases.filters
from tests.test_gaggle.conftest import falsy_values

from gaggle import gaggle

_GENERIC_NUMBER_OF_FIELDS = 10
_GENERIC_FIELD_VALUE = 'value'
_GENERIC_FIELD_NAME = 'Field'
ANKI_CARD_RESERVED_NAMES = (
    'GUID',
    'Note Type',
    'Deck',
    'Tags',
)


@pytest_cases.fixture
def fully_specified_well_formed_values():
  return FullySpecifiedWellFormedAnkiCardComponents()


class AnkiCardTestingComponents:
  expected_fields = None
  expected_field_names = None
  fields = None
  field_names = None
  has_html = None
  tags_idx = None
  note_type_idx = None
  deck_idx = None
  guid_idx = None

  def __init__(self):
    if not self.fields:
      self.fields = self._new_field_values()
    if not self.expected_field_names:
      self.expected_field_names = self._new_expected_field_names()
    if not self.expected_fields:
      self.expected_fields = self._new_expected_fields()

  def new_anki_card(self):
    assert self.fields
    assert self.has_html
    card = gaggle.AnkiCard(
        fields=self.fields,
        field_names=self.field_names,
        has_html=self.has_html,
        tags_idx=self.tags_idx,
        note_type_idx=self.note_type_idx,
        deck_idx=self.deck_idx,
        guid_idx=self.guid_idx,
    )
    assert self.expected_field_names == list(card.fields.keys())
    return card

  def _new_field_values(self):
    raise NotImplementedError

  def _new_expected_field_names(self):
    raise NotImplementedError

  def _new_expected_fields(self):
    raise NotImplementedError


class MinimumWellFormedAnkiCardComponents(AnkiCardTestingComponents):
  number_of_fields = _GENERIC_NUMBER_OF_FIELDS
  field_value_prefix = _GENERIC_FIELD_VALUE
  field_names = []
  has_html = 'false'
  tags_idx = None
  note_type_idx = None
  deck_idx = None
  guid_idx = None
  reserved_names = {}

  def _new_field_values(self):
    """Of the form ['value0', 'value1', 'value2', ...]"""
    return [
        f'{self.field_value_prefix}{field_idx}'
        for field_idx in range(self.number_of_fields)
    ]

  def _new_expected_fields(self):
    return self._new_field_values()

  def _new_expected_field_names(self):
    return [
        f'{_GENERIC_FIELD_NAME}{idx}' for idx in range(self.number_of_fields)
    ]


class FullySpecifiedWellFormedAnkiCardComponents(
    MinimumWellFormedAnkiCardComponents):
  note_type_idx = 1
  deck_idx = 2
  guid_idx = 0
  field_name_prefix = _GENERIC_FIELD_NAME

  def __init__(self):
    self.tags_idx = self.number_of_fields - 1
    assert self.tags_idx not in {
        self.note_type_idx,
        self.deck_idx,
        self.guid_idx,
    }, 'Values defined by AnkiHeader overlap.'
    self.reserved_names = dict(
        zip([self.guid_idx, self.note_type_idx, self.deck_idx, self.tags_idx],
            ANKI_CARD_RESERVED_NAMES))
    if not self.field_names:
      self.field_names = self._new_field_names_generic_with_reserved_names()
    super().__init__()

  def _new_field_names_generic_with_reserved_names(self):
    field_names = [
        f'{self.field_name_prefix}{field_idx}'
        for field_idx in range(self.number_of_fields)
    ]
    for index, reserved_name in self.reserved_names.items():
      field_names[index] = reserved_name
    return field_names

  def _new_expected_field_names(self):
    return self._new_field_names_generic_with_reserved_names()


class ModifiedFullySpecifiedAnkiCardComponents(
    FullySpecifiedWellFormedAnkiCardComponents):

  def __init__(self, *, field_names=None):
    if field_names:
      self.field_names = field_names
    super().__init__()


@pytest_cases.case(tags=[
    'AnkiCardComponentsConstructor',
    'ModifiedFullySpecified',
    'Constructor',
])
def case_modified_fully_specified_anki_card_components():
  return ModifiedFullySpecifiedAnkiCardComponents


class FieldNamesCase:

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'Surplus',
  ])
  def field_names_surplus_by_one(
      self,
      fully_specified_well_formed_values,
  ):
    field_names = fully_specified_well_formed_values.field_names
    extra_field_names = ['This extends field_names by one.']
    field_names.extend(extra_field_names)
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'Surplus',
      'Multiple',
  ])
  def field_names_surplus_by_two(
      self,
      fully_specified_well_formed_values,
  ):
    field_names = fully_specified_well_formed_values.field_names
    extra_field_names = [
        'This extends field_names by one.',
        'This extends field_names by two.',
    ]
    field_names.extend(extra_field_names)
    return field_names

  @pytest_cases.case(tags=[
      'Well-Formed',
      'FieldNames',
  ])
  def field_names_empty_list(self,):
    field_names = []
    return field_names

  @pytest_cases.case(tags=[
      'Well-Formed',
      'FieldNames',
  ])
  def field_names_none(self,):
    field_names = None
    return field_names

  @pytest_cases.case(tags=[
      'Well-Formed',
      'FieldNames',
  ])
  def field_names_generic_well_formed(
      self,
      fully_specified_well_formed_values,
  ):
    field_names = fully_specified_well_formed_values.field_names
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'HeaderNameMismatch',
  ])
  def field_names_header_name_mismatch(
      self,
      fully_specified_well_formed_values,
  ):
    card_values = fully_specified_well_formed_values
    guid_idx = card_values.guid_idx
    field_names = card_values.field_names
    field_names[guid_idx] = 'This is not a field name assigned by the header'
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'HeaderNameMismatch',
      'Multiple',
  ])
  def field_names_multiple_header_name_mismatch(
      self,
      fully_specified_well_formed_values,
  ):
    card_values = fully_specified_well_formed_values
    guid_idx = card_values.guid_idx
    note_type_idx = card_values.note_type_idx
    field_names = card_values.field_names
    field_names[guid_idx] = 'This is not a field name assigned by the header'
    field_names[note_type_idx] = 'Also not a field name assigned by the header'
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'GenericFieldNameOverwritten',
      'DuplicateReservedFieldNames',
  ])
  def field_names_duplicate_reserved_name_overwrites_generic(
      self,
      fully_specified_well_formed_values,
  ):
    card_values = fully_specified_well_formed_values
    guid_idx = card_values.guid_idx
    first_generic_field_name = card_values.deck_idx + 1
    field_names = card_values.field_names
    field_names[first_generic_field_name] = field_names[guid_idx]
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'GenericFieldNameOverwritten',
      'DuplicateReservedFieldNames',
      'Multiple',
  ])
  def field_names_multiple_duplicate_reserved_name_overwrites_generic(
      self, fully_specified_well_formed_values):
    card_values = fully_specified_well_formed_values
    guid_idx = card_values.guid_idx
    first_generic_field_name = card_values.deck_idx + 1
    field_names = card_values.field_names
    field_names[first_generic_field_name] = field_names[guid_idx]
    field_names[first_generic_field_name + 1] = field_names[guid_idx]
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'GenericFieldNameOverwritten',
      'UsageAfterAssignment',
  ])
  def field_names_usage_after_assignment_generic(
      self,
      fully_specified_well_formed_values,
  ):
    card_values = fully_specified_well_formed_values
    first_generic_field_name = card_values.deck_idx + 1
    field_names = card_values.field_names
    field_names[first_generic_field_name +
                1] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name}'
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'GenericFieldNameOverwritten',
      'UsageAfterAssignment',
      'Multiple',
  ])
  def field_names_usage_after_assignment_generic_multiple(
      self,
      fully_specified_well_formed_values,
  ):
    card_values = fully_specified_well_formed_values
    first_generic_field_name = card_values.deck_idx + 1
    field_names = card_values.field_names
    field_names[first_generic_field_name +
                1] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name}'
    field_names[first_generic_field_name +
                2] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name}'
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'GenericFieldNameOverwritten',
      'UsageBeforeAssignment',
  ])
  def field_names_usage_before_assignment_generic(
      self,
      fully_specified_well_formed_values,
  ):
    card_values = fully_specified_well_formed_values
    first_generic_field_name = card_values.deck_idx + 1
    field_names = card_values.field_names
    field_names[first_generic_field_name] = (
        f'{_GENERIC_FIELD_NAME}{first_generic_field_name +  1}')
    return field_names

  @pytest_cases.case(tags=[
      'Malformed',
      'FieldNames',
      'GenericFieldNameOverwritten',
      'UsageBeforeAssignment',
      'Multiple',
  ])
  def field_names_usage_before_assignment_generic_multiple(
      self, fully_specified_well_formed_values):
    card_values = fully_specified_well_formed_values
    first_generic_field_name = card_values.deck_idx + 1
    field_names = card_values.field_names
    field_names[first_generic_field_name] = (
        f'{_GENERIC_FIELD_NAME}{first_generic_field_name + 2}')
    field_names[first_generic_field_name +
                1] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name + 2}'
    return field_names


class FieldValuesCase:

  @pytest_cases.case(tags=['Fields', 'Well-Formed'])
  def fields_fully_specified_well_formed(
      self,
      fully_specified_well_formed_values,
  ):
    return fully_specified_well_formed_values.fields


class HasHtmlCase:

  @pytest_cases.case(tags=['HasHtml', 'Well-Formed'])
  @pytest_cases.parametrize('well_formed_value', ['true', 'false'])
  def has_html_well_formed(self, well_formed_value):
    return well_formed_value

  @pytest_cases.case(tags=['HasHtml', 'Malformed'])
  @pytest_cases.parametrize(
      'malformed_value',
      [falsy_values, 'This is not a valid value for has_html'])
  def has_html_malformed(self, malformed_value):
    return malformed_value


class TagsIdxCase:

  @pytest_cases.case(tags=['TagsIdx', 'Well-Formed'])
  def tags_idx_fully_specified_well_formed(
      self,
      fully_specified_well_formed_values,
  ):
    return fully_specified_well_formed_values.tags_idx

  @pytest_cases.case(tags=['TagsIdx', 'Well-Formed'])
  def tags_idx_none(self):
    return None


class NoteTypeIdxCase:

  @pytest_cases.case(tags=['NoteTypeIdx', 'Well-Formed'])
  def note_type_idx_fully_specified_well_formed(
      self,
      fully_specified_well_formed_values,
  ):
    return fully_specified_well_formed_values.note_type_idx

  @pytest_cases.case(tags=['NoteTypeIdx', 'Well-Formed'])
  def note_type_idx_none(self):
    return None


class GuidIdxCase:

  @pytest_cases.case(tags=['GuidIdx', 'Well-Formed'])
  def guid_idx_fully_specified_well_formed(
      self,
      fully_specified_well_formed_values,
  ):
    return fully_specified_well_formed_values.guid_idx

  @pytest_cases.case(tags=['GuidIdx', 'Well-Formed'])
  def guid_idx_none(self):
    return None


class DeckIdxCase:

  @pytest_cases.case(tags=['DeckIdx', 'Well-Formed'])
  def deck_idx_fully_specified_well_formed(
      self,
      fully_specified_well_formed_values,
  ):
    return fully_specified_well_formed_values.deck_idx

  @pytest_cases.case(tags=['DeckIdx', 'Well-Formed'])
  def deck_idx_none(self):
    return None


class AnkiCardComponentsCase:

  @pytest_cases.case(tags=[
      'AnkiCardComponents',
      'ModifiedFullySpecified',
      'WellFormed',
  ])
  @pytest_cases.parametrize_with_cases(
      'field_names',
      cases='.',
      filter=~pytest_cases.filters.has_tag('UsageBeforeAssignment'),
      prefix='field_names',
      idstyle='explicit')
  def case_well_formed_modified_fully_specified_anki_card_components(
      self, field_names):
    """Must be defined after all cases to be used when using cases='.'"""
    return ModifiedFullySpecifiedAnkiCardComponents(field_names=field_names)

  @pytest_cases.case(tags=[
      'AnkiCardComponents',
      'FullySpecified',
      'WellFormed',
  ])
  def case_fully_specified_well_formed_anki_card_components(self):
    return FullySpecifiedWellFormedAnkiCardComponents()

  @pytest_cases.case(tags=[
      'AnkiCardComponents',
      'Minimum',
      'WellFormed',
  ])
  def case_minimum_well_formed_anki_card_components(self):
    return MinimumWellFormedAnkiCardComponents()


class AnkiCardCase:

  @pytest_cases.case(tags=[
      'AnkiCard',
      'ModifiedFullySpecified',
      'WellFormed',
  ])
  @pytest_cases.parametrize_with_cases(
      'field_names',
      cases='.',
      filter=~pytest_cases.filters.has_tag('UsageBeforeAssignment'),
      prefix='field_names',
      idstyle='explicit')
  def case_well_formed_modified_fully_specified_anki_card(self, field_names):
    """Must be defined after all cases to be used when using cases='.'"""
    return ModifiedFullySpecifiedAnkiCardComponents(
        field_names=field_names).new_anki_card()

  @pytest_cases.case(tags=[
      'AnkiCard',
      'FullySpecified',
      'WellFormed',
  ])
  def case_fully_specified_well_formed_anki_card(self):
    return FullySpecifiedWellFormedAnkiCardComponents().new_anki_card()

  @pytest_cases.case(tags=[
      'AnkiCard',
      'Minimum',
      'WellFormed',
  ])
  def case_minimum_well_formed_anki_card(self):
    return MinimumWellFormedAnkiCardComponents().new_anki_card()
