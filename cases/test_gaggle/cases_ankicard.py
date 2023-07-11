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
import pytest_cases

from gaggle import gaggle

_GENERIC_NUMBER_OF_FIELDS = 10
_GENERIC_FIELD_VALUE = 'value'
_GENERIC_FIELD_NAME = 'Field'
ANKI_CARD_RESERVED_NAMES = ['GUID', 'Note Type', 'Deck', 'Tags']


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


@pytest_cases.case(tags=['FullySpecifiedAnkiCard', 'WellFormedAnkiCard'])
def case_fully_specified_well_formed_anki_card():
  return FullySpecifiedWellFormedAnkiCard()


@pytest_cases.case(tags=['MinimumAnkiCard', 'WellFormedAnkiCard'])
def case_minimum_well_formed_anki_card():
  return MinimumWellFormedAnkiCard()


class ModifiedFullySpecifiedAnkiCard(FullySpecifiedWellFormedAnkiCard):

  def __init__(self, *, field_names=None):
    if field_names:
      self.field_names = field_names
    super().__init__()
