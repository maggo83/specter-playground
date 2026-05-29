# Tetris firmware manifest (hardware — STM32F469 Discovery)
include('../f469-disco/manifests/disco.py')
freeze('../scenarios', ('tetris.py',))
freeze('../scenarios/tetris_hw')
