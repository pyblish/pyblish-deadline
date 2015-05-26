import os
import getpass
import re

import pyblish.api
import pyblish.plugin
import ftrack


@pyblish.api.log
class SelectDeadlineFtrack(pyblish.api.Selector):
    """ Gathers Ftrack related data for Deadline
    """

    families = ['deadline.render']
    hosts = ['nuke', 'maya']
    version = (0, 1, 0)

    def version_get(self, string, prefix, suffix = None):

      if string is None:
        raise ValueError, "Empty version string - no match"

      regex = "[/_.]"+prefix+"\d+"
      matches = re.findall(regex, string, re.IGNORECASE)
      if not len(matches):
        msg = "No \"_"+prefix+"#\" found in \""+string+"\""
        raise ValueError, msg
      return (matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group())

    def process_context(self, context):

        # getting job data
        job_data = {}
        if context.has_data('deadlineJobData'):
            job_data = context.data('deadlineJobData').copy()

        # getting data
        username = getpass.getuser()

        task_id = os.environ['FTRACK_TASKID']
        task = ftrack.Task(id=os.environ['FTRACK_TASKID'])

        task_name = task.getName()
        task_id = os.environ['FTRACK_TASKID']
        project_name = task.getProject().getName()
        project_id = task.getProject().getId()

        asset_name = None
        asset_id = None
        for asset in task.getAssets():
            if asset.getType().getShort() == 'comp':
                asset_name = asset.getName()
                asset_id = asset.getId()

        # setting extra info
        extra_info = []
        if 'ExtraInfo' in job_data:
            extra_info = job_data['ExtraInfo']

        # host specific current file gathering
        current_file = ''
        if pyblish.plugin.current_host() == 'maya':
            from maya import cmds
            current_file = cmds.file(sceneName=True, query=True)

            # Maya returns forward-slashes by default
            current_file = os.path.normpath(current_file)

        if pyblish.plugin.current_host() == 'nuke':
            import nuke
            current_file = nuke.root().name()

        current_file = context.data('currentFile')
        version_number = int(self.version_get(current_file, 'v')[1])

        extra_info.extend([task_name, project_name, asset_name,
                          version_number,username])

        job_data['ExtraInfo'] = extra_info

        # setting extra info key values
        extra_info_key_value = {}
        if 'ExtraInfoKeyValue' in job_data:
            extra_info_key_value = job_data['ExtraInfoKeyValue']

        extra_info_key_value['FT_TaskName'] = task_name
        extra_info_key_value['FT_Description'] = ''
        extra_info_key_value['FT_VersionId'] = ''
        extra_info_key_value['FT_ProjectId'] = project_id
        extra_info_key_value['FT_AssetName'] = asset_name
        extra_info_key_value['FT_AssetId'] = asset_id
        extra_info_key_value['FT_TaskId'] = task_id
        extra_info_key_value['FT_ProjectName'] = project_name
        extra_info_key_value['FT_Username'] = username

        job_data['ExtraInfoKeyValue'] = extra_info_key_value

        context.set_data('deadlineJobData', value=job_data)
