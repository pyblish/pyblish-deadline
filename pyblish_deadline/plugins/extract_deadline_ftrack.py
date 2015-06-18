import getpass

import pyblish.api


@pyblish.api.log
class ExtractDeadlineFtrack(pyblish.api.Extractor):
    """ Gathers Ftrack related data for Deadline
    """
    order = pyblish.api.Extractor.order + 0.5
    families = ['deadline.render']
    hosts = ['*']
    version = (0, 1, 0)
    optional = True
    label = 'Extract Ftrack to Deadline'

    def process(self, instance):

        # getting job data
        job_data = {}
        if instance.has_data('deadlineJobData'):
            job_data = instance.data('deadlineJobData').copy()

        # getting data
        username = getpass.getuser()

        ftrack_data = instance.context.data('ftrackData')

        project_name = ftrack_data['Project']['code']
        project_id = ftrack_data['Project']['id']

        task_name = ftrack_data['Task']['name']
        task_id = ftrack_data['Task']['id']

        asset_name = ftrack_data['Asset']['name']
        asset_id = ftrack_data['Asset']['id']

        version_id = ftrack_data['AssetVersion']['id']
        version_used_id = ''

        if instance.has_data('ftrackVersionUsedID'):
            version_id = ''
            version_used_id = instance.data('ftrackVersionUsedID')

        version_number = instance.context.data('version')

        component_name = None
        if instance.has_data('ftrack_components'):
            component_name = instance.data('ftrack_components').keys()[0]

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
        extra_info_key_value['FT_Description'] = ''
        extra_info_key_value['FT_VersionId'] = version_id
        extra_info_key_value['FT_VersionUsedId'] = version_used_id
        extra_info_key_value['FT_ProjectId'] = project_id
        extra_info_key_value['FT_AssetName'] = asset_name
        extra_info_key_value['FT_AssetId'] = asset_id
        extra_info_key_value['FT_TaskId'] = task_id
        extra_info_key_value['FT_ProjectName'] = project_name
        extra_info_key_value['FT_Username'] = username
        extra_info_key_value['FT_VersionNumber'] = version_number
        extra_info_key_value['FT_ComponentName'] = component_name


        job_data['ExtraInfoKeyValue'] = extra_info_key_value

        instance.set_data('deadlineJobData', value=job_data)
