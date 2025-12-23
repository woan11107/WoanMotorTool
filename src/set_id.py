#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import colorama
from interface import MotorController, Motor

# 初始化 colorama
colorama.init()

def set_motor_id(current_canid, new_motor_id=None, new_master_id=None, port='/dev/ttyACM1', baudrate=921600):
    """
    设置或读取电机ID和Master ID
    
    Args:
        current_canid: 当前电机ID
        new_motor_id: 新的电机ID (可选)
        new_master_id: 新的Master ID (可选)
        port: 串口路径
        baudrate: 波特率
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    motor = Motor(motor_id=current_canid, master_id=0)

    try:
        controller = MotorController(port=port, baudrate=baudrate)
    except Exception as e:
        print(f"\033[91m[X] 无法打开串口 {port}\033[0m")
        return False
    
    controller.add_motor(motor)

    # controller.disable_motor(motor)

    current_master_id = controller.read_master_id(motor)

    if current_master_id < 0:
        print(f"\033[91m[X] 无法读取电机 ID {current_canid} 的 Master ID\033[0m")
        controller.close()
        return False

    print(f"当前 CAN ID: 0x{motor.motor_id:02x}, Master ID: 0x{current_master_id:02x}")

    # 如果没有提供新ID，只是读取
    if new_motor_id is None:
        controller.close()
        return True
    
    # 如果没有提供 new_master_id，自动计算：十六进制下高位加1
    if new_master_id is None:
        new_master_id = 0x10 + new_motor_id
    
    print(f"设置新 CAN ID: 0x{new_motor_id:02x}, 新 Master ID: 0x{new_master_id:02x}")

    motor_new = Motor(motor_id=new_motor_id, master_id=new_master_id)
    if new_motor_id != current_canid:
        controller.add_motor(motor_new)

    controller.set_master_id(motor, new_master_id)
    controller.set_canid(motor, new_motor_id)

    # 保存参数到Flash（永久保存）
    time.sleep(0.1)
    print("正在保存参数到 Flash...")
    controller.save_motor_param(motor_new)
    time.sleep(0.5)  # 等待Flash写入完成

    current_master_id = controller.read_master_id(motor_new)
    print(f"新 CAN ID: 0x{motor_new.motor_id:02x}, 新 Master ID: 0x{current_master_id:02x}")
    
    controller.close()
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python set_id.py <motor_id> [<new_motor_id> <new_master_id>]")
        sys.exit(1)

    current_canid = int(sys.argv[1], 0)
    new_motor_id = None
    new_master_id = None
    
    if len(sys.argv) >= 4:
        new_motor_id = int(sys.argv[2], 0)
        new_master_id = int(sys.argv[3], 0)
    
    success = set_motor_id(current_canid, new_motor_id, new_master_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
    
