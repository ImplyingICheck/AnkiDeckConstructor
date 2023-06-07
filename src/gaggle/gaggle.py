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
"""Base class for collection, a class representing multiple Anki Decks."""
from __future__ import annotations

import collections
import copy
import csv
import functools
import os.path
import itertools
import operator
import enum
import warnings
from _csv import Dialect
from typing import cast, overload, Any, Protocol, Self, TypeVar, TYPE_CHECKING
from collections.abc import Callable, Iterable, Iterator, Mapping, Sized

from gaggle import exceptions

if TYPE_CHECKING:
  from _typeshed import SupportsWrite, StrOrBytesPath, SupportsReadline, SupportsRead

  _T = TypeVar('_T')
  _T_co = TypeVar('_T_co', covariant=True)
  _T_contra = TypeVar('_T_contra', contravariant=True)
  _S = TypeVar('_S')

  class SupportsIndex(Protocol):
    def __index__(self) -> int:
      ...

  class SupportsInt(Protocol):
    def __int__(self) -> int:
      ...

  class SupportsTrunc(Protocol):
    def __trunc__(self) -> int:
      ...

  class Falsy(Protocol):
    def __bool__(self) -> bool:
      return False

  class SupportsAppend(Protocol[_T_contra]):
    def append(self, obj: _T_contra) -> Any:
      ...

  class Seekable(Protocol):
    def tell(self) -> Any:
      ...
    def seek(self, position: Any) -> Any:
      ...

  class SupportsWriteRow(Protocol):
    @property
    def dialect(self) -> Dialect:
      ...

    def writerow(self, row: Iterable[_T_co]) -> Any:
      ...

  class SizedAppendable(Sized, SupportsAppend[_T_contra],
                        Protocol[_T_contra]):
    ...

  class SizedAppendableIterable(SizedAppendable[_T],
                                Iterable[_T], Protocol[_T]):
    ...

  class ReadableAndSeekable(SupportsRead[_T_co],
                            SupportsReadline[_T_co], Seekable,
                            Protocol[_T_co]):
    ...

  RealNumber = SupportsInt | SupportsTrunc
  # dict() is invariant so value type [str | int] and [str] must be declared
  AnkiHeader = dict[str, str | int] | dict[str, str]

_ANKI_EXPORT_HEADER_LINE_SYMBOL = '#'
_ANKI_EXPORT_HEADER_DELIMITER_SYMBOL = ':'
_ANKI_EXPORT_ENCODING = 'utf-8'
_ANKI_EXPORT_HEADER_SETTING_SEPARATOR_NAME = 'separator'
_ANKI_EXPORT_HEADER_SETTING_SEPARATOR_TSV_STRING = 'tab'
class HeaderBoolean(enum.StrEnum):
  FALSE_ = 'false'
  TRUE_ = 'true'
_ANKI_EXPORT_HEADER_TRUE = 'true'
_ANKI_EXPORT_HEADER_FALSE = 'false'
_ANKI_EXPORT_HEADER_MAPPING = {
  'html':'has_html',
  'tags column':'tags_idx',
  'notetype column':'note_type_idx',
  'deck column':'deck_idx',
  'guid column':'guid_idx',
  _ANKI_EXPORT_HEADER_SETTING_SEPARATOR_NAME:'separator',
}
_ANKI_EXPORT_HEADER_MAPPING_REVERSE = {
  v: k for k, v in _ANKI_EXPORT_HEADER_MAPPING.items()
}
_ANKI_ORDERED_HEADER = [
  'separator', 'html', 'guid column', 'notetype column', 'deck column',
  'tags column'
]
_ANKI_NOTESINPLAINTEXT_EXT = '.txt'
_ANKI_CARDSINPLAINTEXT_EXT = '.txt'

GENERIC_EXPORT_FILE_NAME = 'GaggleFile'
class ReformatDirection(enum.StrEnum):
  ANKI_TO_GAGGLE = 'anki_to_gaggle'
  GAGGLE_TO_ANKI = 'gaggle_to_anki'
_DIRECTION_TRANSLATION_VALUE = {ReformatDirection.ANKI_TO_GAGGLE: -1,
                                ReformatDirection.GAGGLE_TO_ANKI: 1}
