#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import colorama
from interface import MotorController, Motor

# 初始化 colorama
colorama.init()

def set_zero_position(motor_id, port='/dev/ttyACM1', baudrate=921600):
    """
    设置单个电机的零点位置
    
    Args:
        motor_id: 电机ID
        port: 串口路径
        baudrate: 波特率
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    motor = Motor(motor_id=motor_id, master_id=0)

    try:
        controller = MotorController(port=port, baudrate=baudrate)
    except Exception as e:
        print(f"\033[91m[X] 无法打开串口 {port}\033[0m")
        return False
    
    controller.add_motor(motor)

    current_master_id = controller.read_master_id(motor)

    if current_master_id < 0:
        print(f"\033[91m[X] 无法读取电机 ID {motor_id} 的 Master ID\033[0m")
        controller.close()
        return False

    print(f"CAN ID: 0x{motor.motor_id:02x}, Master ID: 0x{current_master_id:02x}")

    controller.enable_motor(motor)
    time.sleep(0.5)
    controller.refresh_status(motor)
    time.sleep(0.1)
    print(f"当前位置: {motor.get_position():.3f} rad")
    
    controller.set_zero_position(motor)
    time.sleep(0.5)
    controller.disable_motor(motor)
    time.sleep(0.5)
    
    controller.refresh_status(motor)
    time.sleep(0.1)
    print(f"新位置: {motor.get_position():.3f} rad")
    
    controller.close()
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python set_zero.py <motor_id>")
        sys.exit(1)

    current_canid = int(sys.argv[1], 0)
    success = set_zero_position(current_canid)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


