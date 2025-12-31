#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial # 替换 can 为 serial
import threading
import signal
import sys
import time
import enum
import math
import struct
import numpy as np # 引入numpy处理字节数组更方便，或者直接用list/bytearray
from slcan_protocol import *

class MotorType(enum.Enum):
    A4310 = 0
    A4340 = 1

class MotorMode(enum.Enum):
    POSITION = 0
    VELOCITY = 1
    TORQUE = 2
    MIT = 3

class Gripper:
    def __init__(self, gripper_id):
        self.gripper_id = gripper_id
        self.pos = 0.0
        self.vel = 0.0
        self.force = 0.0
        self.status = 0
        self.err = 0

    def get_position(self):
        return self.pos
    
    def get_velocity(self):
        return self.vel

    def get_force(self):
        return self.force

    def get_error(self):
        return self.err

    def get_status(self):
        return self.status
    
    def parse_msg(self, data : bytearray):
        # 确保传入的是8字节payload
        if len(data) < 5: return
        self.err = data[0]
        self.status = data[1]
        self.pos = data[2]
        self.vel = data[3]
        self.force = data[4]

class Motor:
    def __init__(self, motor_id, master_id, motor_type=MotorType.A4310):
        self.motor_id = motor_id
        self.master_id = master_id
        self.enabled = False
        self.mode = MotorMode.MIT
        self.pos = 0.0
        self.vel = 0.0
        self.tau = 0.0
        self.temp_mos = 0
        self.temp_motor = 0
        self.status = 0
        self.motor_type = motor_type
        self.goal_position = 0.0
        self.goal_tau = 0.0
        self.params = {}
        if motor_type == MotorType.A4310:
            self.pos_max = 12.5
            self.vel_max = 50.0
            self.tau_max = 10.0
        elif motor_type == MotorType.A4340:
            self.pos_max = 12.5
            self.vel_max = 10.0
            self.tau_max = 28.0
        else:
            raise ValueError("Unsupported motor type")

    def get_position(self):
        return self.pos
    
    def get_velocity(self):
        return self.vel

    def get_torque(self):
        return self.tau

    def get_temperature_mos(self):
        return self.temp_mos

    def get_temperature_motor(self):
        return self.temp_motor

    def get_status(self):
        return self.status

    def uint_to_float(self, x_int : int, x_min : int, x_max : int, bits : int) -> float:
        span = x_max - x_min
        offset = x_min
        return float(x_int * span / ((1<<bits)-1) + offset)

    def float_to_uint(self, x_float : float, x_min : int, x_max : int, bits : int) -> int:
        span = x_max - x_min
        offset = x_min
        # 增加限幅防止溢出
        if x_float > x_max: x_float = x_max
        if x_float < x_min: x_float = x_min
        return int((x_float-offset)* ((1<<bits)-1) / span)
    
    def __is_in_range(self, number) -> bool:
        if (7 <= number <= 10) or (13 <= number <= 16) or (35 <= number <= 36):
            return True
        return False

    def parse_msg(self, data : bytearray):
        # 此时传入的 data 应该是纯净的 8字节 CAN Payload
        if len(data) < 8: return

        if data[1] == 0x00 and (data[2] == 0x55 or data[2] == 0x33):
            # 参数读取返回
            rid = data[3]
            if self.__is_in_range(rid):
                value = struct.unpack('<I', data[4:8])[0]
            else:
                value = struct.unpack('<f', data[4:8])[0]
            self.params[rid] = value
                
        else:
            # 状态反馈 (MIT模式或其他控制模式反馈)
            self.status = (data[0] >> 4) & 0x0F
            self.temp_mos = data[6]
            self.temp_motor = data[7]
            pos = data[1] << 8 | data[2]
            vel = data[3] << 4 | (data[4] >> 4)
            tau = ((data[4] & 0x0F) << 8) | data[5]
            self.pos = self.uint_to_float(pos, -self.pos_max, self.pos_max, 16)
            self.vel = self.uint_to_float(vel, -self.vel_max, self.vel_max, 12)
            self.tau = self.uint_to_float(tau, -self.tau_max, self.tau_max, 12)

