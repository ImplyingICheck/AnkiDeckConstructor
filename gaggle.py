"""Base class for collection, a class representing multiple Anki Decks."""
import csv
import ankicard
_ANKI_EXPORT_HEADER_SYMBOL = '#'
_ANKI_EXPORT_HEADER_SEPARATOR_SYMBOL = ':'
_ANKI_EXPORT_ENCODING = 'utf-8'
class Gaggle:
  """
  Parser class for Anki exported files.
  Handles deck construction and organisation.
  """
  def __init__(self, exported_file=None):
    self.decks = self.__initialise_decks(exported_file)

  def __initialise_decks(self, exported_file):
    if not exported_file:
      return []
    return [self.parse_anki_export(exported_file)]
  def add_deck(self, deck):
    self.decks.append(deck)
  def add_deck_from_file(self, file):
    deck = self.parse_anki_export(file)
    self.add_deck(deck)

  def print_decks(self):
    for num, deck in enumerate(self.decks, start=1):
      print(f'Deck {num}:')
      for card in deck:
        print(card)

  @staticmethod
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

  @staticmethod
  def create_cards_from_tsv(f):
    cards = csv.reader(f, dialect='excel-tab')
    deck = []
    for card in cards:
      card = ankicard.AnkiCard(card)
      deck.append(card)
    return deck

  def parse_anki_export(self, exported_file, field_names=None):
    deck = []
    with open(exported_file, newline='', encoding=_ANKI_EXPORT_ENCODING) as f:
      header = self.parse_txt_file_header(f)
      if header['separator'] == 'tab':
        deck = self.create_cards_from_tsv(f, field_names)
    return deck
