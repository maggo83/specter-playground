# Unix simulator manifest
include('../f469-disco/manifests/unix.py')
include('mockui-shared.py')
freeze('../src')
# sim_control: TCP control server for sim_cli.py / MCP — simulator only.
# Frozen from parent dir so the package name 'sim_control' is preserved.
freeze('../scenarios', ('sim_control/__init__.py', 'sim_control/control_server.py', 'sim_control/widget_tree.py'))