_DIRECTION_MAPPING = {ReformatDirection.ANKI_TO_GAGGLE:
                        _ANKI_EXPORT_HEADER_MAPPING,
                      ReformatDirection.GAGGLE_TO_ANKI:
                        _ANKI_EXPORT_HEADER_MAPPING_REVERSE}

def propagate_warnings(stack_level):
  def decorator(function):
    @functools.wraps(function)
    def capture_and_raise_warnings(*args, **kwargs):
      with warnings.catch_warnings(record=True) as warning_context_manager:
        return_value = function(*args, **kwargs)
      for warning in warning_context_manager:
        warnings.warn(warning.message, warning.category, stacklevel=stack_level)
      return return_value
    return capture_and_raise_warnings
  return decorator

def propagate_warnings_yield(stack_level):
  def decorator(function):
    @functools.wraps(function)
    def capture_and_raise_warnings(*args, **kwargs):
      with warnings.catch_warnings(record=True) as warning_context_manager:
        yield from function(*args, **kwargs)
      for warning in warning_context_manager:
        warnings.warn(warning.message, warning.category, stacklevel=stack_level)
    return capture_and_raise_warnings
  return decorator


def _initialise_decks(exported_file, field_names):
  """

  Args:
    exported_file:
    field_names:

  Returns:

  Raises:
    FileNotFoundError: If file specified by exported_file does not exist
  """
  if exported_file:
    return [AnkiDeck.from_file(exported_file, field_names)]
  else:
    return []


def _generate_unique_file_path(filename, extension, destination):
  if not filename:
    filename = GENERIC_EXPORT_FILE_NAME
  file_exists = True
  tag = 0
  if filename == GENERIC_EXPORT_FILE_NAME:
    modified_filename = f'{filename}{tag}'
    tag += 1
  else:
    modified_filename = filename
  while file_exists:
    complete_filename = f'{modified_filename}{extension}'
    file_path = os.path.join(destination, complete_filename)
    file_exists = os.path.isfile(file_path)
    if file_exists:
      modified_filename = f'{filename}{tag}'
      tag += 1
  return modified_filename


def generate_flattened_kwargs_fill_missing(fillvalue: Any = None,
                                           **kwargs: Iterator[Any],
                                           ) -> Iterator[dict[str, Any]]:
  """Generator which yields a dictionary of keywords to arguments. The values
  have lazy evaluation and missing arguments are filled with fillvalue.

  For usage with arguments which evaluate to False, see documentation for
  generate_flattened_kwargs_remove_sentinel(). To remove all falsy arguments,
  see documentation for generate_flattened_kwargs_remove_falsy().

  Args:
    fillvalue: Any value with which missing arguments are filled
    **kwargs: An iterable containing arguments

  Yields:
    Dictionary mapping keyword to arguments. Each dictionary contains the
    arguments that would be found at the same "index" i as if **kwargs
    contained lists. For example, having i as 5:

    {'param_x_keyword': argument_x5,
     'param_y_keyword': argument_y5,
     'param_z_keyword': argument_z5}

    Returned keys always strings. This function will fill missing arguments
    with the specified fillvalue. Taking our previous example, let us say
    "argument_y5" was not passed in but "param_y_keyword" is a key in the
    **kwargs passed in. We have the "fillvalue" object(). For example:

    {'param_x_keyword': argument_x5,
     'param_y_keyword': object(),
     'param_z_keyword': argument_z5}
    """
  cast_zip = cast(Callable, zip)
  keyword_argument_mappings = map(cast_zip,
                                  itertools.repeat(kwargs),
                                  itertools.zip_longest(*kwargs.values(),
                                                        fillvalue=fillvalue))
  for flat_kwargs in keyword_argument_mappings:
    yield dict(flat_kwargs)


