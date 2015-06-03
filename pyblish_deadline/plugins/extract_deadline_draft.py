import pyblish.api


@pyblish.api.log
class ExtractDeadlineDraft(pyblish.api.Extractor):
    """ Gathers Draft related data for Deadline
    """

    families = ['deadline.render']
    hosts = ['*']
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

        extra_info_key_value['DraftExtraArgs'] = ''
        extra_info_key_value['DraftVersion'] = ''
        extra_info_key_value['DraftUsername'] = ''
        extra_info_key_value['DraftUploadToShotgun'] = 'False'
        extra_info_key_value['DraftEntity'] = ''

        job_data['ExtraInfoKeyValue'] = extra_info_key_value

        context.set_data('deadlineJobData', value=job_data)
