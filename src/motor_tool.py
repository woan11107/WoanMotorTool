#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
电机调试工具 - 整合版
功能包括：扫描电机、设置ID、设置零点等
"""

import sys
import os
import json
import platform
from pathlib import Path
import serial
import serial.tools.list_ports
import colorama

# 初始化 colorama
colorama.init()

# 导入功能模块
from scan_motors import scan_motors
from set_id import set_motor_id
from set_zero import set_zero_position
from set_zero_all import set_zero_all_motors

# 配置文件路径
CONFIG_FILE = "motor_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "port": "/dev/ttyACM0",
    "baudrate": 921600,
    "max_scan_id": 16
}


def check_port_connection(port, baudrate=921600):
    """检测串口是否可以连接"""
    try:
        # 尝试打开串口
        ser = serial.Serial(port, baudrate, timeout=0.5)
        ser.close()
        return True, "已连接"
    except serial.SerialException as e:
        if "Permission denied" in str(e):
            return False, "权限不足 (需要sudo或将用户添加到dialout组)"
        elif "No such file" in str(e) or "could not open port" in str(e):
            return False, "端口不存在"
        else:
            return False, f"连接失败: {str(e)}"
    except Exception as e:
        return False, f"未知错误: {str(e)}"


def get_available_ports():
    """获取所有可用的串口列表"""
    ports = serial.tools.list_ports.comports()
    return [(port.device, port.description) for port in ports]


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # print(f"已加载配置: {CONFIG_FILE}")
                return config
        except Exception as e:
            print(f"\033[93m警告: 配置文件加载失败 ({e})，使用默认配置\033[0m")
    
    # 根据操作系统调整默认端口
    if platform.system() == "Windows":
        DEFAULT_CONFIG["port"] = "COM3"
    
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        # print(f"配置已保存到: {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"\033[91m错误: 配置文件保存失败 ({e})\033[0m")
        return False


def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("           电机调试工具 v1.0")
    print("="*60)
    print("1. 查看/修改串口配置")
    print("2. 扫描电机")
    # print("3. 读取电机ID和Master ID")
    print("3. 设置电机ID和Master ID")
    print("4. 设置单个电机零点")
    print("5. 设置全部已连接电机零点")
    print("0. 退出")
    print("="*60)


def scan_menu(config):
    """扫描电机菜单"""
    # print("\n--- 扫描电机 ---")
    # print(f"\n使用串口: {config['port']}")
    motors = scan_motors(port=config['port'], baudrate=config['baudrate'], max_id=config['max_scan_id'])
    
    if motors is None:
        pass  # 错误信息已在 scan_motors 中显示
    elif motors:
        print(f"\n找到 {len(motors)} 个电机")
        print("\n电机列表:")
        print("  Motor ID | Master ID |  当前位置   | 状态")
        print(" " + "-" * 50)
        for motor_id, motor_info in sorted(motors.items()):
            master_id = motor_info['master_id']
            position = motor_info['position']
            status = "正常" if master_id >= 0 else "Master ID读取失败"
            print(f"   0x{motor_id:02x}    |  0x{master_id:02x}     | {position:7.3f} rad | {status}")
    else:
        print("\n\033[93m未检测到任何电机\033[0m")
    
    input("\n按Enter键继续...")


def read_id_menu(config):
    """读取电机ID菜单"""
    print("\n--- 读取电机ID和Master ID ---")
    motor_id_str = input("请输入电机ID (1~9): ").strip()
    
    if not motor_id_str:
        print("已取消")
        return
    
    try:
        motor_id = int(motor_id_str, 0)
    except ValueError:
        print("\033[91m[X] ID格式无效\033[0m")
        return
    
    # print(f"\n使用串口: {config['port']}")
    set_motor_id(motor_id, None, None, port=config['port'], baudrate=config['baudrate'])
    
    input("\n按Enter键继续...")


def set_id_menu(config):
    """设置电机ID菜单"""
    print("\n--- 设置电机ID和Master ID ---")
    print("当前电机ID:")
    current_id_str = input("  请输入当前电机ID (1~9): ").strip()
    
    if not current_id_str:
        print("已取消")
        return
    
    try:
        current_id = int(current_id_str, 0)
    except ValueError:
        print("\033[91m[X] ID格式无效\033[0m")
        return
    
    print("\n新的电机配置:")
    new_motor_id_str = input("  请输入新的电机ID (十进制或0x十六进制): ").strip()
    
    if not new_motor_id_str:
        print("已取消")
        return
    
    try:
        new_motor_id = int(new_motor_id_str, 0)
        # 自动计算 Master ID: 十六进制下高位加1
        new_master_id = 0x10 + new_motor_id
    except ValueError:
        print("\033[91m[X] ID格式无效\033[0m")
        return
    
    print(f"\n将设置: Motor ID = 0x{new_motor_id:02x}, Master ID = 0x{new_master_id:02x}")
    confirm = input(f"\n确认设置 - 当前ID: 0x{current_id:02x} -> 新ID: 0x{new_motor_id:02x}, 新Master ID: 0x{new_master_id:02x}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    # print(f"\n使用串口: {config['port']}")
    success = set_motor_id(current_id, new_motor_id, new_master_id, 
                          port=config['port'], baudrate=config['baudrate'])
    
    if success:
        print("\n\033[92m[OK] 设置成功！参数已永久保存到电机Flash\033[0m")
    else:
        print("\n[X] 设置失败")
    
    input("\n按Enter键继续...")


def set_zero_menu(config):
    """设置单个电机零点菜单"""
    print("\n--- 设置单个电机零点 ---")
    motor_id_str = input("请输入电机ID (1~9): ").strip()
    
    if not motor_id_str:
        print("已取消")
        return
    
    try:
        motor_id = int(motor_id_str, 0)
    except ValueError:
        print("\033[91m[X] ID格式无效\033[0m")
        return
    
    # print(f"\n使用串口: {config['port']}")
    success = set_zero_position(motor_id, port=config['port'], baudrate=config['baudrate'])
    
    if success:
        print("\n\033[92m[OK] 零点设置成功！\033[0m")
    else:
        print("\n\033[91m[X] 零点设置失败\033[0m")
    
    input("\n按Enter键继续...")


def set_zero_all_menu(config):
    """设置全部已连接电机零点菜单"""
    print("\n--- 设置全部已连接电机零点 ---")
    # print("正在扫描已连接的电机...")
    
    # 扫描所有已连接的电机
    motors = scan_motors(port=config['port'], baudrate=config['baudrate'], max_id=config['max_scan_id'])
    
    if motors is None:
        print("\n\033[91m[X] 串口连接错误\033[0m")
        input("\n按Enter键继续...")
        return
    
    if not motors:
        print("\n\033[93m未检测到任何电机\033[0m")
        input("\n按Enter键继续...")
        return
    
    motor_ids = sorted(motors.keys())
    print(f"\n检测到 {len(motor_ids)} 个电机: {motor_ids}")
    
    confirm = input(f"\n确定要将电机 {motor_ids} 设置零点? (y/Enter确认, n取消): ").strip().lower()
    if confirm and confirm != 'y':
        print("已取消")
        input("\n按Enter键继续...")
        return
    
    # print(f"\n使用串口: {config['port']}")
    success = set_zero_all_motors(motor_ids, port=config['port'], baudrate=config['baudrate'])
    
    if success:
        print("\n\033[92m[OK] 所有电机零点设置成功！\033[0m")
    else:
        print("\n\033[91m[X] 零点设置失败\033[0m")
    
    input("\n按Enter键继续...")


def config_menu(config, show_return=True):
    """配置菜单"""
    while True:
        print("\n--- 串口配置 ---")
        
        # 检测当前串口连接状态
        is_connected, status_msg = check_port_connection(config['port'], config['baudrate'])
        status_symbol = "[OK]" if is_connected else "[X]"
        status_color = "\033[92m" if is_connected else "\033[91m"  # 绿色或红色
        reset_color = "\033[0m"
        
        # 如果初始不允许返回，但现在已连接，则允许返回
        if not show_return and is_connected:
            show_return = True
        
        print(f"串口状态: {status_color}{status_symbol} {status_msg}{reset_color}")
        print(f"\n当前配置:")
        print(f"  1. 串口端口: {config['port']}")
        print(f"  2. 列出所有可用串口")
        print(f"  3. 重新检测串口连接")
        print(f"  4. 重置为默认配置")
        if show_return:
            print(f"  0. 返回主菜单")
        
        choice = input("\n请选择要修改的项 (0-4): " if show_return else "\n请选择要修改的项 (1-4): ").strip()
        
        if choice == '0':
            if show_return:
                break
            else:
                # 检查是否已连接，只有连接后才允许退出
                is_connected, _ = check_port_connection(config['port'], config['baudrate'])
                if is_connected:
                    break
                else:
                    print("\n\033[93m提示: 请先配置一个有效的串口\033[0m")
        elif choice == '1':
            new_port = input(f"请输入新的串口端口 (当前: {config['port']}): ").strip()
            if new_port:
                # Windows端口自动转换为大写
                if platform.system() == "Windows" and new_port.lower().startswith("com"):
                    new_port = new_port.upper()
                
                # 验证新串口
                is_valid, msg = check_port_connection(new_port, config['baudrate'])
                if is_valid:
                    config['port'] = new_port
                    save_config(config)
                    print(f"\033[92m[OK] 串口设置成功: {new_port}，自动返回主菜单\033[0m")
                    break
                else:
                    confirm = input(f"\033[93m警告: {msg}\n仍要设置此串口? (y/n): \033[0m").strip().lower()
                    if confirm == 'y':
                        config['port'] = new_port
                        save_config(config)
        elif choice == '2':
            available_ports = get_available_ports()
            if available_ports:
                # 只显示可以连接的串口
                connected_ports = []
                print("\n可用串口列表:")
                for device, description in available_ports:
                    is_conn, status = check_port_connection(device, config['baudrate'])
                    if is_conn:
                        connected_ports.append((device, description))
                        print(f"  \033[92m{len(connected_ports)}. {device} - {description}\033[0m")
                
                if connected_ports:
                    select = input("\n输入序号选择串口 (直接回车跳过): ").strip()
                    if select and select.isdigit():
                        idx = int(select) - 1
                        if 0 <= idx < len(connected_ports):
                            config['port'] = connected_ports[idx][0]
                            save_config(config)
                            print(f"\033[92m[OK] 已连接串口: {config['port']}，自动返回主菜单...\033[0m")
                            break
                else:
                    print("\033[91m[X] 未检测到已连接的串口\033[0m")
            else:
                print("\033[93m未检测到可用的串口\033[0m")
        elif choice == '3':
            print("\n正在检测串口连接...")
            is_connected, status_msg = check_port_connection(config['port'], config['baudrate'])
            if is_connected:
                print(f"\033[92m[OK] 串口 {config['port']} 连接正常\033[0m")
            else:
                print(f"[X] 串口 {config['port']} 连接失败: {status_msg}")
            input("\n按Enter键继续...")
        elif choice == '4':
            confirm = input("确认重置为默认配置? (y/n): ").strip().lower()
            if confirm == 'y':
                config.update(DEFAULT_CONFIG)
                # 根据操作系统调整默认端口
                if platform.system() == "Windows":
                    config["port"] = "COM3"
                save_config(config)
                print("已重置为默认配置")


def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    # 显示系统信息
    # print(f"操作系统: {platform.system()}")
    # print(f"默认串口: {config['port']}")
    
    # 检查启动时串口连接状态
    is_connected, status_msg = check_port_connection(config['port'], config['baudrate'])
    if not is_connected:
        # print(f"\n警告: 串口未连接 - {status_msg}")
        # print("进入串口配置菜单...\n")
        config_menu(config, show_return=False)
    
    # 主循环
    while True:
        show_menu()
        choice = input("\n请选择功能 (0-6): ").strip()
        
        if choice == '0':
            # print("\n感谢使用，再见！")
            break
        elif choice == '1':
            config_menu(config)
        elif choice == '2':
            scan_menu(config)
        # elif choice == '3':
        #     read_id_menu(config)
        elif choice == '3':
            set_id_menu(config)
        elif choice == '4':
            set_zero_menu(config)
        elif choice == '5':
            set_zero_all_menu(config)
        else:
            print("\033[91m[X] 无效的选择，请重新输入\033[0m")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