def generate_flattened_kwargs_remove_falsy(**kwargs: Iterable[Any],
                                           ) -> Iterator[dict[str, Any]]:
  """Generator which yields a dictionary of keywords to arguments. The values
  have lazy evaluation and falsy values are not returned.

  To remove all falsy arguments, see documentation for
  generate_flattened_kwargs_remove_falsy(). To fill missing arguments, see
  documentation for generate_flattened_kwargs_fill_missing().

  Args:
    **kwargs: An iterable containing arguments

  Yields:
    Dictionary mapping keyword to arguments. Each dictionary contains the
    arguments that would be found at the same "index" i as if **kwargs contained
    lists. For example, having i as 5:

    {'param_x_keyword': argument_x5,
     'param_y_keyword': argument_y5,
     'param_z_keyword': argument_z5}

    Returned keys always strings. This function will remove any argument which
    evaluates to False. Taking our previous example, let us say
    argument_y5 == None and argument_x5 == ''. For example:

    {'param_z_keyword': argument_z5}
  """
  arguments = itertools.zip_longest(*kwargs.values())
  arguments, falsy_filter = itertools.tee(arguments)
  cast_zip = cast(Callable, zip)
  keyword_argument_pairs = map(cast_zip,
                               itertools.repeat(kwargs),
                               arguments)
  cast_compress = cast(Callable, itertools.compress)
  filtered_pairs = map(cast_compress,
                       keyword_argument_pairs,
                       falsy_filter)
  for flat_kwargs in filtered_pairs:
    yield dict(flat_kwargs)


def generate_flattened_kwargs_remove_sentinel(sentinel: Any = None,
                                              fillvalue: Any = None,
                                              **kwargs: Iterable[Any],
                                              ) -> Iterator[dict[str, Any]]:
  """Generator which yields a dictionary of keywords to arguments. The values
  have lazy evaluation and only arguments which match sentinel are removed.
  Missing arguments are filled with fillvalue.

  To remove missing arguments for which the parameter has been specified,
  ensure sentinel and fillvalue are equal.

  To remove all falsy arguments, see documentation for
  generate_flattened_kwargs_remove_falsy(). To only fill missing arguments, see
  documentation for generate_flattened_kwargs_fill_missing().

  Args:
    sentinel: Any value for which matching arguments should be removed
    fillvalue: Any value with which missing arguments are filled
    **kwargs: An iterable containing arguments

  Yields:
    Dictionary mapping keyword to arguments. Each dictionary contains the
    arguments that would be found at the same "index" i as if **kwargs
    contained lists. For example, having i as 5:

    {'param_x_keyword': argument_x5,
     'param_y_keyword': argument_y5,
     'param_z_keyword': argument_z5}

    Returned keys always strings. Unlike the generate_flattened_kwargs()
    function, this function will remove any argument which matches sentinel.
    Taking our previous example, let us say argument_x5 == None and
    "argument_y5" was not passed in but 'param_y_keyword' is a key in the
    **kwargs passed in. Let sentinel == None and fillvalue == ''. For example,

    {'param_y_keyword': '',
     'param_z_keyword': argument_z5}
      """
  arguments = itertools.zip_longest(*kwargs.values(), fillvalue=fillvalue)
  arguments, sentinel_filter = itertools.tee(arguments)
  cast_zip = cast(Callable, zip)
  keyword_argument_pairs = map(cast_zip,
                               itertools.repeat(kwargs),
                               arguments)
  sentinel_filter = map(operator.ne,
                        itertools.chain.from_iterable(sentinel_filter),
                        itertools.repeat(sentinel))
  cast_compress = cast(Callable, itertools.compress)
  filtered_keyword_argument_pairs = map(cast_compress,
                                        keyword_argument_pairs,
                                        itertools.repeat(sentinel_filter))
  for flat_kwargs in filtered_keyword_argument_pairs:
    yield dict(flat_kwargs)


