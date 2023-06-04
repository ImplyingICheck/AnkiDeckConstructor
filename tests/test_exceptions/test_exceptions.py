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
import pytest
from gaggle import exceptions


@pytest.fixture
def deck_index():
  return 42


class TestDecksNotWrittenException:
  @pytest.fixture(autouse=True)
  def decks_not_written_exception(self, deck_index):
    self.test_exception = exceptions.DecksNotWrittenException(deck_index)

  @pytest.fixture
  def decks_not_written_exception_string_representation(self, deck_index):
    return (f'Failed to write all Decks to the file. '
              f'Last deck successfully written was the deck at: '
              f'Index {deck_index}')

  def test_decks_not_written_exception_init_with_int(self):
    assert self.test_exception

  def test_decks_not_written_exception_last_deck_written_property(
      self,
      deck_index
  ):
    assert self.test_exception.last_deck_written == deck_index

  def test_decks_not_written_exception_str(
      self,
      decks_not_written_exception_string_representation
  ):
    assert (str(self.test_exception) ==
            decks_not_written_exception_string_representation)
