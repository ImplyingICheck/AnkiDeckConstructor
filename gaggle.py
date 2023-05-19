"""Base class for collection, a class representing multiple Anki Decks."""
import csv
import os.path
import ankicard


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
  modified_filename = filename
  while file_exists:
    complete_filename = f'{modified_filename}{extension}'
    file_path = os.path.join(destination, complete_filename)
    file_exists = os.path.isfile(file_path)
    if file_exists:
      modified_filename = f'{filename}{tag}'
      tag += 1
  return modified_filename


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

  def write_deck_to_file(self, deck_idx, filename=None, file_type=None,
                         destination='.', extension=''):
    encoding = _ANKI_EXPORT_ENCODING
    mode = 'x'
    file_path = _generate_unique_file_path(filename, extension, destination)
    if file_type in (_ANKI_NOTESINPLAINTEXT_EXT, _ANKI_NOTESINPLAINTEXT_EXT):
      with open(file_path, mode=mode, encoding=encoding, newline='') as f:
        w = csv.writer(f, dialect='excel-tab')
        for card in self.decks[deck_idx]:
          card_strs = card.as_str_list()
          w.writerow(card_strs)

  def _get_decks(self):
    return self.decks

  def _get_num_decks(self):
    return len(self.decks)

  def print_decks(self):
    for num, deck in enumerate(self.decks, start=1):
      print(f'Deck {num}:')
      for card in deck:
        print(card)