class Gaggle:
  """
  Parser class for Anki exported files.
  Handles deck construction and organisation.
  """
  def __init__(self, exported_file=None, field_names=None):
    """

    Args:
      exported_file:
      field_names:

    Raises:
      FileNotFoundError: If file specified by exported_file does not exist
    """
    self.decks = _initialise_decks(exported_file, field_names)

  def __iter__(self):
    return iter(self._get_decks())

  def add_deck(self, deck):
    self.decks.append(deck)

  def add_deck_from_file(self, file: str) -> None:
    """

    Args:
      file:

    Returns:

    """
    deck = AnkiDeck.from_file(file)
    self.add_deck(deck)

  @overload
  def write_deck_to_file(self, deck: AnkiDeck,
                         filename: str | None = None,
                         file_type: str = _ANKI_NOTESINPLAINTEXT_EXT,
                         destination: str = '.',
                         extension: str = '',
                         ) -> None:
    ...
  @overload
  def write_deck_to_file(self, deck_idx: int,
                         filename: str | None = None,
                         file_type: str = _ANKI_NOTESINPLAINTEXT_EXT,
                         destination: str = '.',
                         extension: str = '',
                         ) -> None:
    ...
  def write_deck_to_file(self, deck, filename=None,
                         file_type=_ANKI_NOTESINPLAINTEXT_EXT,
                         destination='.', extension=''):
    """Writes a deck to a location in file storage. Supports various file naming
    features. See documentation for _generate_unique_file_path() for details on
    how the path is calculated. Will generate a unique filename if one is not
    given.

    Args:
      deck: A Deck object or an index indicating which deck to write.
      filename: The name to give to the newly created file. If none or if not
      unique, filename is generated by _generate_unique_file_path().
      file_type: The file type as designated by Anki. See
      (https://docs.ankiweb.net/exporting.html) for more information.
      destination: The directory to which the file will be written to.
      extension: The file extension, written after filename. Does not change
      functionality of written file and is purely for naming.

    Raises:
      OSError: Uses builtin open(). See open() Python documentation for more
      details (https://docs.python.org/3/library/functions.html#open)
      FileExistsError: _generate_unique_file_path() will generate unique
      filenames if a file already exists in a given path. Will not raise.
      ValueError: If argument passed for file_type is not a supported file type
    """
    if isinstance(deck, int):
      deck = self.get_deck(deck)
    file_path = _generate_unique_file_path(filename, extension, destination)
    encoding = _ANKI_EXPORT_ENCODING
    mode = 'x'
    with open(file_path, mode=mode, encoding=encoding, newline='') as f:
      if file_type in (_ANKI_NOTESINPLAINTEXT_EXT, _ANKI_NOTESINPLAINTEXT_EXT):
        deck.write_as_tsv(f)
      else:
        raise ValueError('Failed to write Deck to file. Expected a valid '
                       f'file_type but instead got {file_type}')

  def write_all_decks_to_file(self, **kwargs: Iterable[str | None]) -> None:
    """Writes all Decks stored in Gaggle to file. **kwargs is flattened and
    write_deck_to_file is called with each group of arguments. If there are more
    Decks than argument groups, prints the remaining decks using default values.
    **kwargs names and default values can be found in documentation for
    write_deck_to_file().

    Args:
      **kwargs: Dictionary of keyword to iterable of arguments. For more
      information, see documentation for write_deck_to_file()

    Raises:
      DecksNotWrittenException: If method fails to write all Decks to file.
      ValueError: See documentation for write_deck_to_file() for details
    """
    flat_kwargs = generate_flattened_kwargs_remove_sentinel(sentinel='',
                                                            **kwargs)
    last_written_deck_idx = None
    for idx, deck in enumerate(self._get_decks()):
      self.write_deck_to_file(deck, **next(flat_kwargs, {}))
      last_written_deck_idx = idx
    if last_written_deck_idx != self._get_num_decks() - 1:
      raise exceptions.DecksNotWrittenException(last_written_deck_idx)

  def _get_decks(self) -> list[AnkiDeck]:
    """Getter for list containing Deck objects in Gaggle

    Returns:
      List containing Deck objects store in Gaggle
    """
    return self.decks

  def get_deck(self, idx):
    return self.decks[idx]

  def _get_num_decks(self):
    return len(self.decks)

  def print_decks(self) -> None:
    """Outputs each AnkiCard contained in each Deck within the Gaggle to
    standard output using print() Python builtin.
    """
    for num, deck in enumerate(self.decks, start=1):
      print(f'Deck {num}:')
      for card in deck:
        print(card)


@overload
def transform_integer_value(value: RealNumber,
                            translation: int = 0,
                            scale: int = 1,
                            ) -> int:
  ...
