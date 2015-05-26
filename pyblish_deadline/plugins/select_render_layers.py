import os

import pyblish.api

import pymel.core as pm
import pymel.versions as pv


@pyblish.api.log
class SelectRenderlayers(pyblish.api.Selector):
    """ Gathers all renderlayers
    """

    hosts = ['maya']
    version = (0, 1, 0)
    name = 'Select Renderlayers'

    def process_context(self, context):

        # storing current layer
        current_layer = pm.nodetypes.RenderLayer.currentLayer()

        # getting output path
        render_globals = pm.PyNode('defaultRenderGlobals')
        start_frame = render_globals.startFrame.get()

        paths = [str(pm.system.Workspace.getPath().expand())]
        paths.append(str(pm.system.Workspace.fileRules['images']))
        output_path = os.path.join(*paths)
        tmp = pm.rendering.renderSettings(firstImageName=True)[0]
        paths.append(str(tmp))

        path = os.path.join(*paths)

        padding = render_globals.extensionPadding.get()
        firstFrame = int(render_globals.startFrame.get())
        stringFrame = str(firstFrame).zfill(padding)
        if stringFrame in path:
            tmp = '#' * padding
            path = path.replace(stringFrame, tmp)

        layer = pm.nodetypes.RenderLayer.currentLayer()
        if layer.name() == 'defaultRenderLayer':
            layer_name = 'masterLayer'
        else:
            layer_name = layer.name()

        path = path.replace(layer_name, '{render_layer}')

        # getting job data
        job_data = {}
        if context.has_data('deadlineJobData'):
            job_data = context.data('deadlineJobData').copy()

        # storing plugin data
        plugin_data = {'UsingRenderLayers': 1}

        tmp = str(pm.system.Workspace.getPath().expand())
        plugin_data['ProjectPath'] = tmp

        plugin_data['Version'] = pv.flavor()
        plugin_data['Build'] = pv.bitness()

        drg = pm.PyNode('defaultRenderGlobals')
        plugin_data['Renderer'] = drg.currentRenderer.get()

        # arnold specifics
        if drg.currentRenderer.get() == 'arnold':
            plugin_data['Animation'] = 1

        #creating instances
        for layer in pm.ls(type='renderLayer'):
            if layer.renderable.get():

                layer.setCurrent()

                instance = context.create_instance(name=layer.name())
                instance.set_data('family', value='deadline.render')

                # getting layer name
                if layer.name() == 'defaultRenderLayer':
                    layer_name = 'masterLayer'
                else:
                    layer_name = layer.name()

                # setting plugin_data
                plugin_data = plugin_data.copy()
                plugin_data['RenderLayer'] = layer_name

                instance.set_data('deadlinePluginData', value=plugin_data)

                # setting job data
                start_frame = int(render_globals.startFrame.get())
                end_frame = int(render_globals.endFrame.get())
                frames = '%s-%s' % (start_frame, end_frame)
                instance.set_data('deadlineFrames', value=frames)

                output_file = os.path.basename(path)
                job_data['OutputFilename0'] = output_file

                context.set_data('deadlineJobData', value=job_data)

                # setting output
                output = os.path.dirname(path.format(render_layer=layer_name))
                instance.set_data('deadlineOutput', value=output)

        # restoring current layer
        current_layer.setCurrent()
