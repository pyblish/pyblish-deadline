# pyblish-deadline

## Setup
The repository path needs to be in the ```PYTHONPATH``` environment variable.

Test with ```import pyblish_deadline```

**Remote Submission**

Deadline has the ability to submit job from remote locations. To use this feature, you need to enable the web service; http://docs.thinkboxsoftware.com/products/deadline/7.1/1_User%20Manual/manual/web-service.html

To setup pyblish-deadline for remote submission, you need to create a ```config.json``` file next to ```check_port.py```. The ```config.json``` needs to have the following structure:
```
{"address":"URL","port":"PORT NUMBER","username":"USERNAME","password":"PASSWORD"}
```
The parameters look something like this:
```
URL = http://43.2.33.415
PORT NUMBER = 8080
USERNAME = myusername
PASSWORD = mypassword
```

Run ```check_port.py``` to check that everything is setup correctly.

## Usage
To use this extension you need to collect and inject data into the instance you want to publish.

The data member you need to create is ```deadlineData```. ```deadlineData``` is a dictionary containing three items; ```job```, ```plugin``` and ```order```. ```job``` and ```plugin``` has dictionaries as values. ```order``` is an integer.

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
OutputDirectory0=L:\ethel_and_ernest_0001\renders\img_sequences\q000c010\compositing\v002\Write1
OutputFilename0=q000c010.compositing.v002.####.exr
```

Some of this data is filled in by Deadline and the extension when submitting, so here is what was submitted with the extension;

```python
job = {'Frames': '1-375','Plugin': 'Nuke',
'OutputFilename0': 'L:\ethel_and_ernest_0001\renders\img_sequences\q000c010\compositing\v002\Write1\q000c010.compositing.v002.####.exr'}
```

This shows the bare minimum of data required for a Nuke job. This extension fills in the "Name" and "UserName" parameters. Deadline splits the file path from the "OutputFilename0" parameter into "OutputFilename0" and "OutputDirectory0"

**plugin**

This contains all relevant data for the Deadline plugin.

You can obtain the required data if you submit a job to Deadline, and inspect the job properties. An example of this could be;
```
NukeX=False
WriteNode=Write1
Version=9.0
EnforceRenderOrder=True
SceneFile=L:\ethel_and_ernest_0001\sequences\q000\q000c010\compositing\publish\q000c010.compositing.v002.nk
```

All this data has been filled in by collecting data from the scene and application;

```python
plugin = {'NukeX': False, 'WriteNode': 'Write1', 'Version': '9.0', 'EnforceRenderOrder': True, 'SceneFile': 'L:\ethel_and_ernest_0001\sequences\q000\q000c010\compositing\publish\q000c010.compositing.v002.nk'}
```

**order**

This is an optional value to set. This determines dependencies between jobs. Being a simple integer value, you can set which order the jobs get submitted to the Deadline.

In a publish with instances that has orders like; ```Write1.order = 1``` and ```Write2.order = 2```, ```Write2``` will be dependent on ```Write1``` as ```Write1``` has a lower order value.

This works for multiple dependencies as well. So in the case of; ```Write1.order = 1```, ```Write2.order = 1``` and ```Write3.order = 2```, ```Write3``` will be dependent on ```Write1``` and ```Write2```.

**Event Plugins**

To utilize the event plugins in Deadline, you will need to append additional data to the ```job``` data. You can find various examples in ```pyblish_deadline/examples```.
