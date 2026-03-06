# MockUI firmware manifest (hardware — STM32F469 Discovery)
include('../f469-disco/manifests/disco.py')
include('mockui-shared.py')
# platform.py and config_default.py needed for SDRAM init
freeze('../src', ('platform.py', 'config_default.py'))
# boot.py and main.py entry points
freeze('../scenarios/mockui_fw')
