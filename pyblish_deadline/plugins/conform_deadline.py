import os
import getpass
import subprocess
import tempfile
import json
import inspect
import sys

import pyblish.api

# adding vendor
requests_path = os.path.dirname(inspect.getfile(inspect.currentframe()))
requests_path = os.path.dirname(os.path.dirname(requests_path))
requests_path = os.path.join(requests_path, 'vendor', 'requests')
sys.path.append(requests_path)

import requests


class IntegrateDeadline(pyblish.api.Integrator):

    label = 'Send to Deadline'

    def process(self, context, instance):

        # skipping instance if data is missing
        if not instance.has_data('deadlineData'):
            self.log.info('No deadlineData present. Skipping this instance')
            return

        job_data = instance.data('deadlineData')['job']

        # getting input
        scene_file = context.data('currentFile')

        if context.has_data('deadlineInput'):
            scene_file = context.data('deadlineInput')

        name = os.path.basename(scene_file)
        name = os.path.splitext(name)[0]
        name += ' - ' + str(instance)

        # getting job data

        job_data['Name'] = name

        job_data['UserName'] = getpass.getuser()

        if instance.has_data('deadlineFrames'):
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

        current_dir = tempfile.gettempdir()
        filename = job_data['Name'].replace(':', '_') + '.job.txt'
        job_path = os.path.join(current_dir, filename)

        with open(job_path, 'w') as outfile:
            outfile.write(data)

        self.log.info('job data:\n\n%s' % data)

        # getting plugin data
        plugin_data = instance.data('deadlineData')['plugin']

        plugin_data['SceneFile'] = scene_file

        # writing plugin data
        data = ''
        for entry in plugin_data:
            data += '%s=%s\n' % (entry, plugin_data[entry])

        current_dir = tempfile.gettempdir()
        filename = job_data['Name'].replace(':', '_') + '.plugin.txt'
        plugin_path = os.path.join(current_dir, filename)

        with open(plugin_path, 'w') as outfile:
            outfile.write(data)

        self.log.info('plugin data:\n\n%s' % data)

        # submitting job
        args = [job_path, plugin_path]

        try:
            self.log.info(self.CallDeadlineCommand(args))
        except:
            self.log.warning('No local Deadline found!')

            # deleting temporary files
            os.remove(job_path)
            os.remove(plugin_path)

        d = os.path.dirname
        config = d(d(d(inspect.getfile(inspect.currentframe()))))
        config = os.path.join(config, 'config.json')

        data = ''
        with open(config) as f:
            data = json.load(f)
            f.close()
        url = '%s:%s/api/jobs' % (data['address'], data['port'])

        payload = {'JobInfo': job_data, 'PluginInfo': plugin_data, 'AuxFiles': []}
        self.log.info(requests.post(url, auth=(data['username'], data['password']), data=json.dumps(payload)))

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