@overload
def transform_integer_value(value: SupportsIndex,
                            translation: int = 0,
                            scale: int = 1,
                            ) -> SupportsIndex | int:
  ...
@overload
def transform_integer_value(value: _T,
                            translation: int = 0,
                            scale: int = 1,
                            ) -> _T | int:
  ...
def transform_integer_value(value, translation=0, scale=1):
  """Attempt to convert value into an int(). If successful, translate the
  resulting int and then scale it. If value cannot be converted, it is returned
  as is.

  For specifics on which values can be converted, see Python documentation for
  int().

  Args:
    value: The item to be cast into int
    translation: A mathematical translation, added to value
    scale: A mathematical scaling, multiplied with value

  Returns:
    The value unchanged if it cannot be converted. Otherwise, a translated then
    scaled int.
  """
  try:
    transformed_value = int(value)
  except ValueError:
    return value
  else:
    transformed_value += translation
    transformed_value *= scale
    return transformed_value


@overload
def _copy_and_reformat(original: AnkiHeader,
                       direction: ReformatDirection,
                       ) -> AnkiHeader:
  ...
@overload
def _copy_and_reformat(original: Mapping[str, _T],
                       direction: ReformatDirection,
                       ) -> dict[str, _T | int] | dict[str, _T] | AnkiHeader:
  ...
def _copy_and_reformat(original, direction):
  """Helper function to create a copy of a dictionary and format it as desired.
  Intended for internal use when writing a deck to stream.

  Args:
    original: A dictionary to make a deep copy of. Not modified.
    direction: The format style which the return value should take.

  Returns:
    A deep copy of the original dictionary, reformatted as specified.
  """
  deep_copy = copy.deepcopy(original)
  deep_copy = cast(dict[str, Any], deep_copy)
  reformat_header_settings(deep_copy, direction)
  return deep_copy


def reformat_header_settings(header: dict[str, Any],
                             direction: ReformatDirection,
                             ) -> None:
  """Convert between Anki header naming style and Gaggle header naming style.
  For more information on Anki header style, see documentation for
  gaggle.AnkiCard for a link to official Anki documentation. The Gaggle header
  naming style is snake case and uses 0-indexing.

  Transforms header in place.

  Args:
    header: A header read from an Anki file. Original entries are deleted and
    replaced by reformatted entries.
    direction: Denotes which style format the header should be converted to.
    Specified by gaggle.ReformatDirection enum.

  Returns:
    None; transforms header in place.

  Raises:
    KeyError: If argument passed for direction is not a supported conversion
  """
  translation = _DIRECTION_TRANSLATION_VALUE[direction]
  reformat_mapping = _DIRECTION_MAPPING[direction]
  reformatted_header = {}
  for setting, value in header.items():
    new_key = reformat_mapping[setting]
    new_value = transform_integer_value(value,
                                        translation=translation)
    reformatted_header[new_key] = new_value
  header.clear()
  header.update(reformatted_header)


def read_header_settings(f: ReadableAndSeekable[str]) -> AnkiHeader:
  """Reads in Anki Header from a stream and stores it into a dictionary. Strips
  all trailing whitespace characters from header value.

  Assumes input of a specific format, see documentation for parameter f.

  Args:
    f: A stream containing Anki Header information. Assumes input of format
    <header symbol><header setting name><header delimiter><header setting value>
    where header symbol is the denotation that the line is a part of the file
    header. The stream is left at the first line which does not contain
    <header symbol> as its first component. <header symbol> and
    <header delimiter> are specified by gaggle module constants.

  Returns:
    A mapping of settings specified by the Anki file header.
  """
  header_symbol = _ANKI_EXPORT_HEADER_LINE_SYMBOL
  header_separator = _ANKI_EXPORT_HEADER_DELIMITER_SYMBOL
  header = {}
  reader_pos = f.tell()
  while f.read(1) == header_symbol:
    line = f.readline()
    setting, value = line.split(header_separator)
    value = value.rstrip()
    value = transform_integer_value(value)
    header[setting] = value
    reader_pos = f.tell()
  f.seek(reader_pos)
  return header


