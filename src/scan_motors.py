#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import colorama
from interface import MotorController, Motor, MotorType

# 初始化 colorama 以支持 Windows 终端颜色
colorama.init()

def scan_motors(port='/dev/ttyACM1', baudrate=921600, max_id=16, slcan_type='canable'):
    """
    扫描指定范围内的所有电机ID，查询它们的master ID
    
    Args:
        port: 串口设备路径
        baudrate: 波特率
        max_id: 扫描的最大ID (默认16，可根据实际情况调整)
        slcan_type: SLCAN协议类型 ('canable' | 'damiao')
    
    Returns:
        dict: {motor_id: {'master_id': int, 'position': float}} 的字典，如果串口打开失败返回None
    """
    try:
        controller = MotorController(port=port, baudrate=baudrate, slcan_type=slcan_type)
    except Exception as e:
        print(f"\033[91m[X] 无法打开串口 {port}\033[0m")
        return None
    
    print(f"\n开始扫描电机，请等待...")
    
    found_motors = {}
    
    try:
        for motor_id in range(1, max_id + 1):
            # 创建临时电机对象
            temp_motor = Motor(motor_id=motor_id, master_id=0, motor_type=MotorType.A4310)
            controller.add_motor(temp_motor)
            
            # 尝试读取状态（检测电机是否存在）
            controller.refresh_status(temp_motor)
            time.sleep(0.05)  # 等待响应
            
            # 检查是否收到反馈（通过status或其他字段判断）
            # 如果电机存在，至少会有一些状态更新
            initial_pos = temp_motor.get_position()
            
            # 再次刷新确认
            controller.refresh_status(temp_motor)
            time.sleep(0.05)
            
            # 如果位置有效（不是初始值0.0）或者温度有更新，说明电机存在
            if (abs(temp_motor.get_position()) > 0.001 or 
                temp_motor.get_temperature_mos() > 0 or
                temp_motor.get_temperature_motor() > 0):
                
                # 读取 master ID
                # print(f"检测到电机 ID {motor_id}，正在读取 Master ID...")
                master_id = controller.read_master_id(temp_motor)
                
                if master_id >= 0:
                    found_motors[motor_id] = {
                        'master_id': master_id,
                        'position': temp_motor.get_position()
                    }
                else:
                    found_motors[motor_id] = {
                        'master_id': -1,
                        'position': temp_motor.get_position()
                    }
                    print(f"\033[91m[X] 电机 ID: {motor_id:2d} | Master ID: 读取失败\033[0m")
            
            # 从控制器中移除，避免累积
            controller.motors.pop(motor_id, None)
            
            # 显示进度
            # if motor_id % 4 == 0:
            #     print(f"  扫描进度: {motor_id}/{max_id}")
        
        # print("-" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断扫描")
    except Exception as e:
        print(f"\n扫描过程中出错: {e}")
    finally:
        controller.close()
        # print("\n扫描完成，已关闭连接")
    
    return found_motors


def main():
    """主函数"""
    # 可以根据实际情况修改参数
    port = '/dev/ttyACM1'  # 串口设备
    baudrate = 921600      # 波特率
    max_id = 16            # 扫描ID范围 (1-16)
    
    # 如果有命令行参数，可以覆盖默认值
    if len(sys.argv) > 1:
        port = sys.argv[1]
    if len(sys.argv) > 2:
        max_id = int(sys.argv[2])
    if len(sys.argv) > 3:
        baudrate = int(sys.argv[3])

    
    motors = scan_motors(port=port, max_id=max_id, baudrate=baudrate)
    
    # 保存结果到文件
    # if motors:
    #     output_file = 'motor_scan_result.txt'
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         f.write("达妙电机扫描结果\n")
    #         f.write(f"扫描时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    #         f.write(f"串口: {port}\n")
    #         f.write("-" * 40 + "\n")
    #         f.write("Motor ID | Master ID\n")
    #         f.write("-" * 40 + "\n")
    #         for motor_id, master_id in sorted(motors.items()):
    #             f.write(f" 0x{motor_id:2x}    |  0x{master_id:2x}\n")
        
    #     print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    main()