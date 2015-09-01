import os
import pyblish.api
import re


import hou

@pyblish.api.log
class SelectDeadlineMantraNodes(pyblish.api.Selector):
    """Selects all write nodes"""

    hosts = ['houdini']
    version = (0, 1, 0)

    def process(self, context):

        # storing plugin data
        plugin_data = {}


        renderNode = hou.node( "/out" )
        render_nodes = renderNode.children()

        # creating instances per write node
        for node in list(render_nodes):
            if node.type().name() == 'ifd':

                instance = context.create_instance(name=node.name())
                instance.set_data('family', value='deadline.render')
                instance.set_data('outputPathExpanded', value=node.parm('vm_picture').eval())
                instance.set_data('outputPath', value=node.parm('vm_picture').unexpandedString())

                # instance.add(node)

                output = node.parm('vm_picture').eval()
                output_path = os.path.dirname(output)

                # setting job data
                job_data = {}
                if instance.has_data('deadlineJobData'):
                    job_data = instance.data('deadlineJobData').copy()

                # output_file = os.path.basename(output)
                #
                # if '$F' in output_file:
                #     padding = int(output_file.split('F')[1])
                #     padding_string = '$F{}'.format(padding)
                #     tmp = '#' * padding
                #     output_file = output_file.replace(padding_string, tmp)

                paddedNumberRegex = re.compile( "([0-9]+)", re.IGNORECASE )

                paddedOutputFile = ""

                # Check the output file
                # output = GetOutputPath( renderNode )
                output_file = output
                matches = paddedNumberRegex.findall( os.path.basename( output_file ) )
                if matches != None and len( matches ) > 0:
                    paddingString = matches[ len( matches ) - 1 ]
                    paddingSize = len( paddingString )
                    padding = "#"
                    while len(padding) < paddingSize:
                        padding = padding + "#"
                    paddedOutputFile = self.right_replace( output_file, paddingString, padding, 1 )

                job_data['OutputFilename0'] = paddedOutputFile
                job_data['Plugin'] = 'Houdini'

                instance.set_data('deadlineJobData', value=job_data)

                # frame range
                start_frame = int(node.parm('f1').eval())
                end_frame = int(node.parm('f2').eval())


                frames = '{}-{}\n'.format(start_frame, end_frame)
                instance.set_data('deadlineFrames', value=frames)

                # setting plugin data
                plugin_data = plugin_data.copy()
                # plugin_data['SceneFile'] = None
                # plugin_data['Output'] = None
                # plugin_data['IFD'] = None
                plugin_data['OutputDriver'] = node.path()
                plugin_data['Version'] = '14'
                plugin_data['IgnoreInputs'] = '0'
                # plugin_data['Build'] = None

                instance.set_data('deadlinePluginData', value=plugin_data)


                components = {node.name(): {}}
                instance.set_data('ftrackComponents', value=components)


    def right_replace(self, fullString, oldString, newString, occurences ):
        return newString.join(fullString.rsplit( oldString, occurences ) )
