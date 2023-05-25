"""Definition of project-wide exceptions"""

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
