#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import colorama
from interface import MotorController, Motor

# 初始化 colorama
colorama.init()

def set_zero_all_motors(motor_ids, port='/dev/ttyACM1', baudrate=921600):
    """
    设置多个电机的零点位置
    
    Args:
        motor_ids: 电机ID列表
        port: 串口路径
        baudrate: 波特率
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        controller = MotorController(port=port, baudrate=baudrate)
    except Exception as e:
        print(f"\033[91m[X] 无法打开串口 {port}\033[0m")
        return False
    
    motors = []
    
    print("开始设置零点...")
    
    # 添加延迟以确保总线初始化完成
    time.sleep(1.0)
    
    # 1. 创建并添加所有电机
    for motor_id in motor_ids:
        motor = Motor(motor_id=motor_id, master_id=0)
        controller.add_motor(motor)
        motors.append(motor)
        time.sleep(0.1)
    
    # 2. 使能所有电机并读取当前位置
    print("等待零点设置...")
    current_positions = {}
    for motor in motors:
        controller.enable_motor(motor)
        time.sleep(0.1)
        controller.refresh_status(motor)
        time.sleep(0.05)
        current_positions[motor.motor_id] = motor.get_position()
    
    # 3. 设置零点
    for motor in motors:
        controller.set_zero_position(motor)
        time.sleep(0.2)
    
    # 4. 禁用电机
    for motor in motors:
        controller.disable_motor(motor)
        time.sleep(0.1)
    
    # 5. 验证新位置
    new_positions = {}
    for motor in motors:
        controller.refresh_status(motor)
        time.sleep(0.05)
        new_positions[motor.motor_id] = motor.get_position()
    
    # 6. 显示结果表格
    print("\n电机零点设置结果:")
    print("  Motor ID |   Old Position  |   New Position")
    print("  " + "-" * 45)
    for motor_id in motor_ids:
        current_pos = current_positions.get(motor_id, 0.0)
        new_pos = new_positions.get(motor_id, 0.0)
        print(f"    0x{motor_id:02x}   |  {current_pos:7.3f} rad    |  {new_pos:7.3f} rad")
    
    # print("\n零点设置成功！")
    
    controller.close()
    return True


def main():
    # 定义要设置零点的电机 ID 列表
    motor_ids = [1, 2, 3, 4, 5, 6, 7]
    
    # 如果有命令行参数，可以覆盖默认值
    if len(sys.argv) > 1:
        motor_ids = [int(x, 0) for x in sys.argv[1:]]
    
    print(f"将为以下电机设置零点: {motor_ids}")
    success = set_zero_all_motors(motor_ids)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()