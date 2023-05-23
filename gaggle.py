"""Base class for collection, a class representing multiple Anki Decks."""
import csv
import os.path
import ankicard
import itertools
import exceptions

from typing import overload

_ANKI_EXPORT_HEADER_SYMBOL = '#'
_ANKI_EXPORT_HEADER_SEPARATOR_SYMBOL = ':'
_ANKI_EXPORT_ENCODING = 'utf-8'
_ANKI_EXPORT_HEADER_SETTING_SEPARATOR = 'separator'
_ANKI_EXPORT_HEADER_MAPPING = {
  'html':'has_html', 'tags column':'tags_idx',
  'notetype column':'note_type_idx', 'deck column':'deck_idx',
  'guid column':'guid_idx'}
_ANKI_EXPORT_HEADER_MAPPING_KEYS = set(_ANKI_EXPORT_HEADER_MAPPING.keys())
_ANKI_NOTESINPLAINTEXT_EXT = '.txt'
_ANKI_CARDSINPLAINTEXT_EXT = '.txt'

_GENERIC_EXPORT_FILE_NAME = 'GaggleFile'

def convert_ankicol_to_zero_based_numbering(ankicol_value):
  try:
    ankicol = int(ankicol_value)
  except ValueError:
    return ankicol_value
  else:
    zero_based_idx = ankicol - 1
    return zero_based_idx

def reformat_header_settings(header):
  reformated_settings = []
  new_settings = {}
  for setting in header.keys():
    if setting in _ANKI_EXPORT_HEADER_MAPPING_KEYS:
      value = header[setting]
      new_key = _ANKI_EXPORT_HEADER_MAPPING[setting]
      new_value = convert_ankicol_to_zero_based_numbering(value)
      new_settings[new_key] = new_value
      reformated_settings.append(setting)
  for setting in reformated_settings:
    del header[setting]
  del header[_ANKI_EXPORT_HEADER_SETTING_SEPARATOR]
  header.update(new_settings)

def create_cards_from_tsv(f, field_names=None, header=None):
  reformat_header_settings(header)
  cards = csv.reader(f, dialect='excel-tab')
  deck = []
  for card in cards:
    card = ankicard.AnkiCard(card, field_names=field_names, **header)
    deck.append(card)
  return deck

def parse_txt_file_header(f):
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

def parse_anki_export(exported_file, field_names=None):
  deck = []
  with open(exported_file, newline='', encoding=_ANKI_EXPORT_ENCODING) as f:
    header = parse_txt_file_header(f)
    if header['separator'] == 'tab':
      deck = create_cards_from_tsv(f, field_names=field_names, header=header)
  return deck

def _initialise_decks(exported_file, field_names):
  initial_deck = []
  if not exported_file:
    return initial_deck
  initial_deck.append(parse_anki_export(exported_file, field_names))
  return initial_deck

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


def generate_flattened_kwargs(**kwargs):
  keyword_argument_mappings = map(zip,
                                  itertools.cycle([kwargs]),
                                  itertools.zip_longest(*kwargs.values()))
  for keyword_arguments in list(keyword_argument_mappings):
    flat_kwargs = dict(keyword_arguments)
    yield flat_kwargs

def generate_flattened_kwargs_with_sentinel(sentinel=None, **kwargs):
  arguments = itertools.zip_longest(*kwargs.values(), fillvalue=sentinel)
  arguments, sentinel_filter = itertools.tee(arguments)
  keyword_argument_pairs = map(zip,
                               itertools.cycle([kwargs]),
                               arguments)
  filtered_pairs = map(itertools.compress,
                       keyword_argument_pairs,
                       sentinel_filter)
  for keyword_arguments in filtered_pairs:
    yield dict(keyword_arguments)

class Gaggle:
  """
  Parser class for Anki exported files.
  Handles deck construction and organisation.
  """
  def __init__(self, exported_file=None, field_names=None):
    self.decks = _initialise_decks(exported_file, field_names)

  def add_deck(self, deck):
    self.decks.append(deck)

  def add_deck_from_file(self, file):
    deck = parse_anki_export(file)
    self.add_deck(deck)

  @overload
  def write_deck_to_file(self, deck: 'Deck',
                         filename: str | None = None,
                         file_type: str | None = None,
                         destination: str | None = '.',
                         extension: str | None = '',
                         ) -> None:
    ...
  @overload
  def write_deck_to_file(self, deck: str,
                         filename: str | None = None,
                         file_type: str | None = None,
                         destination: str | None = '.',
                         extension: str | None = '',
                         ) -> None:
    ...
  def write_deck_to_file(self, deck, filename=None, file_type=None,
                         destination='.', extension=''):
    if isinstance(deck, int):
      deck = self.get_deck(deck)
    file_type = file_type or _ANKI_NOTESINPLAINTEXT_EXT
    destination = destination or '.'
    if extension is None:
      extension = ''
    encoding = _ANKI_EXPORT_ENCODING
    mode = 'x'
    file_path = _generate_unique_file_path(filename, extension, destination)
    if file_type in (_ANKI_NOTESINPLAINTEXT_EXT, _ANKI_NOTESINPLAINTEXT_EXT):
      with open(file_path, mode=mode, encoding=encoding, newline='') as f:
        w = csv.writer(f, dialect='excel-tab')
        for card in deck:
          card_strs = card.as_str_list()
          w.writerow(card_strs)

  def write_all_decks_to_file(self, **kwargs):
    flat_kwargs = generate_flattened_kwargs(**kwargs)
    last_written_deck_idx = None
    for idx, deck in enumerate(self._get_decks()):
      self.write_deck_to_file(deck, **next(flat_kwargs, {}))
      last_written_deck_idx = idx
    if last_written_deck_idx != self._get_num_decks() - 1:
      raise exceptions.DecksNotWrittenException(last_written_deck_idx)

  def _get_decks(self):
    return self.decks

  def get_deck(self, idx):
    return self.decks[idx]

  def _get_num_decks(self):
    return len(self.decks)

  def print_decks(self):
    for num, deck in enumerate(self.decks, start=1):
      print(f'Deck {num}:')
      for card in deck:
        print(card)
