#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电机调试工具 - 达妙（Damiao）二进制帧协议版本
适用于达妙电机直连串口或使用达妙私有协议的适配器
"""

import motor_tool

motor_tool.SLCAN_TYPE = "damiao"

if __name__ == "__main__":
    motor_tool.main()
