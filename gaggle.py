"""Base class for collection, a class representing multiple Anki Decks."""
from __future__ import annotations

import copy
import csv
import os.path
import itertools
import operator
from typing import overload, Any, List, Protocol, Self, TypeVar
from collections.abc import Iterable, Iterator

import exceptions
import ankicard

_ANKI_EXPORT_HEADER_SYMBOL = '#'
_ANKI_EXPORT_HEADER_SEPARATOR_SYMBOL = ':'
_ANKI_EXPORT_ENCODING = 'utf-8'
_ANKI_EXPORT_HEADER_SETTING_SEPARATOR_NAME = 'separator'
_ANKI_EXPORT_HEADER_SETTING_SEPARATOR_TSV_STRING = 'tab'
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

_GENERIC_EXPORT_FILE_NAME = 'GaggleFile'
ANKI_TO_GAGGLE = 'anki_to_gaggle'
GAGGLE_TO_ANKI = 'gaggle_to_anki'
_DIRECTION_TRANSLATION_VALUE = {ANKI_TO_GAGGLE: -1, GAGGLE_TO_ANKI: 1}
_DIRECTION_MAPPING = {ANKI_TO_GAGGLE: _ANKI_EXPORT_HEADER_MAPPING,
                      GAGGLE_TO_ANKI: _ANKI_EXPORT_HEADER_MAPPING_REVERSE}

class HasIndex(Protocol):
  def __index__(self) -> int:
    ...

class HasInt(Protocol):
  def __int__(self) -> int:
    ...

class HasTruncate(Protocol):
  def __trunc__(self) -> int:
    ...

class Falsy(Protocol):
  def __bool__(self) -> bool:
    return False

T = TypeVar('T')
RealNumber = TypeVar('RealNumber', HasInt, HasTruncate)


@overload
def transform_integer_value(value: T,
                            translation: int = 0,
                            scale: int = 1,
                            ) -> T:
  ...
@overload
def transform_integer_value(value: HasIndex,
                            translation: int = 0,
                            scale: int = 1,
                            ) -> HasIndex | int:
  ...
@overload
def transform_integer_value(value: RealNumber,
                            translation: int = 0,
                            scale: int = 1,
                            ) -> int:
  ...
def transform_integer_value(value, translation=0, scale=1):
  try:
    transformed_value = int(value)
  except ValueError:
    return value
  else:
    transformed_value += translation
    transformed_value *= scale
    return transformed_value


# TODO: Move to class declaration of AnkiCard after refactor
def create_cards_from_tsv(f, field_names=None, header=None):
  cards = csv.reader(f, dialect='excel-tab')
  deck = []
  for card in cards:
    card = ankicard.AnkiCard(card, field_names=field_names, **header)
    deck.append(card)
  return deck


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
    filename = _GENERIC_EXPORT_FILE_NAME
  file_exists = True
  tag = 0
  if filename == _GENERIC_EXPORT_FILE_NAME:
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
  keyword_argument_mappings = map(zip,
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
  keyword_argument_pairs = map(zip,
                               itertools.repeat(kwargs),
                               arguments)
  filtered_pairs = map(itertools.compress,
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
  keyword_argument_pairs = map(zip,
                               itertools.repeat(kwargs),
                               arguments)
  sentinel_filter = map(operator.ne,
                        itertools.chain.from_iterable(sentinel_filter),
                        itertools.repeat(sentinel))
  filtered_keyword_argument_pairs = map(itertools.compress,
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
    encoding = _ANKI_EXPORT_ENCODING
    mode = 'x'
    file_path = _generate_unique_file_path(filename, extension, destination)
    if file_type in (_ANKI_NOTESINPLAINTEXT_EXT, _ANKI_NOTESINPLAINTEXT_EXT):
      with open(file_path, mode=mode, encoding=encoding, newline='') as f:
        w = csv.writer(f, dialect='excel-tab')
        for card in deck:
          card_strs = card.as_str_list()
          w.writerow(card_strs)
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

  def _get_decks(self) -> List[AnkiDeck]:
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


def copy_and_reformat(original: dict, direction: 'ReformatDirection'):
  deep_copy = copy.deepcopy(original)
  reformat_header_settings(deep_copy, direction)
  return deep_copy


def reformat_header_settings(header: dict, direction: 'ReformatDirection'):
  """

  Args:
    header:
    direction:

  Returns:

  Raises:
    KeyError: If argument passed for direction is not a supported conversion
  """
  # TODO: make a custom exception, can shadow header[setting] KeyError
  translation = _DIRECTION_TRANSLATION_VALUE[direction]
  reformat_mapping = _DIRECTION_MAPPING[direction]
  reformatted_header = {}
  for setting, value in header.items():
    value = header[setting]
    new_key = reformat_mapping[setting]
    new_value = transform_integer_value(value,
                                        translation=translation)
    reformatted_header[new_key] = new_value
  header.clear()
  header.update(reformatted_header)


def read_header_settings(f):
  header_symbol = _ANKI_EXPORT_HEADER_SYMBOL
  header_separator = _ANKI_EXPORT_HEADER_SEPARATOR_SYMBOL
  header = {}
  reader_pos = f.tell()
  while f.read(1) == header_symbol:
    line = f.readline()
    setting, value = line.split(header_separator)
    value = value.rstrip()
    header[setting] = value
    reader_pos = f.tell()
  f.seek(reader_pos)
  return header


def parse_header_settings(f):
  header = read_header_settings(f)
  reformat_header_settings(header, direction=ANKI_TO_GAGGLE)
  return header


def _parse_anki_export(exported_file, field_names=None):
  """

  Args:
    exported_file:
    field_names:

  Returns:

  Raises:
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
  (i.e. gaggle.AnkiCards)."""
  def __init__(self,
               header: dict[str, str | int],
               cards: Iterable[ankicard.AnkiCard]):
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
      A gaggle.AnkiDeck object

    Raises:
      FileNotFoundError: If file specified by file does not exist
    """
    header, cards = _parse_anki_export(file, field_names)
    return cls(header, cards)

  def __iter__(self):
    return iter(self.cards)

  def get_cards(self) -> Iterable[ankicard.AnkiCard]:
    """Getter method for AnkiDeck.cards

    Returns:
      Iterable of AnkiCards
    """
    return self.cards

  def get_header(self):
    return self.header

  def get_header_setting(self, setting: str, default: Any = None):
    header = self.get_header()
    return header.get(setting, default)

  def write_header(self, f):
    """

    Args:
      f:

    Returns:
    Raises:
      KeyError: If AnkiDeck.header contains a header name not supported
    """
    header_symbol = _ANKI_EXPORT_HEADER_SYMBOL
    header_seperator = _ANKI_EXPORT_HEADER_SEPARATOR_SYMBOL
    header_copy = copy_and_reformat(self.header, direction=GAGGLE_TO_ANKI)
    for setting_name in _ANKI_ORDERED_HEADER:
      setting_value = header_copy[setting_name]
      if setting_value is not None:
        header_line = (f'{header_symbol}{setting_name}'
                       f'{header_seperator}{setting_value}\n')
        f.write(header_line)
