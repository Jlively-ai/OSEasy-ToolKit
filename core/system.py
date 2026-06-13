# -*- coding: utf-8 -*-
"""
系统操作模块
封装 Windows 系统命令操作，支持详细日志输出
"""

import os
import sys
import ctypes
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Optional, Callable

from .utils import Color


class SystemManager:
    """系统管理器 - 支持日志回调"""
    
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        self.oepath: Optional[Path] = None
        self._find_oepath()
        self._log_callback = log_callback
    
    def set_log_callback(self, callback: Optional[Callable[[str, str], None]]):
        self._log_callback = callback
    
    def _log(self, message: str, level: str = "info"):
        if self._log_callback:
            self._log_callback(message, level)
    
    def _find_oepath(self) -> None:
        possible_paths = [
            Path("C:/Program Files (x86)/Os-Easy/os-easy multicast teaching system"),
            Path("C:/Program Files/Os-Easy/os-easy multicast teaching system"),
        ]
        for path in possible_paths:
            if path.exists():
                self.oepath = path
                break
    
    @staticmethod
    def is_admin() -> bool:
        if sys.platform != "win32":
            return True
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    @staticmethod
    def run_as_admin():
        if sys.platform != "win32":
            return
        Color.print("[!] 检测到未以管理员身份运行", Color.RED)
        print()
        Color.print("[*] 正在自动请求管理员权限...", Color.YELLOW)
        time.sleep(2)
        script = sys.argv[0]
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
        sys.exit(0)
    
    def run_command(self, cmd: List[str], capture: bool = True, description: str = "") -> Tuple[int, str]:
        cmd_str = " ".join(cmd)
        if description:
            self._log(f"[执行] {description}", "cmd")
        self._log(f"[命令] {cmd_str}", "cmd")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", shell=False)
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines[:20]:
                    self._log(f"[输出] {line}", "output")
                if len(lines) > 20:
                    self._log(f"[输出] ... ({len(lines)-20} 行省略)", "output")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[:10]:
                    self._log(f"[错误] {line}", "error")
            self._log(f"[返回] 代码 {result.returncode}", "info" if result.returncode == 0 else "warning")
            return result.returncode, result.stdout
        except Exception as e:
            self._log(f"[异常] {str(e)}", "error")
            return -1, str(e)
    
    @staticmethod
    def clear_screen():
        os.system("cls" if sys.platform == "win32" else "clear")
    
    def stop_service(self, service_name: str) -> bool:
        self._log(f"停止服务: {service_name}", "action")
        code, _ = self.run_command(["sc", "stop", service_name], description=f"停止服务 {service_name}")
        ok = code == 0
        self._log(f"服务 {service_name} 停止{'成功' if ok else '失败 (可能已停止或不存在)'}", "success" if ok else "warning")
        return ok
    
    def start_service(self, service_name: str) -> bool:
        self._log(f"启动服务: {service_name}", "action")
        code, _ = self.run_command(["sc", "start", service_name], description=f"启动服务 {service_name}")
        ok = code == 0
        self._log(f"服务 {service_name} 启动{'成功' if ok else '失败'}", "success" if ok else "error")
        return ok
    
    def delete_service(self, service_name: str) -> bool:
        self._log(f"删除服务: {service_name}", "action")
        code, _ = self.run_command(["sc", "delete", service_name], description=f"删除服务 {service_name}")
        ok = code == 0
        self._log(f"服务 {service_name} 删除{'成功' if ok else '失败 (可能不存在)'}", "success" if ok else "warning")
        return ok
    
    def get_service_status(self, service_name: str) -> str:
        code, output = self.run_command(["sc", "query", service_name], description=f"查询服务 {service_name} 状态")
        if code != 0:
            return "不存在"
        if "RUNNING" in output:
            return "运行中"
        elif "STOPPED" in output:
            return "已停止"
        return "未知"
    
    def kill_process(self, process_name: str) -> bool:
        self._log(f"终止进程: {process_name}", "action")
        code, output = self.run_command(["taskkill", "/f", "/im", process_name], description=f"强制终止进程 {process_name}")
        ok = code == 0
        if ok:
            self._log(f"进程 {process_name} 已终止", "success")
        else:
            self._log(f"进程 {process_name} {'未运行' if '找不到' in output or 'not found' in output.lower() else '终止失败'}", "info" if '找不到' in output else "warning")
        return ok
    
    def get_process_status(self, process_name: str) -> str:
        code, output = self.run_command(["tasklist", "/FI", f"IMAGENAME eq {process_name}"], description=f"查询进程 {process_name} 状态")
        return "运行中" if process_name.lower() in output.lower() else "未运行"
    
    def delete_file(self, file_path: Path) -> bool:
        self._log(f"删除文件: {file_path}", "action")
        try:
            if file_path.exists():
                file_path.unlink()
                self._log(f"文件已删除", "success")
                return True
            self._log(f"文件不存在", "info")
            return False
        except Exception as e:
            self._log(f"删除失败: {e}", "error")
            return False
    
    def rename_file(self, src: Path, dst: Path) -> bool:
        self._log(f"重命名: {src.name} -> {dst.name}", "action")
        try:
            if src.exists():
                src.rename(dst)
                self._log(f"重命名成功", "success")
                return True
            self._log(f"源文件不存在", "warning")
            return False
        except Exception as e:
            self._log(f"重命名失败: {e}", "error")
            return False
    
    def run_powershell(self, script: str, description: str = "执行 PowerShell 脚本") -> Tuple[int, str]:
        self._log(description, "action")
        temp_script = Path(os.environ.get("TEMP", "/tmp")) / "temp_script.ps1"
        try:
            temp_script.write_text(script, encoding="utf-8")
            self._log(f"[脚本] 已写入临时文件", "cmd")
            return self.run_command(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(temp_script)], description=description)
        finally:
            temp_script.unlink(missing_ok=True)
            self._log(f"[清理] 删除临时脚本", "info")