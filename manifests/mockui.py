# MockUI firmware manifest (hardware — STM32F469 Discovery)
include('../f469-disco/manifests/disco.py')
include('mockui-shared.py')
# platform.py + config_default.py: SDRAM init; rng.py: PIN keypad shuffle
freeze('../src', ('platform.py', 'config_default.py', 'rng.py'))
# boot.py and main.py entry points
freeze('../scenarios/mockui_fw')