def parse_header_settings(f: ReadableAndSeekable[str],
                          ) -> AnkiHeader:
  """Reads in all Anki file header settings, producing a mapping of setting
  name to setting value. Then reformats this mapping and returns it.

  Args:
    f: A stream from which lines are read. Read until no longer contains header
    information; stream left at first line with no header information, may be
    depleted. See read_header_settings() for more information.

  Returns:
    A mapping of setting name to setting value. The settings are formatted to
    ensure internal consistency with AnkiCard and AnkiDeck. See
    reformat_header_settings() documentation for more information.
  """
  header = read_header_settings(f)
  reformat_header_settings(header, direction=ReformatDirection.ANKI_TO_GAGGLE)
  return header


def _parse_anki_export(
    exported_file: StrOrBytesPath,
    field_names: Iterable[str] | None = None,
) -> tuple[AnkiHeader, list[AnkiCard]]:
  """Reads in a file exported from Anki. Determines file type through the header
  then parses all data accompanying the header using the header settings.

  Args:
    exported_file: A reference to a file exported by Anki
    field_names: The names to be used for referencing AnkiCard fields. See
      _generate_field_names() for implementation details.

  Returns:
    A Tuple(header, cards). header is a dictionary mapping setting names to
    setting values. cards is a series of AnkiCards. Both are read from the
    exported file.

  Raises:
    OSError: Uses Python builtin open(). See Pythong documentation for further
    information.
    FileNotFoundError: If file specified by exported_file does not exist
  """
  seperator_setting_key = _ANKI_EXPORT_HEADER_SETTING_SEPARATOR_NAME
  tsv = _ANKI_EXPORT_HEADER_SETTING_SEPARATOR_TSV_STRING
  cards = []
  with open(exported_file, encoding=_ANKI_EXPORT_ENCODING) as f:
    header = parse_header_settings(f)
    if header[seperator_setting_key] == tsv:
      del header[seperator_setting_key]
      cards = create_cards_from_tsv(f, field_names=field_names, header=header)
      header[seperator_setting_key] = tsv
  return header, cards


class AnkiDeck:
  """Represents a collection of Notes and Cards exported from Anki
  (i.e. gaggle.AnkiCards).

  Attributes:
    header: A dictionary mapping setting names to the setting value. The setting
    value is an int if it references a column of parsed data.
    cards: An iterable of gaggle.AnkiCards
  """
  def __init__(self,
               header: AnkiHeader,
               cards: Iterable[AnkiCard]):
    self.header = header
    self.cards = cards

  @classmethod
  def from_file(cls, file, field_names=None) -> Self:
    """Factory method to create an AnkiDeck directly from a file.

    Args:
      file: A string representing the file path of the information used to
      construct the deck.
      field_names: Strings representing the name of each field in each card. See
      documentation for _generate_field_names() for details on usage and
      structure.

    Returns:
      A gaggle.AnkiDeck object. See AnkiDeck documentation for more information.

    Raises:
      FileNotFoundError: If file specified by file does not exist
    """
    header, cards = _parse_anki_export(file, field_names)
    return cls(header, cards)

  def __iter__(self):
    return iter(self.cards)

  def get_header_setting(self, setting_name: str,
                         default: Any = None,
                         ) -> str | int:
    """Return the value of a header setting, referenced by name

    Args:
      setting_name: String representing the name of the setting, as named in
      Gaggle representation. A conversion from Anki naming to Gaggle naming can
      be referenced in _ANKI_EXPORT_HEADER_MAPPING.
      default: The value to return if no header setting with the given name is
      found.

    Returns:
      The found setting as stored. Else, default if a setting by name
      setting_name is not found.
    """
    return self.header.get(setting_name, default)

  def write_header(self, f: SupportsWrite[str]) -> None:
    """Outputs header settings stored in self.header.

    Setting a header value to None will prevent it from being output.

    Args:
      f: A stream implementing write(). See Gaggle.write_deck_to_file() for an
      example using open().

    Raises:
      KeyError: If AnkiDeck.header contains a header name not supported by
      reformat_header_settings()
    """
    header_symbol = _ANKI_EXPORT_HEADER_LINE_SYMBOL
    header_seperator = _ANKI_EXPORT_HEADER_DELIMITER_SYMBOL
    header_copy = _copy_and_reformat(self.header,
                                     direction=ReformatDirection.GAGGLE_TO_ANKI)
    for setting_name in _ANKI_ORDERED_HEADER:
      setting_value = header_copy.get(setting_name)
      if setting_value is not None:
        header_line = (f'{header_symbol}{setting_name}'
                       f'{header_seperator}{setting_value}\n')
        f.write(header_line)

  def write_as_tsv(self, f: SupportsWrite[str]) -> None:
    """Outputs header settings associated with deck. Then outputs the data
    fields of each AnkiCard stored in self.cards. One card per row.

    Requires only a stream to improve reusability as a public API. See
    Gaggle.write_deck_to_file() for a simpler setup.

    Args:
      f: A stream implementing write(). See Gaggle.write_deck_to_file() for an
      example using open().
    """
    self.write_header(f)
    w = csv.writer(f, dialect='excel-tab')
    for card in self.cards:
      card.write_as_tsv(w)


