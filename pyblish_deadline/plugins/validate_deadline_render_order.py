import os

import pyblish.api
import nuke


@pyblish.api.log
class ValidateDeadlineRenderOrder(pyblish.api.Validator):
    """Validates the write nodes render order"""

    families = ['deadline.render']
    hosts = ['nuke']
    version = (0, 1, 0)

    def upstream_nodes(self, node):
        results = []
        def climb(climb_node):
            results.append(climb_node)
            for n in climb_node.dependencies():
                climb(n)
        climb(node)
        return results

    def get_render_order(self, node):
        write_nodes = []
        for n in self.upstream_nodes(node):
            if n.Class() == 'Write':
                write_nodes.append(n)

        return len(write_nodes)

    def process_instance(self, instance):
        node = nuke.toNode(str(instance))

        if self.get_render_order(node) != node['render_order'].getValue():
            msg = '%s render order was incorrect.' % instance
            raise ValueError(msg)

    def repair_instance(self, instance):
        """Auto-repair correct render order"""
        node = nuke.toNode(str(instance))
        node['render_order'].setValue(self.get_render_order(node))
