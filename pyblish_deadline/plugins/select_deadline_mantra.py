import os
import pyblish.api


import hou

@pyblish.api.log
class SelectDeadlineMantraNodes(pyblish.api.Selector):
    """Selects all write nodes"""

    hosts = ['houdini']
    version = (0, 1, 0)

    def process_context(self, context):

        # storing plugin data
        plugin_data = {'EnforceRenderOrder': True}



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

                instance.set_data('deadlineOutput', value=output_path)

                # setting job data
                job_data = {}
                if context.has_data('deadlineJobData'):
                    job_data = context.data('deadlineJobData').copy()

                output_file = os.path.basename(output)

                if '$F' in output_file:
                    padding = int(output_file.split('F')[1])
                    padding_string = '$F{}'.format(padding)
                    tmp = '#' * padding
                    output_file = output_file.replace(padding_string, tmp)

                job_data['OutputFilename0'] = output_file
                job_data['Plugin'] = 'Houdini'

                instance.context.set_data('deadlineJobData', value=job_data)

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
                # plugin_data['Build'] = None

                instance.set_data('deadlinePluginData', value=plugin_data)
                instance.set_data('ftrackComponentName', value=node.name())
