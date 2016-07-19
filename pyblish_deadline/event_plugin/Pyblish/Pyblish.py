import os
import sys
import logging
import json

import Deadline.Events
import Deadline.Scripting


def GetDeadlineEventListener():
    return PyblishEventListener()


def CleanupDeadlineEventListener(eventListener):
    eventListener.Cleanup()


class PyblishEventListener(Deadline.Events.DeadlineEventListener):

    def __init__(self):
        self.OnJobSubmittedCallback += self.OnJobSubmitted
        self.OnJobStartedCallback += self.OnJobStarted
        self.OnJobFinishedCallback += self.OnJobFinished
        self.OnJobRequeuedCallback += self.OnJobRequeued
        self.OnJobFailedCallback += self.OnJobFailed
        self.OnJobSuspendedCallback += self.OnJobSuspended
        self.OnJobResumedCallback += self.OnJobResumed
        self.OnJobPendedCallback += self.OnJobPended
        self.OnJobReleasedCallback += self.OnJobReleased
        self.OnJobDeletedCallback += self.OnJobDeleted
        self.OnJobErrorCallback += self.OnJobError
        self.OnJobPurgedCallback += self.OnJobPurged

        self.OnHouseCleaningCallback += self.OnHouseCleaning
        self.OnRepositoryRepairCallback += self.OnRepositoryRepair

        self.OnSlaveStartedCallback += self.OnSlaveStarted
        self.OnSlaveStoppedCallback += self.OnSlaveStopped
        self.OnSlaveIdleCallback += self.OnSlaveIdle
        self.OnSlaveRenderingCallback += self.OnSlaveRendering
        self.OnSlaveStartingJobCallback += self.OnSlaveStartingJob
        self.OnSlaveStalledCallback += self.OnSlaveStalled

        self.OnIdleShutdownCallback += self.OnIdleShutdown
        self.OnMachineStartupCallback += self.OnMachineStartup
        self.OnThermalShutdownCallback += self.OnThermalShutdown
        self.OnMachineRestartCallback += self.OnMachineRestart

    def Cleanup(self):
        del self.OnJobSubmittedCallback
        del self.OnJobStartedCallback
        del self.OnJobFinishedCallback
        del self.OnJobRequeuedCallback
        del self.OnJobFailedCallback
        del self.OnJobSuspendedCallback
        del self.OnJobResumedCallback
        del self.OnJobPendedCallback
        del self.OnJobReleasedCallback
        del self.OnJobDeletedCallback
        del self.OnJobErrorCallback
        del self.OnJobPurgedCallback

        del self.OnHouseCleaningCallback
        del self.OnRepositoryRepairCallback

        del self.OnSlaveStartedCallback
        del self.OnSlaveStoppedCallback
        del self.OnSlaveIdleCallback
        del self.OnSlaveRenderingCallback
        del self.OnSlaveStartingJobCallback
        del self.OnSlaveStalledCallback

        del self.OnIdleShutdownCallback
        del self.OnMachineStartupCallback
        del self.OnThermalShutdownCallback
        del self.OnMachineRestartCallback

    def run_pyblish(self, config_entry, job, additonalData={}):

        # returning early if data is not present
        if "PyblishContextData" not in job.GetJobExtraInfoKeys():
            return
        if "PyblishInstanceData" not in job.GetJobExtraInfoKeys():
            return

        # returning early if no plugins are configured
        if not self.GetConfigEntryWithDefault(config_entry, ""):
            return

        # adding python search paths
        paths = self.GetConfigEntryWithDefault("PythonSearchPaths", "").strip()
        paths = paths.split(";")

        # since this runs at all events, we don't want to keep filling sys.path
        for path in paths:
            if path not in sys.path:
                self.LogInfo("Extending sys.path with: " + str(path))
                sys.path.append(path)

        # clearing previous plugin paths,
        # and adding pyblish plugin search paths
        os.environ["PYBLISHPLUGINPATH"] = ""
        path = ""
        adding_paths = self.GetConfigEntryWithDefault(config_entry, "").strip()

        if adding_paths != "":
            adding_paths.replace(";", os.pathsep)

            if path != "":
                path = path + os.pathsep + adding_paths
            else:
                path = adding_paths

            self.LogInfo("Setting PYBLISHPLUGINPATH to: \"%s\"" % path)
            os.environ["PYBLISHPLUGINPATH"] = str(path)

        # setup logging
        level_item = self.GetConfigEntryWithDefault("LoggingLevel", "DEBUG")
        level = logging.DEBUG

        if level_item == "INFO":
            level = logging.INFO
        if level_item == "WARNING":
            level = logging.WARNING
        if level_item == "ERROR":
            level = logging.ERROR

        logging.basicConfig(level=level)
        logger = logging.getLogger()

        # setup username
        os.environ["LOGNAME"] = job.UserName

        # setup context and injecting deadline job and additional data
        import pyblish.api
        cxt = pyblish.api.Context()

        cxt.data["deadlineJob"] = job
        cxt.data["deadlineAdditionalData"] = additonalData

        # recreate context from data
        data = job.GetJobExtraInfoKeyValue("PyblishContextData")
        try:
            data = json.loads(data)
        except:
            logger.error("No Pyblish data found.")
            return
        cxt.data.update(data)

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

    def OnJobSubmitted(self, job):

        self.run_pyblish("OnJobSubmittedPaths", job)

    def OnJobStarted(self, job):

        self.run_pyblish("OnJobStartedPaths", job)

    def OnJobFinished(self, job):

        self.run_pyblish("OnJobFinishedPaths", job)

    def OnJobRequeued(self, job):

        self.run_pyblish("OnJobRequeuedPaths", job)

    def OnJobFailed(self, job):

        self.run_pyblish("OnJobFailedPaths", job)

    def OnJobSuspended(self, job):

        self.run_pyblish("OnJobSuspendedPaths", job)

    def OnJobResumed(self, job):

        self.run_pyblish("OnJobResumedPaths", job)

    def OnJobPended(self, job):

        self.run_pyblish("OnJobPendedPaths", job)

    def OnJobReleased(self, job):

        self.run_pyblish("OnJobReleasedPaths", job)

    def OnJobDeleted(self, job):

        self.run_pyblish("OnJobDeletedPaths", job)

    def OnJobError(self, job, task, report):

        data = {"task": task, "report": report}
        self.run_pyblish("OnJobErrorPaths", job, data)

    def OnJobPurged(self, job):

        self.run_pyblish("OnJobPurgedPaths", job)

    def OnHouseCleaning(self):

        self.run_pyblish("OnHouseCleaningPaths", None)

    def OnRepositoryRepair(self, job):

        self.run_pyblish("OnRepositoryRepairPaths", job)

    def OnSlaveStarted(self, job):

        self.run_pyblish("OnSlaveStartedPaths", job)

    def OnSlaveStopped(self, job):

        self.run_pyblish("OnSlaveStoppedPaths", job)

    def OnSlaveIdle(self, job):

        self.run_pyblish("OnSlaveIdlePaths", job)

    def OnSlaveRendering(self, job):

        self.run_pyblish("OnSlaveRenderingPaths", job)

    def OnSlaveStartingJob(self, job):

        self.run_pyblish("OnSlaveStartingJobPaths", job)

    def OnSlaveStalled(self, job):

        self.run_pyblish("OnSlaveStalledPaths", job)

    def OnIdleShutdown(self, job):

        self.run_pyblish("OnIdleShutdownPaths", job)

    def OnMachineStartup(self, job):

        self.run_pyblish("OnMachineStartupPaths", job)

    def OnThermalShutdown(self, job):

        self.run_pyblish("OnThermalShutdownPaths", job)

    def OnMachineRestart(self, job):

        self.run_pyblish("OnMachineRestartPaths", job)
