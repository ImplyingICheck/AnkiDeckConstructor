"""Base class for Anki card"""

class AnkiCard:
  """
  Anki Card fields as denoted by Anki documentation
  Up to date reference:
  https://docs.ankiweb.net/importing.html#file-headers
  Permanent Reference [09 May 2023]:
  https://github.com/ankitects/anki-manual/blob/0aa372146d10e299631e361769f41533a6d4a417/src/importing.md?plain=1#L196-L220
  """
  def __init__(self, fields, has_html=False, tags_idx=None, field_names=None,
               note_type_idx=None, deck_idx=None, guid_idx=None):
    self.has_html = has_html
    self.tags_field_idx = tags_idx
    self.field_names = self.__generate_field_names(field_names, len(fields))
    self.fields = self.__generate_field_dict(self.field_names, fields)
    self.note_type_field = note_type_idx
    self.deck_field_idx = deck_idx
    self.guid_field_idx = guid_idx

  def __repr__(self):
    return str(self.fields)

  @staticmethod
  def __generate_field_names(field_names, n_fields):
    if field_names is None:
      field_names = []
    if len(field_names) == n_fields:
      return field_names
    else:
      range_start = len(field_names)
      range_stop = n_fields
      for idx in range(range_start, range_stop):
        field_names.append(f'Field{idx}')
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
