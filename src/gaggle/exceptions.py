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
"""Definition of Gaggle exceptions. For internal use."""
from typing import Any


class DecksNotWrittenException(Exception):
  """Gaggle exception for failure to write all stored Decks to file. Can return
  the last successfully written deck"""
  def __init__(self, last_deck_written: int | None = None):
    """
    Args:
      last_deck_written: An int representing the index of the last deck
      successfully written to file. None if no success writes occurred.
    """
    self.last_deck_written = last_deck_written

  def __str__(self):
    return (f'Failed to write all Decks to the file. '
            f'Last deck successfully written was the deck at: '
            f'Index {self.last_deck_written}')

class DuplicateWarning(Warning):
  """Gaggle warning when attempting to use a duplicate value when a unique value
  is expected. However, a replacement value can be generated at run time.
  Warning informs of the value used as a replacement."""
  def __init__(self, context_message: Any, duplicate_value: Any,
               replacement_value: Any):
    """
    Args:
      context_message: Used to provide context to duplicate values. See
      documentation for DuplicateWarning._create_message() for further detail
      duplicate_value: The value which should have been unique
      replacement_value: The value which will be used as a replacement for the
        duplicate
    """
    self.duplicate_value = duplicate_value
    self.replacement_value = replacement_value
    self.message = self._create_message(context_message)

  def _create_message(self, context_message: Any) -> str:
    """Creates value of DuplicateWarning.message

    Args:
      context_message: Extra information giving context, such as a name, to the
      value which was duplicated. Used as f'Duplicate {context_message} ...'

    Returns:
      An f string explaining the type of duplication and the associated values
    """
    return (f'Duplicate {context_message} (replaced with: '
            f'{self.replacement_value}): {self.duplicate_value}')

  def __str__(self):
    return self.message
