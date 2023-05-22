"""Definition of project-wide exceptions"""

class DecksNotWrittenException(Exception):
  def __init__(self, last_deck_written: int | None = None):
    self.last_deck_written = last_deck_written

  def __str__(self):
    return (f'Failed to write all Decks to the file. '
            f'Last deck successfully written was the deck at: '
            f'Index {self.last_deck_written}')
