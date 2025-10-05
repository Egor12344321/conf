import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import socket
import argparse
import time
import xml.etree.ElementTree as ET
import base64

class VirtualFileSystem:
    def __init__(self):
        self.root = {'type': 'directory', 'children': {}, 'permissions': '755'}
        self.current_path = '/'
    
    def load_from_xml(self, xml_path):
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"VFS файл не найден: {xml_path}")
        
        tree = ET.parse(xml_path)
        root_element = tree.getroot()
        self.root = self._parse_xml_element(root_element)
        self.current_path = '/'
    
    def _parse_xml_element(self, element):
        if element.tag == 'directory':
            node = {
                'type': 'directory',
                'name': element.get('name', ''),
                'permissions': element.get('permissions', '755'),
                'children': {}
            }
            for child in element:
                child_node = self._parse_xml_element(child)
                node['children'][child_node['name']] = child_node
            return node
        elif element.tag == 'file':
            content = element.text or ''
            if element.get('encoding') == 'base64':
                content = base64.b64decode(content).decode('utf-8')
            return {
                'type': 'file',
                'name': element.get('name', ''),
                'content': content,
                'permissions': element.get('permissions', '644'),
                'size': len(content)
            }
        return None
    
    def save_to_xml(self, xml_path):
        root_element = self._create_xml_element(self.root)
        
        from xml.dom import minidom
        rough_string = ET.tostring(root_element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
    
    def _create_xml_element(self, node):
        if node['type'] == 'directory':
            element = ET.Element('directory', {
                'name': node['name'],
                'permissions': node['permissions']
            })
            for child in node['children'].values():
                child_element = self._create_xml_element(child)
                element.append(child_element)
            return element
        elif node['type'] == 'file':
            element = ET.Element('file', {
                'name': node['name'],
                'permissions': node['permissions'],
                'encoding': 'base64'
            })
            encoded_content = base64.b64encode(node['content'].encode('utf-8')).decode('utf-8')
            element.text = encoded_content
            return element
    
    def get_current_directory(self):
        path_parts = [p for p in self.current_path.split('/') if p]
        current = self.root
        for part in path_parts:
            if part in current['children']:
                current = current['children'][part]
            else:
                return None
        return current
    
    def list_directory(self, path=None):
        if path is None:
            path = self.current_path
        
        target_dir = self._resolve_path(path)
        if not target_dir or target_dir['type'] != 'directory':
            return None
        
        return [{'name': name, 'type': child['type'], 'permissions': child['permissions']} 
                for name, child in target_dir['children'].items()]
    
    def _resolve_path(self, path):
        if path.startswith('/'):
            path_parts = [p for p in path.split('/') if p]
            current = self.root
        else:
            path_parts = [p for p in path.split('/') if p]
            current = self.get_current_directory()
        
        for part in path_parts:
            if part == '..':
                current = self.root
                self.current_path = '/'
            elif part == '.':
                continue
            elif part in current.get('children', {}):
                current = current['children'][part]
            else:
                return None
        return current
    
    def change_directory(self, path):
        new_dir = self._resolve_path(path)
        if new_dir and new_dir['type'] == 'directory':
            if path.startswith('/'):
                self.current_path = path
            else:
                if self.current_path == '/':
                    self.current_path = '/' + path
                else:
                    self.current_path = self.current_path + '/' + path
            return True
        return False
    
    def read_file(self, path):
        file_node = self._resolve_path(path)
        if file_node and file_node['type'] == 'file':
            return file_node['content']
        return None

class ShellEmulator:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root
        username = os.getlogin()
        hostname = socket.gethostname()
        self.root.title(f"Эмулятор - [{username}@{hostname}]")
        
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.vfs = VirtualFileSystem()
        
        print(f"Параметры запуска:")
        print(f"  VFS путь: {vfs_path if vfs_path else 'Не указан (используется по умолчанию)'}")
        print(f"  Скрипт: {script_path if script_path else 'Не указан (интерактивный режим)'}")
        print("-" * 50)
        
        if vfs_path and os.path.exists(vfs_path):
            try:
                self.vfs.load_from_xml(vfs_path)
                print(f"VFS загружена из: {vfs_path}")
            except Exception as e:
                print(f"Ошибка загрузки VFS: {e}")
        
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
            self._execute_ls(args)
            
        elif command_name == "cd":
            self._execute_cd(args)
                
        elif command_name == "echo":
            self.print_output(f"{' '.join(args)}\n")
            
        elif command_name == "vfs-save":
            self._execute_vfs_save(args)
            
        elif command_name == "rev":
            self._execute_rev(args)
            
        elif command_name == "head":
            self._execute_head(args)
            
        else:
            self.print_output(f"Ошибка: неизвестная команда '{command_name}'\n")
    
    def _execute_ls(self, args):
        if self.vfs_path:
            items = self.vfs.list_directory()
            if items is not None:
                for item in items:
                    perm = item['permissions']
                    type_char = 'd' if item['type'] == 'directory' else '-'
                    self.print_output(f"{type_char}{perm} {item['name']}\n")
            else:
                self.print_output("Ошибка: директория не найдена\n")
        else:
            self.print_output(f"Команда 'ls' вызвана с аргументами: {args}\n")
    
    def _execute_cd(self, args):
        if self.vfs_path:
            if args:
                if self.vfs.change_directory(args[0]):
                    self.print_output(f"Переход в директорию: {args[0]}\n")
                else:
                    self.print_output(f"Ошибка: директория '{args[0]}' не найдена\n")
            else:
                self.print_output("Команда 'cd' требует аргумент - путь к директории\n")
        else:
            if args:
                self.print_output(f"Команда 'cd' пытается перейти в директорию: {args[0]}\n")
            else:
                self.print_output("Команда 'cd' требует аргумент - путь к директории\n")
    
    def _execute_vfs_save(self, args):
        if not self.vfs_path:
            self.print_output("Ошибка: VFS не загружена\n")
            return
            
        if args:
            save_path = args[0]
        else:
            save_path = self.vfs_path
            
        try:
            self.vfs.save_to_xml(save_path)
            self.print_output(f"VFS сохранена в: {save_path}\n")
        except Exception as e:
            self.print_output(f"Ошибка сохранения VFS: {str(e)}\n")
    
    def _execute_rev(self, args):
        if not self.vfs_path:
            self.print_output("Ошибка: VFS не загружена\n")
            return
            
        if not args:
            self.print_output("Ошибка: команда 'rev' требует путь к файлу\n")
            return
            
        content = self.vfs.read_file(args[0])
        if content is None:
            self.print_output(f"Ошибка: файл '{args[0]}' не найден\n")
            return
            
        reversed_content = '\n'.join(reversed(content.split('\n')))
        self.print_output(reversed_content + '\n')
    
    def _execute_head(self, args):
        if not self.vfs_path:
            self.print_output("Ошибка: VFS не загружена\n")
            return
            
        if not args:
            self.print_output("Ошибка: команда 'head' требует путь к файлу\n")
            return
            
        lines_count = 10
        file_path = args[0]
        
        if len(args) > 1 and args[0] == '-n':
            try:
                lines_count = int(args[1])
                file_path = args[2] if len(args) > 2 else None
            except ValueError:
                self.print_output("Ошибка: неверное количество строк\n")
                return
                
        if not file_path:
            self.print_output("Ошибка: не указан файл\n")
            return
            
        content = self.vfs.read_file(file_path)
        if content is None:
            self.print_output(f"Ошибка: файл '{file_path}' не найден\n")
            return
            
        lines = content.split('\n')[:lines_count]
        self.print_output('\n'.join(lines) + '\n')
    
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