class MotorController:
    def __init__(self,
                 port: str = "/dev/ttyACM0",
                 baudrate: int = 921600,
                 slcan_type: str = "damiao"):
        """
        :param port: 串口设备
        :param baudrate: 串口波特率
        :param slcan_type: 'canable' | 'damiao'
        """

        # --------------------------------------------------
        # 1. 打开串口（与协议无关）
        # --------------------------------------------------
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=0.01,
            write_timeout=0.01
        )

        # --------------------------------------------------
        # 2. 创建 SLCAN 协议对象（关键）
        # --------------------------------------------------
        if slcan_type == "canable":
            self.slcan = CanableSlcan(self.serial)

        elif slcan_type == "damiao":
            self.slcan = DamiaoSlcan(self.serial)

        else:
            raise ValueError(f"Unknown slcan_type: {slcan_type}")

        # --------------------------------------------------
        # 3. 初始化 CAN 设备
        # --------------------------------------------------
        self.slcan.init()

        # --------------------------------------------------
        # 4. 初始化业务状态（你原来就有的）
        # --------------------------------------------------
        self.motors = {}
        self.running = True

        # --------------------------------------------------
        # 5. 启动接收线程（线程逻辑不变）
        # --------------------------------------------------
        self.recv_thread = threading.Thread(
            target=self.__recv_thread,
            daemon=True
        )
        self.recv_thread.start()

    def add_motor(self, motor):
        if motor.motor_id not in self.motors:
            self.motors[motor.motor_id] = motor

    def add_gripper(self, gripper):
        if gripper.gripper_id not in self.motors:
            self.motors[gripper.gripper_id] = gripper

    def __recv_thread(self):
        """
        接收线程（协议无关）
        """
    # print("DEBUG: Receive thread started (Unified Mode).")

        while self.running:
            try:
                # ---------------------------------------------
                # 1. 从协议层接收一帧
                # ---------------------------------------------
                ret = self.slcan.recv()

                if ret is None:
                    # 没有完整帧，稍微让出 CPU
                    time.sleep(0.001)
                    continue

                can_id, payload = ret

                # ---------------------------------------------
                # 2. 业务层路由逻辑（完全保留）
                # ---------------------------------------------

                # 2.1 直接按 CAN ID 匹配
                if can_id in self.motors:
                    self.motors[can_id].parse_msg(payload)
                    continue

                # 2.2 尝试从 payload 中提取 slave id
                if payload:
                    possible_id = payload[0] & 0x0F
                    if possible_id in self.motors:
                        self.motors[possible_id].parse_msg(payload)
                        continue

                # 2.3 未匹配（可选调试）
                # print(f"[RX] Unhandled frame: CAN_ID={can_id}, DATA={payload.hex()}")

            except Exception as e:
                print(f"[RX] Serial receive error: {e}")
                time.sleep(0.05)

    def __send_message(self, frame_id: int, data: bytes) -> bool:
        """
        发送 CAN 帧（协议无关）
        """
        try:
            return self.slcan.send(frame_id, data)
        except Exception as e:
            print(f"[TX] Send error: {e}")
            return False


    def close(self):
        self.running = False
        if self.recv_thread.is_alive():
            self.recv_thread.join()
        if self.serial.is_open:
            self.serial.close()
        
    def __read_param(self, canid, rid) -> bool:
        data = [ 
            canid & 0xFF,
            (canid >> 8) & 0xFF, 
            0x33, rid, 0x00, 0x00, 0x00, 0x00
        ]
        return self.__send_message(0x7FF, data)

    def __is_in_range(self, number) -> bool:
        if (7 <= number <= 10) or (13 <= number <= 16) or (35 <= number <= 36):
            return True
        return False

    def __write_param(self, canid, param_id, value) -> bool:
        if not self.__is_in_range(param_id):
            value = struct.pack('<f', value)
        else:
            value = struct.pack('<I', value)
            
        data = [canid & 0xFF, (canid >> 8) & 0xFF, 0x55, param_id] + list(value)
        
        return self.__send_message(0x7FF, data)

    def __send_command(self, frame_id, cmd):
        data=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, cmd]
        return self.__send_message(frame_id, data)

    def enable_motor(self, motor) -> bool:
        motor.enabled = True
        return self.__send_command(motor.motor_id, 0xFC) 

    def disable_motor(self, motor) -> bool:
        motor.enabled = False
        return self.__send_command(motor.motor_id, 0xFD)
    
    def set_zero_position(self, motor) -> bool:
        return self.__send_command(motor.motor_id, 0xFE)

    # 增加了超时重试逻辑
    def set_control_mode(self, motor, mode) -> bool:
        param_id = 10
        if mode == MotorMode.POSITION: value = 2
        elif mode == MotorMode.VELOCITY: value = 3
        elif mode == MotorMode.TORQUE: value = 4
        elif mode == MotorMode.MIT: value = 1
        else: return False
    
        motor.params.pop(param_id, None)
        self.__write_param(motor.motor_id, param_id, value)
    
        for i in range(50):
            if param_id not in motor.params:
                # 偶尔触发一次读取，防止写入后的自动回传丢包
                if i % 10 == 0: self.__read_param(motor.motor_id, param_id)
                time.sleep(0.02)
                continue
            if motor.params[param_id] == value:
                motor.mode = mode
                motor.params.pop(param_id, None)
                return True
        return False
    
    def control_gripper(self, gripper, pos, vel=0xFF, force=0xFF, acc=0xFF, dcc=0xFF) -> bool:
        data=[0x00, pos, vel, force, acc, dcc, 0x00, 0x00]
        return self.__send_message(gripper.gripper_id, data)

    def mit_ctrl(self, motor, kp, kd, pos, vel, tau) -> bool:
        if motor.motor_id not in self.motors: return False
        
        frame_id = motor.motor_id
        pos_int = motor.float_to_uint(pos, -motor.pos_max, motor.pos_max, 16)
        vel_int = motor.float_to_uint(vel, -motor.vel_max, motor.vel_max, 12)
        tau_int = motor.float_to_uint(tau, -motor.tau_max, motor.tau_max, 12)
        kp_int = motor.float_to_uint(kp, 0.0, 500.0, 12)
        kd_int = motor.float_to_uint(kd, 0.0, 5.0, 12)
        
        data = [
            (pos_int >> 8) & 0xFF, pos_int & 0xFF,
            (vel_int >> 4) & 0xFF, ((vel_int & 0x0F) << 4) | ((kp_int >> 8) & 0x0F),
            kp_int & 0xFF, (kd_int >> 4) & 0xFF, 
            ((kd_int & 0x0F) << 4) | ((tau_int >> 8) & 0x0F),
            tau_int & 0xFF
        ]
        return self.__send_message(frame_id, data)

    def pos_ctrl(self, motor, pos, vel) -> bool:
        if motor.motor_id not in self.motors: return False
        frame_id = motor.motor_id + 0x100
        pos_bytes = struct.pack('<f', pos)
        vel_bytes = struct.pack('<f', vel)
        data = list(pos_bytes + vel_bytes)
        return self.__send_message(frame_id, data)

    def vel_ctrl(self, motor, vel) -> bool:
        if motor.motor_id not in self.motors: return False
        frame_id = motor.motor_id + 0x200
        vel_bytes = struct.pack('<f', vel)
        data = list(vel_bytes)
        return self.__send_message(frame_id, data)

    def clear_error(self, motor) -> bool:
        if motor.motor_id not in self.motors: return False
        return self.__send_command(motor.motor_id, 0xFB)

    def refresh_status(self, motor) -> bool:
        if motor.motor_id not in self.motors: return False
        frame_id = 0x7FF
        data = [ 
            motor.motor_id & 0xFF,
            (motor.motor_id >> 8) & 0xFF, 
            0xCC, 0x00, 0x00, 0x00, 0x00, 0x00
        ]
        return self.__send_message(frame_id, data)

    # 增加了超时重试逻辑
    def read_master_id(self, motor) -> int:
        param_id = 7
        motor.params.pop(param_id, None)
        if not self.__read_param(motor.motor_id, param_id): return -1

        for i in range(50):
            if param_id in motor.params:
                motor.master_id = motor.params[param_id]
                return motor.params[param_id]
            time.sleep(0.02)
        return -1

    def set_master_id(self, motor, master_id) -> bool:
        param_id = 7
        motor.params.pop(param_id, None)
        return self.__write_param(motor.motor_id, param_id, master_id)

    def set_canid(self, motor, canid) -> bool:
        param_id = 8
        motor.params.pop(param_id, None)
        return self.__write_param(motor.motor_id, param_id, canid)

    def save_motor_param(self, motor) -> bool:
        """
        保存所有电机参数到Flash（永久保存）
        Save all motor parameters to flash (permanent)
        :param motor: Motor object 电机对象
        :return: bool
        """
        can_id_l = motor.motor_id & 0xFF
        can_id_h = (motor.motor_id >> 8) & 0xFF
        data = [can_id_l, can_id_h, 0xAA, 0x01, 0x00, 0x00, 0x00, 0x00]
        
        # 保存前先禁用电机
        self.disable_motor(motor)
        time.sleep(0.1)
        
        return self.__send_message(0x7FF, data)

