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
from collections.abc import Mapping
from typing import Any

import pytest_cases

from gaggle import gaggle

_GENERIC_NUMBER_OF_FIELDS = 10
_GENERIC_FIELD_VALUE = 'value'
_GENERIC_FIELD_NAME = 'Field'
ANKI_CARD_RESERVED_NAMES = ['GUID', 'Note Type', 'Deck', 'Tags']


def _new_field_values(field_value_prefix, number_of_fields):
  return [
      f'{field_value_prefix}{field_idx}'
      for field_idx in range(number_of_fields)
  ]


class MinimumWellFormedAnkiCard:
  number_of_fields = _GENERIC_NUMBER_OF_FIELDS
  field_value_prefix = _GENERIC_FIELD_VALUE
  fields = None
  field_names = None
  has_html = 'false'
  tags_idx = None
  note_type_idx = None
  deck_idx = None
  guid_idx = None

  def __init__(self):
    if not self.fields:
      self.fields = _new_field_values(self.field_value_prefix,
                                      self.number_of_fields)
    self.card = gaggle.AnkiCard(
        fields=self.fields,
        field_names=self.field_names,
        has_html=self.has_html,
        tags_idx=self.tags_idx,
        note_type_idx=self.note_type_idx,
        deck_idx=self.deck_idx,
        guid_idx=self.guid_idx,
    )


def _new_field_names_generic_with_reserved_names(field_name_prefix: Any,
                                                 number_of_fields: int,
                                                 reserved_names: Mapping[int,
                                                                         str]):
  field_names = [
      f'{field_name_prefix}{field_idx}' for field_idx in range(number_of_fields)
  ]
  for index, reserved_name in reserved_names.items():
    field_names[index] = reserved_name
  return field_names


class FullySpecifiedWellFormedAnkiCard(MinimumWellFormedAnkiCard):
  tags_idx = MinimumWellFormedAnkiCard.number_of_fields - 1
  note_type_idx = 1
  deck_idx = 2
  guid_idx = 0
  field_name_prefix = _GENERIC_FIELD_NAME
  reserved_names = dict(
      zip([guid_idx, note_type_idx, deck_idx, tags_idx],
          ANKI_CARD_RESERVED_NAMES))
  field_names = _new_field_names_generic_with_reserved_names(
      field_name_prefix, MinimumWellFormedAnkiCard.number_of_fields,
      reserved_names)


@pytest_cases.case(tags=['FullySpecifiedAnkiCard', 'WellFormedAnkiCard'])
def case_fully_specified_well_formed_anki_card():
  return FullySpecifiedWellFormedAnkiCard()


@pytest_cases.case(tags=['MinimumAnkiCard', 'WellFormedAnkiCard'])
def case_minimum_well_formed_anki_card():
  return MinimumWellFormedAnkiCard()
