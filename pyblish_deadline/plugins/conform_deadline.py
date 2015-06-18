import os
import getpass
import subprocess

import pyblish.api


@pyblish.api.log
class ConformDeadline(pyblish.api.Conformer):

    families = ['deadline.render']
    hosts = ['*']
    label = 'Send to Deadline'

    def process(self, instance):

        job_data = instance.data('deadlineJobData')

        # getting input
        scene_file = instance.context.data('currentFile')

        if instance.context.has_data('deadlineInput'):
            scene_file = instance.context.data('deadlineInput')

        name = os.path.basename(scene_file)
        name = os.path.splitext(name)[0]
        name += ' - ' + str(instance)

        # getting job data

        job_data['Name'] = name

        job_data['UserName'] = getpass.getuser()

        job_data['Frames'] = instance.data('deadlineFrames')

        if pyblish.api.current_host() == 'maya':
            job_data['Plugin'] = 'MayaBatch'

        if pyblish.api.current_host() == 'nuke':
            job_data['Plugin'] = 'Nuke'

        # writing job data
        data = ''

        if 'ExtraInfo' in job_data:
            for v in job_data['ExtraInfo']:
                index = job_data['ExtraInfo'].index(v)
                data += 'ExtraInfo%s=%s\n' % (index, v)
            del job_data['ExtraInfo']

        if 'DraftTemplates' in job_data:
            for t in job_data['DraftTemplates']:
                index = job_data['DraftTemplates'].index(t)
                job_data['ExtraInfoKeyValue']['DraftTemplate%s' % index] = t
            del job_data['DraftTemplates']

        if 'ExtraInfoKeyValue' in job_data:
            index = 0
            for entry in job_data['ExtraInfoKeyValue']:
                data += 'ExtraInfoKeyValue%s=' % index
                data += '%s=' % entry
                data += '%s\n' % job_data['ExtraInfoKeyValue'][entry]
                index += 1
            del job_data['ExtraInfoKeyValue']

        for entry in job_data:
            data += '%s=%s\n' % (entry, job_data[entry])

        current_dir = instance.data('deadlineOutput')
        job_path = os.path.join(current_dir, job_data['Name'] + '.job.txt')

        with open(job_path, 'w') as outfile:
            outfile.write(data)

        # getting plugin data
        plugin_data = instance.data('deadlinePluginData')

        plugin_data['SceneFile'] = scene_file

        # writing plugin data
        data = ''
        for entry in plugin_data:
            data += '%s=%s\n' % (entry, plugin_data[entry])

        current_dir = instance.data('deadlineOutput')
        plugin_path = os.path.join(current_dir,
                                   job_data['Name'] + '.plugin.txt')

        with open(plugin_path, 'w') as outfile:
            outfile.write(data)

        # submitting job
        args = [job_path, plugin_path]

        self.log.info(self.CallDeadlineCommand(args))

    def CallDeadlineCommand(self, arguments, hideWindow=True):
        # On OSX, we look for the DEADLINE_PATH file. On other platforms, we use the environment variable.
        if os.path.exists("/Users/Shared/Thinkbox/DEADLINE_PATH"):
            with open("/Users/Shared/Thinkbox/DEADLINE_PATH") as f: deadlineBin = f.read().strip()
            deadlineCommand = deadlineBin + "/deadlinecommand"
        else:
            deadlineBin = os.environ['DEADLINE_PATH']
            if os.name == 'nt':
                deadlineCommand = deadlineBin + "\\deadlinecommand.exe"
            else:
                deadlineCommand = deadlineBin + "/deadlinecommand"

        startupinfo = None
        if hideWindow and os.name == 'nt' and hasattr(subprocess,
                                                      'STARTF_USESHOWWINDOW'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        environment = {}
        for key in os.environ.keys():
            environment[key] = str(os.environ[key])

        # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
        if os.name == 'nt':
            environment['PATH'] = str(deadlineBin + os.pathsep + os.environ['PATH'])

        arguments.insert(0, deadlineCommand)

        # Specifying PIPE for all handles to workaround a Python bug on Windows.
        # The unused handles are then closed immediatley afterwards.
        proc = subprocess.Popen(arguments, cwd=deadlineBin,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, startupinfo=startupinfo,
                                env=environment)
        proc.stdin.close()
        proc.stderr.close()

        output = proc.stdout.read()

        return output
