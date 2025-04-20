#!/usr/bin/env python3

from enum import Enum


class MessagePerformative(Enum):
    """MessagePerformative enum class.
    Enumeration containing the possible message performative.
    """
    REQUEST = 1
    DOING = 2

    def __str__(self):
        """Returns the name of the enum item.
        """
        return '{0}'.format(self.name)