class ArmManager:
    def __init__(self, motors, gripper=None, serial_port='/dev/ttyACM0'):
        # 改为传入串口号
        self.control = MotorController(port=serial_port)
        self.motors = motors
        self.gripper = gripper
        for motor in motors:
            self.control.add_motor(motor)
            self.control.enable_motor(motor)
            time.sleep(0.01)
        if gripper:
            self.control.add_gripper(gripper)
        self.set_mode(0)  # Default to MIT control mode
            
    def set_mode(self, mode):
        self.control_mode = mode
        for motor in self.motors:
            if mode == 0:
                self.control.set_control_mode(motor, MotorMode.MIT)
            elif mode == 1:
                self.control.set_control_mode(motor, MotorMode.POSITION)
            elif mode == 2:
                self.control.set_control_mode(motor, MotorMode.VELOCITY)
            else:
                print(f"Unsupported control mode: {mode}")
                return False

    def disable(self):
        for motor in self.motors:
            self.control.disable_motor(motor)

    def shutdown(self):
        for motor in self.motors:
            self.control.mit_ctrl(motor, 0, 0, 0, 0, 0)
        self.control.close()

    def set_zero_position(self):
        for motor in self.motors:
            self.control.disable_motor(motor)
        time.sleep(1)
        for motor in self.motors:
            self.control.set_zero_position(motor)
        time.sleep(1)
        for motor in self.motors:
            self.control.enable_motor(motor)
        return 0
    
    def vel_ctrl(self, vels):
        if self.control_mode == 0:
            kp = 0.0
            kd = 1.0
            tau = 0.0
            for motor, vel in zip(self.motors, vels):
                self.control.mit_ctrl(motor, kp, kd, 0.0, vel, tau)
        elif self.control_mode == 2:
            for motor, vel in zip(self.motors, vels):
                self.control.vel_ctrl(motor, vel)
            
    def pos_ctrl(self, poss, vels=None):
        if self.control_mode == 0:
            if vels is None: return
            kp = 10.0
            kd = 1.0
            tau = 0.0
            for motor, pos, vel in zip(self.motors, poss, vels):
                self.control.mit_ctrl(motor, kp, kd, pos, vel, tau)
        elif self.control_mode == 1:
            vel = 5.0
            for motor, pos in zip(self.motors, poss):
                self.control.pos_ctrl(motor, pos, vel)

    def mit_ctrl(self, kps, kds, poss, vels, taus):
        for motor, kp, kd, pos, vel, tau in zip(self.motors, kps, kds, poss, vels, taus):
            self.control.mit_ctrl(motor, kp, kd, pos, vel, tau)

    def get_status_async(self):
        positions = [motor.get_position() for motor in self.motors]
        velocities = [motor.get_velocity() for motor in self.motors]
        torques = [motor.get_torque() for motor in self.motors]
        temperatures = [(motor.get_temperature_mos(), motor.get_temperature_motor()) for motor in self.motors]
        return (positions, velocities, torques, temperatures)

    def get_status_sync(self):
        for motor in self.motors:
            self.control.refresh_status(motor)
            time.sleep(0.005) # 串口发送间隔稍作延时
        time.sleep(0.01)
        return self.get_status_async()

    def control_gripper(self, pos, vel=0xFF, force=0xFF, acc=0xFF, dcc=0xFF):
        if self.gripper:
            return self.control.control_gripper(self.gripper, pos, vel, force, acc, dcc)
        else:
            return False

if __name__ == "__main__":
    # Example usage
    # 实例化时传入指定串口
    damiao = MotorController(port='/dev/ttyACM1')
    motor1 = Motor(motor_id=1, master_id=0)
    damiao.add_motor(motor1)
    
    time.sleep(1)
    print("Enabling motor...")
    damiao.enable_motor(motor1)
    
    time.sleep(1)
    damiao.refresh_status(motor1)
    time.sleep(0.1)
    print(f"Motor {motor1.motor_id} status: Pos={motor1.get_position():.2f}")
    
    if damiao.set_control_mode(motor1, MotorMode.VELOCITY):
        print(f"Motor {motor1.motor_id} set to VELOCITY mode.")
    
    time.sleep(1)
    print("Running velocity control...")
    damiao.vel_ctrl(motor1, 5.0)
    
    for i in range(20):
        damiao.refresh_status(motor1)
        time.sleep(0.1)
        print(f"Motor {motor1.motor_id} | Pos: {motor1.get_position():.2f} | Vel: {motor1.get_velocity():.2f}")
    
    print("Stopping...")
    damiao.disable_motor(motor1)
    time.sleep(1)
    damiao.close()