import os

import pyblish.api


@pyblish.api.log
class ValidateDeadlineOutputExistence(pyblish.api.Validator):
    """Validates that the output directory for the write nodes exists"""

    families = ['deadline.render']
    hosts = ['*']
    version = (0, 1, 0)

    def process(self, instance):
        path = instance.data('deadlineOutput')

        if not os.path.exists(path):
            msg = 'Output directory for %s doesn\'t exists: %s' % (instance,
                                                                   path)
            raise ValueError(msg)

    def repair_instance(self, instance):
        """Auto-repair creates the output directory"""
        path = instance.data('deadlineOutput')

        if not os.path.exists(path):
            os.makedirs(path)