def create_cards_from_tsv(f, field_names=None, header=None) -> list[AnkiCard]:
  cards = csv.reader(f, dialect='excel-tab')
  deck = []
  for card in cards:
    anki_card = AnkiCard(card, field_names=field_names, **header)
    deck.append(anki_card)
  return deck

# Stack depth when resolving lazy evaluation in _generate_field_dict()
_stack_levels_to_anki_card_init_call = 4
@propagate_warnings_yield(_stack_levels_to_anki_card_init_call)
def _generate_field_names(field_names: Iterator[str],
                          fields: Iterator[_T],
                          reserved_names: Mapping[int, str],
                          seen_names: set[str]
                          ) -> Iterator[str]:
  """

  Args:
    field_names: The names which should be set for each delimited field in the
      parsed file. Used for reference, does not modify read contents. Use any
      Falsy value to apply a default field name. The length of field_names does
      not have to match the length of the delimited fields. Missing names will
      be generated with a default and extra names will be discarded.
    n_fields: The number of fields contained in the AnkiCard.

  Returns:

  """
  for count in itertools.count():
    name = next(field_names, None)
    field_to_be_named = next(fields, None)
    if field_to_be_named is None:
      if name is not None:
        warnings.warn(f'More field names than fields. The following field '
                      f'names were not used: {name} {" ".join(field_names)}')
      return
    if (reserved_name := reserved_names.get(count)) is not None:
      yield reserved_name
    else:
      if name in seen_names:
        warnings.warn(f'Duplicate field name (replaced with: Field{count}): '
                      f'{name}')
        name = None
      if not name:
        name = f'Field{count}'
        if name in seen_names:
          raise ValueError(f'Index-associated generic name duplicated. '
                           f'Duplicated value: {name}')
      yield name
      seen_names.add(name)


def _generate_field_dict(field_names: Iterator[_T],
                         fields: Iterator[_S],
                         ) -> collections.OrderedDict[_T, _S]:
  """Create a dictionary mapping given names to a value in AnkiCard.

  Args:
    field_names: Names used for referencing values stored in the field dict.
    Special properties exist for fields named by the header.
    Must match the length of fields.
    fields: The values to be stored in an AnkiCard.

  Returns:
    Named values whose iteration order is the same as read from file.
  """
  name_field_tuples = zip(field_names, fields, strict=True)
  return collections.OrderedDict(name_field_tuples)


def _parse_anki_header_bool(bool_as_str: HeaderBoolean) -> bool:
  """Translate boolean notation from Anki generated file header to Python
  bool type.

  Args:
    bool_as_str: The string representation of a boolean value as used internally
    by Anki

  Returns:
    True or False depending on value parsed from the AnkiHeader.

  Raises:
    ValueError: If bool_as_str is not the representation for True or False used
    by Anki
  """
  if bool_as_str == HeaderBoolean.TRUE_:
    return True
  elif bool_as_str == HeaderBoolean.FALSE_:
    return False
  else:
    raise ValueError(f'Expected {HeaderBoolean.TRUE_} or '
                     f'{HeaderBoolean.FALSE_} but instead got '
                     f'{bool_as_str}')


