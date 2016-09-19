import sys
import os
import logging
import json

import Deadline.Scripting as ds


def __main__(*args):
    plugin_config = ds.RepositoryUtils.GetEventPluginConfig("Pyblish")

    # returning early if no plugins are configured
    if not plugin_config.GetConfigEntryWithDefault("OnPreTaskPaths", ""):
        return

    # adding python search paths
    paths = plugin_config.GetConfigEntryWithDefault("PythonSearchPaths",
                                                    "").strip()
    paths = paths.split(";")

    for path in paths:
        print "Extending sys.path with: " + str(path)
        sys.path.append(path)

    # clearing previous plugin paths,
    # and adding pyblish plugin search paths
    os.environ["PYBLISHPLUGINPATH"] = ""
    path = ""
    adding_paths = plugin_config.GetConfigEntryWithDefault("OnPreTaskPaths",
                                                           "").strip()

    if adding_paths != "":
        adding_paths.replace(";", os.pathsep)

        if path != "":
            path = path + os.pathsep + adding_paths
        else:
            path = adding_paths

        print "Setting PYBLISHPLUGINPATH to: \"%s\"" % path
        os.environ["PYBLISHPLUGINPATH"] = str(path)

    # setup logging
    level_item = plugin_config.GetConfigEntryWithDefault("LoggingLevel",
                                                         "DEBUG")
    level = logging.DEBUG

    if level_item == "INFO":
        level = logging.INFO
    if level_item == "WARNING":
        level = logging.WARNING
    if level_item == "ERROR":
        level = logging.ERROR

    logging.basicConfig(level=level)
    logger = logging.getLogger()

    # if pyblish is not available
    try:
        __import__("pyblish.api")
    except ImportError:
        import traceback
        print ("Could not load module \"pyblish.api\": %s"
               % traceback.format_exc())
        return

    # setup context and injecting deadline job and additional data
    import pyblish.api
    cxt = pyblish.api.Context()
    cxt.data["deadlineAdditionalData"] = {}

    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()
    cxt.data["deadlineJob"] = job

    task_id = deadlinePlugin.GetCurrentTaskId()
    task = None
    for t in ds.RepositoryUtils.GetJobTasks(job, False):
        if t.TaskId == task_id:
            task = t
    cxt.data["deadlineTask"] = task

    # recreate context from data
    data = job.GetJobExtraInfoKeyValueWithDefault("PyblishContextData", "")
    if data:
        data = json.loads(data)
        cxt.data.update(data)
    else:
        logger.warning("No Pyblish data found.")

    cxt.data["deadlineEvent"] = "OnPreTask"

    # setup username
    os.environ["LOGNAME"] = job.UserName

    # run publish
    import pyblish.util

    logging.getLogger("pyblish").setLevel(level)

    cxt = pyblish.util.publish(context=cxt)

    # error logging needs some work
    for result in cxt.data["results"]:
        if not result["success"]:
            logger.error(result)
            (file_path, line_no, func, line) = result["error"].traceback
            msg = "Error: \"{0}\"\n".format(result["error"])
            msg += "Filename: \"{0}\"\n".format(file_path)
            msg += "Line number: \"{0}\"\n".format(line_no)
            msg += "Function name: \"{0}\"\n".format(func)
            msg += "Line: \"{0}\"\n".format(line)
            logger.error(msg)
