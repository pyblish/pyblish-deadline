# pyblish-deadline

To use this extension you need to collect and inject data into the instance you want to publish.

The data member you need to create is "deadlineData". "deadlineData" is a dictionary containing two items; "job" and "plugin". Each of these has dictionaries as values.

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

**Event Plugins**

To utilize the event plugins in Deadline, you will need to append additional data to the ```job``` data. You can find various examples in ```pyblish_deadline/examples```.
