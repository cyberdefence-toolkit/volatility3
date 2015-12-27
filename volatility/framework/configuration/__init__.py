"""
Created on 7 May 2013

@author: mike
"""

from volatility.framework.interfaces.configuration import ConfigurationSchemaNode, Configurable


class InstanceRequirement(ConfigurationSchemaNode):
    instance_type = bool

    def validate(self, value, _context, valid_children = None):
        # Child_results can be ignored because no instance class should have children
        # We don't ban child_results in case someone wants to extend this in some meaningful way
        if not isinstance(value, self.instance_type):
            raise TypeError(self.name + " input only accepts " + self.instance_type.__name__ + " type")


class IntRequirement(InstanceRequirement):
    instance_type = int


class StringRequirement(InstanceRequirement):
    # TODO: Maybe add string length limits?
    instance_type = str


class TranslationLayerRequirement(ConfigurationSchemaNode, Configurable):
    """Class maintaining the limitations on what sort of address spaces are acceptable"""

    def __init__(self, name, description = None, default = None,
                 optional = False, layer_name = None):
        """Constructs a Translation Layer Requirement

        The configuration option's value will be the name of the layer once it exists in the store

        :param name: Name of the configuration requirement
        :param layer_name: String detailing the expected name of the required layer, this can be None if it is to be randomly generated
        :return:
        """
        ConfigurationSchemaNode.__init__(name, description, default, optional)
        Configurable.__init__(self)
        self._layer_name = layer_name

    @classmethod
    def get_schema(cls):
        # Runs through each of the available translation layers, determining what they're capable of,
        # and adding their requirements (tagged with their class) to a Disjunction config schema node
        pass

    # TODO: Add requirements: acceptable OSes from the address_space information
    # TODO: Add requirements: acceptable arches from the available layers

    def validate(self, value, context, valid_children = None):
        """Validate that the value is a valid layer name and that the layer adheres to the requirements"""
        if not isinstance(value, str):
            raise TypeError("TranslationLayerRequirements only accepts string labels")
        if value not in context.memory:
            raise IndexError((value or "") + " is not a memory layer")


class ChoiceRequirement(ConfigurationSchemaNode):
    """Allows one from a choice of strings
    """

    def __init__(self, choices, *args, **kwargs):
        ConfigurationSchemaNode.__init__(self, *args, **kwargs)
        if not isinstance(choices, list) or any([not isinstance(choice, str) for choice in choices]):
            raise TypeError("ChoiceRequirement takes a list of strings as choices")
        self._choices = choices

    def validate(self, value, context, valid_children = None):
        """Validates the provided value to ensure it is one of the available choices"""
        if value not in self._choices:
            raise ValueError("Value is not within the set of available choices")


class ListRequirement(ConfigurationSchemaNode):
    def __init__(self, element_type, max_elements, min_elements, *args, **kwargs):
        ConfigurationSchemaNode.__init__(self, *args, **kwargs)
        if isinstance(element_type, ListRequirement):
            raise TypeError("ListRequirements cannot contain ListRequirements")
        self.element_type = self._type_check(element_type, ConfigurationSchemaNode)
        self.min_elements = min_elements
        self.max_elements = max_elements

    def validate(self, value, context, valid_children = None):
        """Check the types on each of the returned values and then call the element type's check for each one"""
        self._type_check(value, list)
        if not all([self._type_check(element, self.element_type) for element in value]):
            raise TypeError("At least one element in the list is not of the correct type.")
        if not (self.min_elements <= len(value) <= self.max_elements):
            raise TypeError("List option provided more or less elements than allowed.")
        for element in value:
            self.element_type.validate(element, context)


class DisjunctionRequirement(ConfigurationSchemaNode):
    """Class allowing any of multiple requirements"""

    def __init__(self, requirements, *args, **kwargs):
        # TODO: Type check requirements to ensure it's a dictionary of requirements
        ConfigurationSchemaNode.__init__(self, *args, **kwargs)
        for requirement in requirements:
            self.add_item(requirement)

    def validate(self, value, context, valid_children = None):
        if valid_children is None:
            raise ValueError("A Disjunction requirement cannot exist without children")
        if not any(valid_children):
            raise ValueError("No valid children to support the Disjunction Requirement")


class ConjunctionRequirement(ConfigurationSchemaNode):
    """Class requiring all of multiple requirements"""

    def __init__(self, requirements, *args, **kwargs):
        # TODO: Type check requirements to ensure it's a dictionary of requirements
        ConfigurationSchemaNode.__init__(self, *args, **kwargs)
        for requirement in requirements:
            self.add_item(requirement)

    def validate(self, value, context, valid_children = None):
        if valid_children is None:
            raise ValueError("A Conjunction requirement cannot exist without children")
        if not all(valid_children):
            raise ValueError("An invalid child prevents the Conjunction Requirement")
