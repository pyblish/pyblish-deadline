import pyblish.api

import pymel


@pyblish.api.log
class ExtractDraft(pyblish.api.Extractor):
    """ Gathers host specific Draft related data for Deadline
    """

    families = ['deadline.render']
    hosts = ['maya']
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

        width = None
        height = None

        # TODO: get resolution dimensions

        extra_info_key_value['DraftFrameWidth'] = width
        extra_info_key_value['DraftFrameHeight'] = height

        job_data['ExtraInfoKeyValue'] = extra_info_key_value

        context.set_data('deadlineJobData', value=job_data)
