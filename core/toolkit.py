# -*- coding: utf-8 -*-
"""OsEasy-ToolKit 主工具类"""
import os, sys, time
from pathlib import Path
from typing import List, Callable
from .utils import Color, ServiceInfo, ProcessInfo, Config
from .system import SystemManager

class OsEasyToolKit:
    SERVICES = [ServiceInfo("MMPC","学生端根服务"),ServiceInfo("OeNetlimit","网络限制服务"),ServiceInfo("easyusbflt","USB管控服务")]
    PROCESSES = [
        ProcessInfo("Student.exe","学生端主程序"),ProcessInfo("MultiClient.exe","学生端主进程"),
        ProcessInfo("ScreenRender.exe","屏幕广播进程"),ProcessInfo("ScreenRender_Y.exe","屏幕广播辅助"),
        ProcessInfo("DeviceControl_x64.exe","设备控制进程"),ProcessInfo("BlackSlient.exe","黑屏安静进程"),
        ProcessInfo("OEProtect.exe","保护进程"),ProcessInfo("ProcessProtect.exe","进程保护"),
        ProcessInfo("RunClient.exe","运行客户端"),ProcessInfo("OELogSystem.exe","日志系统"),
        ProcessInfo("OEUpdate.exe","更新程序"),ProcessInfo("ServerOSS.exe","服务端OSS"),
        ProcessInfo("wfilesvr.exe","文件服务"),ProcessInfo("tvnserver.exe","TVN服务"),
        ProcessInfo("updatefilesvr.exe","更新文件服务"),
    ]
    def __init__(self, log_callback=None):
        self.config = Config()
        self.sys_mgr = SystemManager(log_callback=log_callback)
        self.running = True
    def unlock_network(self):
        self.sys_mgr.stop_service("MMPC")
        self.sys_mgr.stop_service("OeNetlimit")
        self.sys_mgr.kill_process("DeviceControl_x64.exe")
    def unlock_screen(self):
        self.sys_mgr.kill_process("ScreenRender.exe")
        self.sys_mgr.kill_process("ScreenRender_Y.exe")
        if self.sys_mgr.oepath:
            sr = self.sys_mgr.oepath / "ScreenRender.exe"
            if sr.exists():
                self.sys_mgr.rename_file(sr, sr.with_suffix(".exe.bak"))
    def unlock_keyboard(self):
        self.sys_mgr.kill_process("BlackSlient.exe")
        self.sys_mgr.kill_process("MultiClient.exe")
        if self.sys_mgr.oepath:
            for f in [self.sys_mgr.oepath/"LockKeyboard.dll", self.sys_mgr.oepath/"LoadDriver.exe", self.sys_mgr.oepath/"BlackSlient.exe", self.sys_mgr.oepath/"x86"/"LISSNetInfoSniffer.exe"]:
                self.sys_mgr.delete_file(f)
    def unlock_usb(self):
        self.sys_mgr.stop_service("easyusbflt")
        self.sys_mgr.delete_service("easyusbflt")
    def kill_all_processes(self):
        for proc in self.PROCESSES:
            self.sys_mgr.kill_process(proc.name)
    def unlock_all(self):
        self.unlock_network()
        self.unlock_screen()
        self.unlock_keyboard()
        self.unlock_usb()
        self.kill_all_processes()
    def suspend_student(self):
        code, out = self.sys_mgr.run_command(["tasklist","/FI","IMAGENAME eq Student.exe"], capture=True)
        if "Student.exe" not in out:
            return
        self.sys_mgr.run_powershell('$p=Get-Process Student -EA 0;if(!$p){exit 2}try{$null=$p[0].MainModule;$p|%{$_.Suspend()};exit 1}catch{$p|%{$_.Resume()};exit 0}')
    def run(self):
        if sys.platform=='win32' and not self.sys_mgr.is_admin():
            self.sys_mgr.run_as_admin()
        self.main_menu()
    def main_menu(self):
        while True:
            self.sys_mgr.clear_screen()
            self.print_header(f"OsEasy-ToolKit v{self.config.version}")
            Color.print(f"{'By ' + self.config.author:^50}", Color.CYAN)
            print("="*50); Color.print("       本工具用于解锁噢易学生端的各类限制", Color.YELLOW); print("="*50)
            Color.print("                      主菜单", Color.CYAN+Color.BOLD); print("="*50); print()
            items = [("1","一键解锁所有限制（推荐）","同时解锁网络、控屏、键鼠、USB"),("2","单独解锁网络限制","停止网络服务 + 终止网络相关进程"),("3","单独解锁控屏限制","终止屏幕广播进程 + 删除控屏程序"),("4","单独解锁键盘鼠标锁","删除键盘锁驱动 + 终止相关进程"),("5","单独解锁USB限制","删除USB管控服务 + 解锁USB设备"),("6","服务管理","选择并停止指定服务"),("7","进程管理","选择并终止指定进程"),("8","挂起/恢复学生端进程","暂停或恢复 Student.exe 运行"),("9","查看当前运行状态","显示学生端相关服务和进程"),("0","退出程序","")]
            for n,t,d in items:
                self.print_menu_item(n,t,d)
            print("="*50)
            c = input("请输入选项 (0-9): ").strip()
            acts = {"1":self.unlock_all,"2":lambda:self._quick_action("解锁网络限制",self.unlock_network),"3":lambda:self._quick_action("解锁控屏限制",self.unlock_screen),"4":lambda:self._quick_action("解锁键盘鼠标锁",self.unlock_keyboard),"5":lambda:self._quick_action("解锁USB限制",self.unlock_usb),"6":self.service_manager,"7":self.process_manager,"8":self.suspend_student,"9":self.show_status,"0":self.exit_program}
            acts.get(c, lambda: (Color.print("[错误] 无效选项！",Color.RED),time.sleep(2)))()
    def _quick_action(self,t,a):
        self.sys_mgr.clear_screen(); self.print_header(t); self.countdown(10); a(); input("\n按回车键返回...")
    def print_header(self,t):
        w=self.config.width; Color.print("="*w,Color.CYAN); Color.print(f"{t:^{w}}",Color.CYAN+Color.BOLD); Color.print("="*w,Color.CYAN); print()
    def print_menu_item(self,n,t,d=""):
        Color.print(f"  [{n}] {t}",Color.GREEN)
        if d: Color.print(f"      └─ {d}",Color.WHITE)
        print()
    def countdown(self,s,m="秒后自动执行，按任意键立即开始..."):
        Color.print(f"[*] {s}{m}",Color.YELLOW)
        for i in range(s,0,-1): print(f"\r[*] 倒计时: {i} 秒",end='',flush=True); time.sleep(1)
        print()
    def service_manager(self):
        while True:
            self.sys_mgr.clear_screen(); self.print_header("服务管理")
            print("请选择要操作的服务：\n")
            for i,svc in enumerate(self.SERVICES,1):
                st = self.sys_mgr.get_service_status(svc.name)
                Color.print(f"  [{i}] {svc.name:<15} - {svc.description} [{st}]",Color.GREEN)
            print(); Color.print("  [4] 停止所有服务",Color.GREEN); Color.print("  [5] 返回主菜单",Color.GREEN); Color.print("  [0] 退出程序",Color.GREEN); print()
            c = input("请输入选项 (0-5): ").strip()
            if c=="0": self.exit_program()
            elif c=="5": return
            elif c=="4":
                for svc in self.SERVICES: self.sys_mgr.stop_service(svc.name)
                Color.print("[√] 所有服务已停止",Color.GREEN); input("\n按回车键继续...")
            elif c in ["1","2","3"]: self._manage_single_service(self.SERVICES[int(c)-1].name)
            else: Color.print("[错误] 无效选项！",Color.RED); time.sleep(2)
    def _manage_single_service(self,n):
        ops = {"1":("停止",self.sys_mgr.stop_service),"2":("启动",self.sys_mgr.start_service),"3":("重启",lambda n:(self.sys_mgr.stop_service(n),time.sleep(1),self.sys_mgr.start_service(n))),"4":("删除",self.sys_mgr.delete_service)}
        while True:
            self.sys_mgr.clear_screen(); self.print_header(f"管理服务: {n}")
            print("  [1] 停止服务\n  [2] 启动服务\n  [3] 重启服务\n  [4] 删除服务\n  [5] 返回上级菜单\n")
            c = input("请选择操作 (1-5): ").strip()
            if c=="5": return
            if c in ops:
                nm,f=ops[c]; f(n)
                Color.print(f"[√] 服务已{nm}",Color.GREEN); input("\n按回车键继续...")
    def process_manager(self):
        while True:
            self.sys_mgr.clear_screen(); self.print_header("进程管理")
            print("请选择要操作的进程：\n")
            for i,p in enumerate(self.PROCESSES[:9],1):
                Color.print(f"  [{i}] {p.name:<25} - {p.description}",Color.GREEN)
            print(); Color.print("  [10] 终止所有学生端进程",Color.GREEN); Color.print("  [11] 持续监控模式（循环终止）",Color.GREEN); Color.print("  [12] 返回主菜单",Color.GREEN); Color.print("  [0]  退出程序",Color.GREEN); print()
            c = input("请输入选项 (0-12): ").strip()
            if c=="0": self.exit_program()
            elif c=="12": return
            elif c=="11": self._monitor_mode()
            elif c=="10": self.kill_all_processes(); input("\n按回车键继续...")
            elif c.isdigit() and 1<=int(c)<=9:
                p=self.PROCESSES[int(c)-1]
                if self.sys_mgr.kill_process(p.name): Color.print(f"[√] {p.name} 已终止",Color.GREEN)
                else: Color.print(f"[!] {p.name} 未运行或终止失败",Color.YELLOW)
                input("\n按回车键继续...")
    def _monitor_mode(self):
        self.sys_mgr.clear_screen(); self.print_header("持续监控模式")
        print("监控以下进程：")
        for p in ["Student.exe","MultiClient.exe","ScreenRender.exe","DeviceControl_x64.exe"]: print(f"- {p}")
        print(); input("按回车键开始监控...")
        self.running=True
        try:
            while self.running:
                self.sys_mgr.clear_screen()
                Color.print(f"[{time.strftime('%H:%M:%S')}] 正在监控进程状态...",Color.CYAN)
                for p in ["Student.exe","MultiClient.exe","ScreenRender.exe","DeviceControl_x64.exe"]: self.sys_mgr.kill_process(p)
                print("\n[*] 监控中... (按 Ctrl+C 停止)"); time.sleep(2)
        except KeyboardInterrupt:
            self.running=False; print("\n[!] 监控已停止"); input("按回车键返回...")
    def show_status(self):
        self.sys_mgr.clear_screen(); self.print_header("当前运行状态")
        Color.print("[服务状态]",Color.CYAN+Color.BOLD); print("-"*50)
        for svc in self.SERVICES:
            s=self.sys_mgr.get_service_status(svc.name)
            Color.print(f"[{'运行中'if s=='运行中'else '已停止'if s=='已停止'else '不存在'}] {svc.name}",Color.GREEN if s=='运行中'else Color.YELLOW if s=='已停止'else Color.RED)
        print(); Color.print("[进程状态]",Color.CYAN+Color.BOLD); print("-"*50)
        for p in self.PROCESSES[:9]:
            s=self.sys_mgr.get_process_status(p.name)
            Color.print(f"[{'运行中'if s=='运行中'else '未运行'}] {p.name}",Color.GREEN if s=='运行中'else Color.RED)
        print(); print("="*50); print("说明：[运行中] [已停止] [不存在] 表示服务状态"); print("      [运行中] [未运行] 表示进程状态"); print("="*50); print(); input("按回车键返回主菜单...")
    def exit_program(self):
        self.sys_mgr.clear_screen(); self.print_header("感谢使用 OsEasy-ToolKit"); print(); time.sleep(3); sys.exit(0)

def main():
    if sys.platform=='win32': os.system('chcp 65001 >nul 2>&1')
    try:
        OsEasyToolKit().run()
    except KeyboardInterrupt: print("\n\n[!] 程序被用户中断"); sys.exit(0)
    except Exception as e: Color.print(f"\n[!] 发生错误: {e}",Color.RED); input("按回车键退出..."); sys.exit(1)