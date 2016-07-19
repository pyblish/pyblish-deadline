# pyblish-deadline

## Setup
The repository path needs to be in the ```PYTHONPATH``` environment variable.

Test with ```import pyblish_deadline```

## Usage
To use this extension you need to assign the ```deadline``` family and inject data into the instance you want to publish. This extension only works on instances.

The data member you need to create is ```deadlineData```. ```deadlineData``` is a dictionary containing four items; ```job```, ```plugin```, ```auxiliaryFiles``` and ```order```.

```job``` and ```plugin``` are dictionaries, ```auxiliaryFiles``` is a list and ```order``` is an integer.

```job``` dictionary can also optionally contain a ```ExtraInfoKeyValue``` dicationary and a ```ExtraInfo``` list. Please refer to the section ```job: ExtraInfo``` below, for further details.
```python
instance.data["deadlineData"] = {"job": {"ExtraInfo": list(),
                                         "ExtraInfoKeyValue": dict()},
                                 "plugin": dict(),
                                 "auxiliaryFiles": list(),
                                 "order": int()}
```
```job``` and ```plugin``` are required for submission, while ```auxiliaryFiles``` and ```order``` are optional.

**job**

This contains all the relevant data for the Deadline job.


You can obtain the required data if you submit a job to Deadline, and inspect the job properties. An example of this could be;

```
Name=q000c010.compositing.v002 - Write1
UserName=toke.jepsen
Frames=1-375
Blacklist=
ScheduledStartDateTime=30/07/2015 12:15
MachineName=061-KUVIRA-PC
Plugin=Nuke
OutputDirectory0=L:\
OutputFilename0=q000c010.compositing.v002.####.exr
```

```pyblish-deadline``` takes care of any formatting when submitting, so you just have to fill in the data. Here is the data generate for the above job submission:

```python
job_data = {"Name": "q000c010.compositing.v002 - Write1",
            "UserName": "toke.jepsen",
            "Plugin": "Nuke",
            "OutputFilename0": "L:\q000c010.compositing.v002.####.exr"}

instance.data["deadlineData"]["job"] = job_data
```

Notice how Deadline splits the file path from the ```OutputFilename0``` parameter into ```OutputFilename0``` and ```OutputDirectory0``` upon submission. Also that not all data in the job properties are required, as Deadline fills in certain data.

**job: ExtraInfo**

Sometimes it might be usefull to submit additional data with a render, for additional event plugin processing. Some built-in event plugins are; ```Ftrack```, ```Shotgun```, ```Draft``` etc.

You can obtain the required data if you submit a job to Deadline, and inspect the job properties. An example of this could be;

```
ExtraInfo0=fx
ExtraInfo1=testing
ExtraInfo3=1
ExtraInfo4=toke.jepsen
ExtraInfoKeyValue0=FT_ComponentName=None
ExtraInfoKeyValue1=FT_TaskName=fx
ExtraInfoKeyValue3=FT_VersionId=0689232e-49d9-11e6-bab7-42010af00048
```

You can easily populate this data by using the sub-dictionaries in the job data. The above data was submitted using this data;

```python
job_data = {"ExtraInfoKeyValue":{"FT_ComponentName": None,
                                 "FT_TaskName": "fx",
                                 "FT_VersionId": "0689232e-49d9-11e6-bab7-42010af00048"},
               "ExtraInfo": ["fx", "testing", 1, "toke.jepsen"]}

instance.data["deadlineData"]["plugin"] = job_data
```

*IMPORTANT: This is NOT required to utilize the Pyblish event plugin, refered to later.*

**plugin**

This contains all relevant data for the Deadline plugin.

You can obtain the required data if you submit a job to Deadline, and inspect the job properties. An example of this could be;
```
NukeX=False
WriteNode=Write1
Version=9.0
EnforceRenderOrder=True
SceneFile=L:\q000c010.compositing.v002.nk
```

All this data has been filled in by collecting data from the scene and application:

```python
plugin_data = {"NukeX": False,
               "WriteNode": "Write1",
               "Version": "9.0",
               "EnforceRenderOrder": True,
               "SceneFile": "L:\q000c010.compositing.v002.nk"}

instance.data["deadlineData"]["plugin"] = plugin_data
```

Notice that the dictionary's values do not have to be strings, as ```pyblish-deadline``` takes care of the formatting.

**order**

This is an optional value to set. This determines dependencies between jobs. Being a simple integer value, you can set which order the jobs get submitted to the Deadline.

```python
instance.data["deadlineData"]["order"] = 1
```

In a publish with instances that has orders like; ```Write1.order = 1``` and ```Write2.order = 2```, ```Write2``` will be dependent on ```Write1``` as ```Write1``` has a lower order value.

This works for multiple dependencies as well. So in the case of; ```Write1.order = 1```, ```Write2.order = 1``` and ```Write3.order = 2```, ```Write3``` will be dependent on ```Write1``` and ```Write2```.

**auxiliaryFiles**

You can optionally submit scene files with a job submission called auxiliary files. This is a list of file paths.

```python
instance.data["deadlineData"]["auxiliaryFiles"] = ["L:\q000c010.compositing.v002.nk"]
```

## Event Plugin

Using Pyblish to submit job to the farm, doesn't have to be the end. With the event plugin, you can continue your publishing in Deadline and keep your entire publishing pipeline within Pyblish.

The event plugin is design to be as flexible as Pyblish, so you can design or use any Pyblish plugin you wish. You can even use ```pyblish-deadline``` to submit jobs, and chain publishes together.

**Usage**

You have all the events in Deadline to trigger a publish from, and you can adjust all the settings in ```Tools``` > ```Configure Events...``` > ```Pyblish```.
Here you can also globally enabled the plugin.

Similar to how all Pyblish integrations work, you need to modify the ```PYTHONPATH``` environment variable to be able to import any python modules. You can easily modify this in the event plugin setting ```Additional Python Search Paths```.

The integration also follows Pyblish workflow, by setting the environment variable ```PYBLISHPLUGINPATH``` per event. You can have different plugins triggered depending on the event by pointing to different directories. You can input the directories in the; ```Job Plugins```, ```Respository Plugins```, ```Slave Plugins``` and ```Power Management Plugins``` section.

When a plugin is run, there are data available to utilize; ```context.data```, ```context.data["deadlineJob"]``` and ```context.data["deadlineAdditionalData"]```.

```context.data``` is inheriting data from the submission. If the job was submitted through ```pyblish-deadline```, the same ```context.data``` available.

```context.data["deadlineJob"]``` is the Deadline job object. From this object you can collect data about the job, by following the standard Deadline scripting reference; http://docs.thinkboxsoftware.com/products/deadline/8.0/2_Scripting%20Reference/class_deadline_1_1_jobs_1_1_job.html

```context.data["deadlineAdditionalData"]``` is additional data that might occur on different events. Currently this is only available on the ```OnJobError``` event, where you get the task and error report.

**Technical breakdown**

By default ```pyblish-deadline``` submission will inject the required data to continue publishing in Deadline. This consists of serializing the context and instance data, into ```PyblishContextData``` and ```PyblishInstanceData``` respectively. Upon serializing any objects get discarded, meaning no results/records are kept.

```PyblishContextData``` is used to recreate the context in Deadline, which is done before any plugins are run.

```PyblishInstanceData``` is available through the ```context.data["deadlineJob"]``` object, and can easily be deserialized with json.
```python
raw_data = job.GetJobExtraInfoKeyValue("PyblishInstanceData")
data = json.loads(raw_data)
```
