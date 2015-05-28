import getpass

import pyblish.api


@pyblish.api.log
class ExtractDeadlineFtrack(pyblish.api.Extractor):
    """ Gathers Ftrack related data for Deadline
    """

    families = ['deadline.render']
    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):

        # getting job data
        job_data = {}
        if context.has_data('deadlineJobData'):
            job_data = context.data('deadlineJobData').copy()

        # getting data
        username = getpass.getuser()

        ftrack_data = context.data('ftrackData')

        project_name = ftrack_data['project']['code']
        project_id = ftrack_data['project']['id']

        task_name = ftrack_data['task']['name']
        task_id = ftrack_data['task']['id']

        asset_name = context.data('ftrackData')['asset']['name']
        asset_id = context.data('ftrackData')['asset']['id']

        version_number = ftrack_data['version']['number']

        # setting extra info
        extra_info = []
        if 'ExtraInfo' in job_data:
            extra_info = job_data['ExtraInfo']

        extra_info.extend([task_name, project_name, asset_name,
                          version_number,username])

        job_data['ExtraInfo'] = extra_info

        # setting extra info key values
        extra_info_key_value = {}
        if 'ExtraInfoKeyValue' in job_data:
            extra_info_key_value = job_data['ExtraInfoKeyValue']

        extra_info_key_value['FT_TaskName'] = task_name
        extra_info_key_value['FT_Description'] = 'Pyblish'
        extra_info_key_value['FT_VersionId'] = ''
        extra_info_key_value['FT_ProjectId'] = project_id
        extra_info_key_value['FT_AssetName'] = asset_name
        extra_info_key_value['FT_AssetId'] = asset_id
        extra_info_key_value['FT_TaskId'] = task_id
        extra_info_key_value['FT_ProjectName'] = project_name
        extra_info_key_value['FT_Username'] = username

        job_data['ExtraInfoKeyValue'] = extra_info_key_value

        context.set_data('deadlineJobData', value=job_data)
