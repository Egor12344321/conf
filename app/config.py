import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import socket
import argparse
import time

class ShellEmulator:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root
        username = os.getlogin()
        hostname = socket.gethostname()
        self.root.title(f"Эмулятор - [{username}@{hostname}]")
        
        self.vfs_path = vfs_path
        self.script_path = script_path
        
        print(f"Параметры запуска:")
        print(f"  VFS путь: {vfs_path if vfs_path else 'Не указан (используется по умолчанию)'}")
        print(f"  Скрипт: {script_path if script_path else 'Не указан (интерактивный режим)'}")
        print("-" * 50)
        
        self.output_area = scrolledtext.ScrolledText(root, state='disabled', height=30)
        self.output_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.prompt_label = tk.Label(root, text=f"[{username}@{hostname}]$ ", anchor='w')
        self.prompt_label.pack(fill=tk.X, padx=10)
        
        self.command_entry = tk.Entry(root)
        self.command_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.command_entry.bind('<Return>', self.process_command)
        
        self.print_output("Добро пожаловать в эмулятор командной оболочки!\nВведите 'exit' для выхода.\n")
        
        if script_path:
            self.root.after(1000, self.execute_script)
        
    def print_output(self, text):
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.configure(state='disabled')
        self.output_area.see(tk.END)
        
    def execute_script(self):
        if not os.path.exists(self.script_path):
            error_msg = f"Ошибка: файл скрипта '{self.script_path}' не найден!"
            self.print_output(error_msg + "\n")
            messagebox.showerror("Ошибка", error_msg)
            return
            
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            self.print_output(f"Выполнение скрипта: {self.script_path}\n")
            self.print_output("-" * 40 + "\n")
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                    
                username = os.getlogin()
                hostname = socket.gethostname()
                self.print_output(f"[{username}@{hostname}]$ {line}\n")
                
                self.execute_command(line)
                
                self.root.update()
                time.sleep(0.5)
                
            self.print_output("-" * 40 + "\n")
            self.print_output("Скрипт выполнен успешно!\n")
            
        except Exception as e:
            error_msg = f"Ошибка выполнения скрипта (строка {line_num}): {str(e)}"
            self.print_output(error_msg + "\n")
            messagebox.showerror("Ошибка скрипта", error_msg)
        
    def execute_command(self, command_text):
        parts = command_text.split()
        if not parts:
            return
            
        command_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if command_name == "exit":
            self.print_output("Завершение работы эмулятора...\n")
            self.root.after(1000, self.root.destroy)
            
        elif command_name == "ls":
            self.print_output(f"Команда 'ls' вызвана с аргументами: {args}\n")
            
        elif command_name == "cd":
            if args:
                self.print_output(f"Команда 'cd' пытается перейти в директорию: {args[0]}\n")
            else:
                self.print_output("Команда 'cd' требует аргумент - путь к директории\n")
                
        elif command_name == "echo":
            self.print_output(f"{' '.join(args)}\n")
            
        else:
            self.print_output(f"Ошибка: неизвестная команда '{command_name}'\n")
    
    def process_command(self, event):
        command_text = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)
        
        username = os.getlogin()
        hostname = socket.gethostname()
        self.print_output(f"[{username}@{hostname}]$ {command_text}\n")
        
        self.execute_command(command_text)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Эмулятор командной оболочки')
    parser.add_argument('--vfs', '-v', help='Путь к физическому расположению VFS')
    parser.add_argument('--script', '-s', help='Путь к стартовому скрипту')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    root = tk.Tk()
    app = ShellEmulator(root, vfs_path=args.vfs, script_path=args.script)
    root.mainloop()