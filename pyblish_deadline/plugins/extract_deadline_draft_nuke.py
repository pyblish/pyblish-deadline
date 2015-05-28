import pyblish.api

import nuke


@pyblish.api.log
class ExtractDeadlineMayaDraftNuke(pyblish.api.Extractor):
    """ Gathers host specifics Draft related data for Deadline
    """

    families = ['deadline.render']
    hosts = ['nuke']
    version = (0, 1, 0)

    def process_context(self, context):

        # getting job data
        job_data = {}
        if context.has_data('deadlineJobData'):
            job_data = context.data('deadlineJobData').copy()

        # setting extra info key values
        extra_info_key_value = {}
        if 'ExtraInfoKeyValue' in job_data:
            extra_info_key_value = job_data['ExtraInfoKeyValue']

        height = nuke.root().format().height()
        width = nuke.root().format().width()

        extra_info_key_value['DraftFrameWidth'] = width
        extra_info_key_value['DraftFrameHeight'] = height

        job_data['ExtraInfoKeyValue'] = extra_info_key_value

        context.set_data('deadlineJobData', value=job_data)
