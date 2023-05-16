"""Base class for collection, a class representing multiple Anki Decks."""
import csv
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

def convert_ankicol_to_gagglecol(ankicol_value):
  try:
    ankicol = int(ankicol_value)
    gagglecol = ankicol - 1
    return gagglecol
  except ValueError:
    return ankicol_value

def reformat_header_settings(header):
  reformated_settings = []
  new_settings = {}
  for setting in header.keys():
    if setting in _ANKI_EXPORT_HEADER_MAPPING_KEYS:
      value = header[setting]
      new_key = _ANKI_EXPORT_HEADER_MAPPING[setting]
      new_value = convert_ankicol_to_gagglecol(value)
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

  def print_decks(self):
    for num, deck in enumerate(self.decks, start=1):
      print(f'Deck {num}:')
      for card in deck:
        print(card)
