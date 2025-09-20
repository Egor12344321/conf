import tkinter as tk
from tkinter import scrolledtext
import os
import socket

class ShellEmulator:
    def __init__(self, root):
        self.root = root
        username = os.getlogin()
        hostname = socket.gethostname()
        self.root.title(f"Эмулятор - [{username}@{hostname}]")
        
        self.output_area = scrolledtext.ScrolledText(root, state='disabled', height=30)
        self.output_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.prompt_label = tk.Label(root, text=f"[{username}@{hostname}]$ ", anchor='w')
        self.prompt_label.pack(fill=tk.X, padx=10)
        
        self.command_entry = tk.Entry(root)
        self.command_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.command_entry.bind('<Return>', self.process_command)  
        
        self.print_output("Добро пожаловать в эмулятор командной оболочки!\nВведите 'exit' для выхода.\n")
        
    def print_output(self, text):
        """Выводит текст в область вывода"""
        self.output_area.configure(state='normal')  
        self.output_area.insert(tk.END, text)       
        self.output_area.configure(state='disabled') 
        self.output_area.see(tk.END)               
    def process_command(self, event):
        """Обрабатывает введенную команду"""
        command_text = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)  
        
        
        self.print_output(f"[{os.getlogin()}@{socket.gethostname()}]$ {command_text}\n")
        
        
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
            
            
        else:
            self.print_output(f"Ошибка: неизвестная команда '{command_name}'\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = ShellEmulator(root)
    root.mainloop()