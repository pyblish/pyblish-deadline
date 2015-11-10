import os
import getpass
import subprocess
import tempfile
import json
import inspect
import sys
import traceback
import re

import pyblish.api
from pyblish_deadline.vendor import requests


class PassthroughSubmission(pyblish.api.Integrator):

    label = 'Deadline Passthrough'
    DeadlineSubmission = True

    def process(self, instance):

        pass


class IntegrateDeadline(pyblish.api.Integrator):

    label = 'Deadline Submission'
    optional = True
    order = PassthroughSubmission.order + 0.1

    def process(self, context):

        instances = {}
        instances_order = []
        instances_no_order = []

        for item in context.data('results'):

            # skipping instances that aren't enabled
            try:
                item['plugin'].DeadlineSubmission
                instance = item['instance']
            except:
                continue

            # skipping instance if data is missing
            if not instance.has_data('deadlineData'):
                msg = 'No deadlineData present. Skipping "%s"' % instance
                self.log.info(msg)
                continue

            if 'order' in instance.data('deadlineData'):
                order = instance.data('deadlineData')['order']
                instances_order.append(order)
                if order in instances:
                    instances[order].append(instance)
                else:
                    instances[order] = [instance]
            else:
                instances_no_order.append(instance)

        instances_order = list(set(instances_order))
        instances_order.sort()

        new_context = []
        for order in instances_order:
            for instance in instances[order]:
                new_context.append(instance)

        if not instances_order:
            new_context = instances_no_order

        for instance in new_context:

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

            # setting up dependencies
            if 'order' in instance.data('deadlineData'):
                order = instance.data('deadlineData')['order']
                if instances_order.index(order) != 0:
                    dependencies = instances[instances_order[instances_order.index(order) - 1]]
                    for count in range(0, len(dependencies)):
                        job_data['JobDependency%s' % count] = dependencies[count].data('jobId')

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

            # submitting remotely
            success = True
            try:
                d = os.path.dirname
                config = d(d(d(inspect.getfile(inspect.currentframe()))))
                config = os.path.join(config, 'config.json')

                data = ''
                with open(config) as f:
                    data = json.load(f)
                    f.close()
                url = '%s:%s/api/jobs' % (data['address'], data['port'])

                payload = {'JobInfo': job_data, 'PluginInfo': plugin_data, 'AuxFiles': []}
                r = requests.post(url, auth=(data['username'], data['password']), data=json.dumps(payload))

                if r.status_code != 200:
                    success = False
            except:
                success = False
            finally:
                if success:
                    self.log.info('Successfully submitted to remote repository.')
                    return
                else:
                    self.log.info('Failed to submit to remote repository.')


             # submitting locally
            try:
                result = self.CallDeadlineCommand(args)

                self.log.info(result)

                job_id = re.search(r'JobID=(.*)', result).groups()[0]
                instance.set_data('jobId', value=job_id)
            except:
                raise ValueError(traceback.format_exc())

            # deleting temporary files
            os.remove(job_path)
            os.remove(plugin_path)

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
