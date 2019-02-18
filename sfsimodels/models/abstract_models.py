from collections import OrderedDict
import copy
# from sfsimodels.loader import add_inputs_to_object
import types
from sfsimodels.exceptions import ModelError
from sfsimodels import functions as sf


class PhysicalObject(object):
    _counter = 0
    type = "physical_object"
    inputs = ()
    skip_list = ()

    def __iter__(self):  # real signature unknown
        return self

    # def __init__(self, **kwargs):
    #     # super(PhysicalObject, self).__init__()
    #     print("Initialised")

    @property
    def attributes(self):
        all_attributes = []
        for item in self.__dir__():
            if item in ["deepcopy", "set", "to_dict"]:
                continue
            if isinstance(item, types.MethodType):
                continue
            if "_" != item[0]:
                all_attributes.append(item)
        all_attributes.sort()
        return all_attributes

    def __next__(self):
        self._counter += 1
        all_attributes = self.attributes
        if self._counter == len(all_attributes):
            raise StopIteration
        return all_attributes[self._counter]

    def set(self, values):
        """
        Set the object parameters using a dictionary
        """
        if hasattr(self, "inputs"):
            for item in self.inputs:
                if hasattr(self, item):
                    setattr(self, item, values[item])

    def deepcopy(self):
        """ Make a clone of the object """
        return copy.deepcopy(self)

    @property
    def ancestor_types(self):
        return ["physical_object"]

    def add_from_same(self, obj, inputs_from="obj", update_inputs=True):
        if not hasattr(self, "inputs"):
            raise ModelError("self does not contain attribute: 'inputs'")
        if inputs_from == "obj":
            if hasattr(obj, "inputs"):
                inputs_list = obj.inputs
            else:
                raise ModelError("obj does not contain attribute: 'inputs'")
        else:
            inputs_list = self.inputs
        for item in inputs_list:
            if hasattr(obj, item):
                setattr(self, item, getattr(obj, item))
                if update_inputs and item not in self.inputs:
                    self.inputs.append(item)

    def to_dict(self, extra=(), **kwargs):
        outputs = OrderedDict()
        export_none = kwargs.get("export_none", True)
        if hasattr(self, "inputs"):
            full_inputs = list(self.inputs) + list(extra)
        else:
            full_inputs = list(extra)
        for item in full_inputs:
            if item not in self.skip_list:
                value = self.__getattribute__(item)
                if not export_none and value is None:
                    continue
                outputs[item] = sf.collect_serial_value(value)
        return outputs


class CustomObject(PhysicalObject):
    """
    An object to describe structures.
    """
    _id = None
    name = None
    base_type = "custom_object"
    type = "custom_object"

    def __init__(self):
        self.inputs = [
            "id",
            "name",
            "base_type",
            "type"
            ]

    @property
    def id(self):
        """
        Object id
        :return:
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def ancestor_types(self):
        return ["custom"]
