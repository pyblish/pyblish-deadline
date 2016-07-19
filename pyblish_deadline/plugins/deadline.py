import os
import subprocess
import tempfile
import traceback
import re
import uuid
import json

import pyblish.api


class IntegrateDeadline(pyblish.api.Integrator):

    label = "Deadline Submission"
    optional = True

    def process(self, context):

        instances = {}
        instances_order = []
        instances_no_order = []

        for instance in context:

            if not instance.data.get("publish", True):
                continue

            # skipping instance if not part of the family
            if "deadline" not in instance.data.get("families", []):
                msg = "No \"deadline\" family assigned. "
                msg += "Skipping \"%s\"." % instance
                self.log.info(msg)
                continue

            if "order" in instance.data("deadlineData"):
                order = instance.data("deadlineData")["order"]
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

            submission_id = uuid.uuid4()

            # getting job data
            job_data = instance.data("deadlineData")["job"]

            data = json.dumps(instance.data)
            if "ExtraInfoKeyValue" in job_data:
                job_data["ExtraInfoKeyValue"]["PyblishInstanceData"] = data
            else:
                job_data["ExtraInfoKeyValue"] = {"PyblishInstanceData": data}

            data = instance.context.data.copy()
            del data["results"]
            if "deadlineJob" in data:
                del data["deadlineJob"]
            data = json.dumps(data)
            job_data["ExtraInfoKeyValue"]["PyblishContextData"] = data

            # setting up dependencies
            if "order" in instance.data("deadlineData"):
                order = instance.data("deadlineData")["order"]
                if instances_order.index(order) != 0:
                    index = instances_order.index(order) - 1
                    dependencies = instances[instances_order[index]]
                    for count in range(0, len(dependencies)):
                        name = "JobDependency%s" % count
                        job_data[name] = dependencies[count].data("jobId")

            # writing job data
            data = ""

            if "ExtraInfo" in job_data:
                for v in job_data["ExtraInfo"]:
                    index = job_data["ExtraInfo"].index(v)
                    data += "ExtraInfo%s=%s\n" % (index, v)
                del job_data["ExtraInfo"]

            if "ExtraInfoKeyValue" in job_data:
                index = 0
                for entry in job_data["ExtraInfoKeyValue"]:
                    data += "ExtraInfoKeyValue%s=" % index
                    data += "%s=" % entry
                    data += "%s\n" % job_data["ExtraInfoKeyValue"][entry]
                    index += 1
                del job_data["ExtraInfoKeyValue"]

            for entry in job_data:
                data += "%s=%s\n" % (entry, job_data[entry])

            current_dir = tempfile.gettempdir()
            filename = str(submission_id) + ".job.txt"
            job_path = os.path.join(current_dir, filename)

            with open(job_path, "w") as outfile:
                outfile.write(data)

            self.log.info("job data:\n\n%s" % data)

            # writing plugin data
            plugin_data = instance.data("deadlineData")["plugin"]
            data = ""
            for entry in plugin_data:
                data += "%s=%s\n" % (entry, plugin_data[entry])

            current_dir = tempfile.gettempdir()
            filename = str(submission_id) + ".plugin.txt"
            plugin_path = os.path.join(current_dir, filename)

            with open(plugin_path, "w") as outfile:
                outfile.write(data)

            self.log.info("plugin data:\n\n%s" % data)

            # submitting job
            args = [job_path, plugin_path]

            if "auxiliaryFiles" in instance.data["deadlineData"]:
                aux_files = instance.data("deadlineData")["auxiliaryFiles"]
                if isinstance(aux_files, list):
                    args.extend(aux_files)
                else:
                    args.append(aux_files)

            # submitting
            try:
                result = self.CallDeadlineCommand(args)

                self.log.info(result)

                job_id = re.search(r"JobID=(.*)", result).groups()[0]
                instance.set_data("jobId", value=job_id)
            except:
                raise ValueError(traceback.format_exc())

            # deleting temporary files
            os.remove(job_path)
            os.remove(plugin_path)

    def CallDeadlineCommand(self, arguments, hideWindow=True):
        # On OSX, we look for the DEADLINE_PATH file. On other platforms,
        # we use the environment variable.
        if os.path.exists("/Users/Shared/Thinkbox/DEADLINE_PATH"):
            with open("/Users/Shared/Thinkbox/DEADLINE_PATH") as f:
                deadlineBin = f.read().strip()
                deadlineCommand = deadlineBin + "/deadlinecommand"
        else:
            deadlineBin = os.environ["DEADLINE_PATH"]
            if os.name == "nt":
                deadlineCommand = deadlineBin + "\\deadlinecommand.exe"
            else:
                deadlineCommand = deadlineBin + "/deadlinecommand"

        startupinfo = None
        if hideWindow and os.name == "nt" and hasattr(subprocess,
                                                      "STARTF_USESHOWWINDOW"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        environment = {}
        for key in os.environ.keys():
            environment[key] = str(os.environ[key])

        # Need to set the PATH, cuz windows seems to load DLLs from the PATH
        # earlier that cwd....
        if os.name == "nt":
            path = str(deadlineBin + os.pathsep + os.environ["PATH"])
            environment["PATH"] = path

        arguments.insert(0, deadlineCommand)

        # Specifying PIPE for all handles to
        # workaround a Python bug on Windows.
        # The unused handles are then closed immediatley afterwards.
        proc = subprocess.Popen(arguments, cwd=deadlineBin,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                startupinfo=startupinfo,
                                env=environment)
        proc.stdin.close()
        proc.stderr.close()

        output = proc.stdout.read()

        return output
