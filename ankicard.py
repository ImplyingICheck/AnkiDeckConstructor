"""Base class for Anki card"""

class AnkiCard:
  """
  Anki Card fields as denoted by Anki documentation
  Up to date reference:
  https://docs.ankiweb.net/importing.html#file-headers
  Permanent Reference [09 May 2023]:
  https://github.com/ankitects/anki-manual/blob/0aa372146d10e299631e361769f41533a6d4a417/src/importing.md?plain=1#L196-L220
  """
  def __init__(self, fields, has_html=False, tags=None, field_names=None,
               note_type=None, deck=None, guid=None):
    self.has_html = has_html
    self.tags = tags
    self.field_names = self.__generate_field_names(field_names, len(fields))
    self.fields = self.__generate_field_dict(self.field_names, fields)
    self.note_type = note_type
    self.deck = deck
    self.guid = guid
  def __repr__(self):
    return str(self.fields)
  @staticmethod
  def __generate_field_names(field_names, n_fields):
    if field_names:
      return field_names
    field_names = []
    for idx in range(n_fields):
      curr_field_name = f'Field{idx}'
      field_names.append(curr_field_name)
    return field_names

  @staticmethod
  def __generate_field_dict(field_names, fields):
    field_dict = {}
    for idx in range(len(field_names)):
      field_dict[field_names[idx]] = fields[idx]
    return field_dict

  def get_field(self, field_name):
    return self.fields[field_name]

  def get_field_names(self):
    return self.field_names
