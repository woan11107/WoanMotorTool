#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电机调试工具 - CANable / SLCAN ASCII 版本
适用于 MKS CANable、candleLight 等标准 SLCAN ASCII 协议设备
"""

import motor_tool

motor_tool.SLCAN_TYPE = "canable"

if __name__ == "__main__":
    motor_tool.main()
