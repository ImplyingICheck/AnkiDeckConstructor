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
import pytest_cases

from gaggle import gaggle

_GENERIC_NUMBER_OF_FIELDS = 10
_GENERIC_FIELD_VALUE = 'value'
_GENERIC_FIELD_NAME = 'Field'
ANKI_CARD_RESERVED_NAMES = ('GUID', 'Note Type', 'Deck', 'Tags')


class MinimumWellFormedAnkiCard:
  number_of_fields = _GENERIC_NUMBER_OF_FIELDS
  field_value_prefix = _GENERIC_FIELD_VALUE
  fields = []
  field_names = None
  has_html = 'false'
  tags_idx = None
  note_type_idx = None
  deck_idx = None
  guid_idx = None

  def __init__(self):
    if not self.fields:
      self.fields = self._new_field_values()

  def new_anki_card(self):
    return gaggle.AnkiCard(
        fields=self.fields,
        field_names=self.field_names,
        has_html=self.has_html,
        tags_idx=self.tags_idx,
        note_type_idx=self.note_type_idx,
        deck_idx=self.deck_idx,
        guid_idx=self.guid_idx,
    )

  def _new_field_values(self):
    return [
        f'{self.field_value_prefix}{field_idx}'
        for field_idx in range(self.number_of_fields)
    ]


class FullySpecifiedWellFormedAnkiCard(MinimumWellFormedAnkiCard):
  note_type_idx = 1
  deck_idx = 2
  guid_idx = 0
  field_name_prefix = _GENERIC_FIELD_NAME

  def __init__(self):
    self.tags_idx = self.number_of_fields - 1
    assert self.tags_idx not in {
        self.note_type_idx, self.deck_idx, self.guid_idx
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


class ModifiedFullySpecifiedAnkiCard(FullySpecifiedWellFormedAnkiCard):

  def __init__(self, *, field_names=None):
    if field_names:
      self.field_names = field_names
    super().__init__()


@pytest_cases.case(tags=['FullySpecifiedAnkiCard', 'WellFormedAnkiCard'])
def case_fully_specified_well_formed_anki_card():
  return FullySpecifiedWellFormedAnkiCard()


@pytest_cases.case(tags=['MinimumAnkiCard', 'WellFormedAnkiCard'])
def case_minimum_well_formed_anki_card():
  return MinimumWellFormedAnkiCard()


@pytest_cases.case(tags=['ModifiedFullySpecifiedAnkiCard', 'Constructor'])
def case_modified_fully_specified_anki_card():
  return ModifiedFullySpecifiedAnkiCard


@pytest_cases.fixture
def fully_specified_well_formed_values():
  return FullySpecifiedWellFormedAnkiCard()


@pytest_cases.case(tags=['Malformed', 'FieldNames', 'Surplus'])
def field_names_surplus_by_one(fully_specified_well_formed_values):
  field_names = fully_specified_well_formed_values.field_names
  extra_field_names = ['This extends field_names by one.']
  field_names.extend(extra_field_names)
  return field_names


@pytest_cases.case(tags=['Malformed', 'FieldNames', 'Surplus', 'Multiple'])
def field_names_surplus_by_two(fully_specified_well_formed_values):
  field_names = fully_specified_well_formed_values.field_names
  extra_field_names = [
      'This extends field_names by one.', 'This extends field_names by two.'
  ]
  field_names.extend(extra_field_names)
  return field_names


@pytest_cases.case(tags=['Well-Formed', 'FieldNames'])
def field_names_empty_list():
  field_names = []
  return field_names


@pytest_cases.case(tags=['Well-Formed', 'FieldNames'])
def field_names_none():
  field_names = None
  return field_names


@pytest_cases.case(tags=['Well-Formed', 'FieldNames'])
def field_names_generic_well_formed(fully_specified_well_formed_values):
  field_names = fully_specified_well_formed_values.field_names
  return field_names


@pytest_cases.case(tags=['Malformed', 'FieldNames', 'HeaderNameMismatch'])
def field_names_header_name_mismatch(fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  guid_idx = card_values.guid_idx
  field_names = card_values.field_names
  field_names[guid_idx] = 'This is not a field name assigned by the header'
  return field_names


@pytest_cases.case(
    tags=['Malformed', 'FieldNames', 'HeaderNameMismatch', 'Multiple'])
def field_names_multiple_header_name_mismatch(
    fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  guid_idx = card_values.guid_idx
  note_type_idx = card_values.note_type_idx
  field_names = card_values.field_names
  field_names[guid_idx] = 'This is not a field name assigned by the header'
  field_names[note_type_idx] = 'Also not a field name assigned by the header'
  return field_names


@pytest_cases.case(tags=[
    'Malformed', 'FieldNames', 'GenericFieldNameOverwritten',
    'DuplicateReservedFieldNames'
])
def field_names_duplicate_reserved_name_overwrites_generic(
    fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  guid_idx = card_values.guid_idx
  first_generic_field_name = card_values.deck_idx + 1
  field_names = card_values.field_names
  field_names[first_generic_field_name] = field_names[guid_idx]
  return field_names


@pytest_cases.case(tags=[
    'Malformed', 'FieldNames', 'GenericFieldNameOverwritten',
    'DuplicateReservedFieldNames', 'Multiple'
])
def field_names_multiple_duplicate_reserved_name_overwrites_generic(
    fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  guid_idx = card_values.guid_idx
  first_generic_field_name = card_values.deck_idx + 1
  field_names = card_values.field_names
  field_names[first_generic_field_name] = field_names[guid_idx]
  field_names[first_generic_field_name + 1] = field_names[guid_idx]
  return field_names


@pytest_cases.case(tags=[
    'Malformed', 'FieldNames', 'GenericFieldNameOverwritten',
    'UsageAfterAssignment'
])
def field_names_usage_after_assignment_generic(
    fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  first_generic_field_name = card_values.deck_idx + 1
  field_names = card_values.field_names
  field_names[first_generic_field_name +
              1] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name}'
  return field_names


@pytest_cases.case(tags=[
    'Malformed', 'FieldNames', 'GenericFieldNameOverwritten',
    'UsageAfterAssignment', 'Multiple'
])
def field_names_usage_after_assignment_generic_multiple(
    fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  first_generic_field_name = card_values.deck_idx + 1
  field_names = card_values.field_names
  field_names[first_generic_field_name +
              1] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name}'
  field_names[first_generic_field_name +
              2] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name}'
  return field_names


@pytest_cases.case(tags=[
    'Malformed', 'FieldNames', 'GenericFieldNameOverwritten',
    'UsageBeforeAssignment'
])
def field_names_usage_before_assignment_generic(
    fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  first_generic_field_name = card_values.deck_idx + 1
  field_names = card_values.field_names
  field_names[first_generic_field_name] = (
      f'{_GENERIC_FIELD_NAME}{first_generic_field_name +  1}')
  return field_names


@pytest_cases.case(tags=[
    'Malformed', 'FieldNames', 'GenericFieldNameOverwritten',
    'UsageBeforeAssignment', 'Multiple'
])
def field_names_usage_before_assignment_generic_multiple(
    fully_specified_well_formed_values):
  card_values = fully_specified_well_formed_values
  first_generic_field_name = card_values.deck_idx + 1
  field_names = card_values.field_names
  field_names[first_generic_field_name] = (
      f'{_GENERIC_FIELD_NAME}{first_generic_field_name + 2}')
  field_names[first_generic_field_name +
              1] = f'{_GENERIC_FIELD_NAME}{first_generic_field_name + 2}'
  return field_names