class AnkiCard:
  """
  Anki Card fields as denoted by Anki documentation
  Up to date reference:
  https://docs.ankiweb.net/importing.html#file-headers
  Permanent Reference [09 May 2023]:
  https://github.com/ankitects/anki-manual/blob/0aa372146d10e299631e361769f41533a6d4a417/src/importing.md?plain=1#L196-L220
  """
  _reserved_names = ['Tags', 'Deck', 'Note Type', 'GUID']
  def __init__(self,
               fields: Iterable[str],
               has_html: HeaderBoolean = HeaderBoolean.FALSE_,
               tags_idx: int | None = None,
               field_names: Iterable[str] | None = None,
               note_type_idx: int | None = None,
               deck_idx: int | None = None,
               guid_idx: int | None = None):
    if field_names is None:
      field_names = ()
    self.has_html = _parse_anki_header_bool(has_html)
    property_indexes = [tags_idx, deck_idx, note_type_idx, guid_idx]
    reserved_names = {
      index: name
      for index, name in zip(property_indexes, AnkiCard._reserved_names,
                             strict=True)
      if index is not None
    }
    reserved_name_set = set(AnkiCard._reserved_names)
    field_names = _generate_field_names(iter(field_names), iter(fields),
                                        reserved_names, reserved_name_set)
    self.fields = _generate_field_dict(iter(field_names), iter(fields))

  @property
  def tags(self) -> str:
    """This property is a reserved name, a field cannot be manually named
    Note Type. It must be set using the tags_idx parameter of AnkiCard.

    Returns:
      Anki program tags, delimited with '::' when generated by Anki

    Raises:
      KeyError: If no field with the name 'Tags' exists
    """
    return self.get_field('Tags')

  @property
  def note_type(self) -> str:
    """This property is a reserved name, a field cannot be manually named
    Note Type. It must be set using the note_type_idx parameter of AnkiCard.

    Returns:
      Anki program note type. This name reflects the expected fields and
      css/html within the Anki program.

    Raises:
      KeyError: If no field with the name 'Note Type' exists
    """
    return self.get_field('Note Type')

  @property
  def deck_name(self) -> str:
    """This property is a reserved name, a field cannot be manually named
    Deck. It must be set using the deck_idx parameter of AnkiCard.

    Returns:
      Anki program deck name, delimited with '::' when generated by Anki.
      This reflects the nested structure of decks saved within the Anki program,
      where the outer layer is ordered first. For example:

      'First Grouping::First Subgroup::Deck 3'

    Raises:
      KeyError: If no field with the name 'Deck' exists
    """
    return self.get_field('Deck')

  @property
  def guid(self) -> str:
    """This property is a reserved name, a field cannot be manually named
    GUID. It must be set using the guid_idx parameter of AnkiCard.

    Returns:
      A GUID used internally by the Anki program. It is used to update existing
      cards should a card with a matching GUID be imported. Per Anki
      documentation, it is not recommended to manually set this value yourself.

    Raises:
      KeyError: If no field with the name 'GUID' exists
    """
    return self.get_field('GUID')

  def __repr__(self):
    return str(self.fields)

  def get_field(self, field_name):
    return self.fields[field_name]

  def as_str_list(self) -> list[str]:
    """Return data fields of AnkiCard. Preserves read-in order.

    Returns:
      List of strings. Each string is an individual data value stored in
      AnkiCard. The order of the strings is the same order as the AnkiCard was
      read from file.

      Assume a file with three values was read. For example:

      [column0, column1, column2]

    """
    str_list = []
    for field_value in self.fields.values():
      str_list.append(field_value)
    return str_list

  def write_as_tsv(self, w: SupportsWriteRow) -> None:
    """Output data fields of AnkiCard in TSV format.

    Requires only a stream to improve reusability as a public API. See
    AnkiDeck.write_as_tsv() for a simpler setup.

    Args:
      w: The stream to write to. Must have internal formatting data.
        See AnkiDeck.write_as_tsv() for an example using csv.writer.
    """
    content = self.as_str_list()
    w.writerow(content)
