# Unix simulator manifest
include('../f469-disco/manifests/unix.py')
include('mockui-shared.py')
freeze('../src')
# sim_control: TCP control server for sim_cli.py / MCP — simulator only
freeze('../scenarios/sim_control')
