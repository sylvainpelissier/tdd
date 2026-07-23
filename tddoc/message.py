from . import data_definition
import re

__doc__ = "Message part"

GS = '\x1d'
RS = '\x1e'

class Data:
    "A data entry"
    def __init__(self, group, definition, value):
        self.group = group
        self.definition = definition
        self.value = value

class VariableData(Data):
    "A variable length data entry"
    def __init__(self, group, definition, value, complete = True):
        super().__init__(group, definition, value)
        self.complete = complete
    
class FixedData(Data):
    "A fixed length data entry"
    pass

class Message:
    "A message"
    def __init__(self, perimeter_id, dataset):
        self.perimeter_id = perimeter_id
        self.dataset = list(dataset)
        
class C40Message(Message):
    "A C40 message"
    def encode(self, max_length = None):
        raise NotImplementedError()

    @classmethod
    def from_code(cls, perimeter_id, code):
        """
        Load a message from a C40 code string, for a given perimeter ID.
        """
        self = cls(perimeter_id, [])
        while code:
            data, code = self.code_extract(code)
            self.dataset.append(data)
        return self

    @classmethod
    def fixed_parse(cls, group, definition, code):
        """
        Parse a fixed size data item in the stream
        """
        value = definition.encoding.parse(code[2:2 + definition.fixed])
        data = FixedData(group, definition, value)
        if code[2 + definition.fixed : 2 + definition.fixed + 1] == GS:
            return data, code[2 + definition.fixed + 1 : ]
        return data, code[2 + definition.fixed : ]

    @classmethod
    def variable_parse(cls, group, definition, code):
        """
        Parse a variable size data item in the stream
        """
        end_index = definition.encoding.size_max + 2 \
            if definition.encoding.size_max is not None \
            else len(code)

        try:
            data_end = code.index(RS, 2, end_index)
            complete = False
        except:
            complete = True
            try:
                data_end = code.index(GS, 2, end_index)
            except:
                data_end = end_index

        if hasattr(definition.encoding, "allowed_format"):
            value = re.match(r'^(' + definition.encoding.allowed_format.pattern + r')', code[2:data_end]).group(1)
        else:
            value = code[2:data_end]

        parsed = definition.encoding.parse(value)
        data = FixedData(group, definition, parsed)
        try:
            next_data = code[2 + len(value)]
        except:
            return data, ""
        if next_data in [RS, GS]:
            return data, code[2 + len(value) + 1:]
        else:
            return data, code[2 + len(value):]

    def code_extract(self, code):
        """
        Parse next data item in the stream
        """
        group, definition = data_definition.c40.datatype_get(self.perimeter_id, code[:2])
        if definition.fixed is not None:
            return self.fixed_parse(group, definition, code)
        return self.variable_parse(group, definition, code)

