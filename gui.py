import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import threading
from monitor import ActivityMonitor
from database import Database
import pystray
from PIL import Image, ImageDraw
# import win32gui
# import win32con

class ActivityTrackerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rastreador de Tempo de Atividade")
        self.root.geometry("900x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.database = Database()
        self.monitor = ActivityMonitor(idle_threshold=60, callback=self.on_state_change)
        
        self.current_state = "active"
        self.current_session_id = None
        self.tray_icon = None

        self.setup_ui()
        self.monitor.start_monitoring()
        self.update_status()
        self.start_auto_refresh()
        self.root.bind("<Unmap>", self.on_minimize)
        
    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.setup_status_tab(notebook)
        self.setup_categorize_tab(notebook)
        self.setup_reports_tab(notebook)
        self.setup_settings_tab(notebook)
    
    def setup_status_tab(self, notebook):
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text='Status Atual')
        
        info_frame = ttk.LabelFrame(status_frame, text="Estado Atual", padding=10)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        self.status_label = ttk.Label(info_frame, text="Estado: Ativo", font=('Arial', 14, 'bold'))
        self.status_label.pack(pady=5)
        
        self.duration_label = ttk.Label(info_frame, text="Duração: 00:00:00", font=('Arial', 12))
        self.duration_label.pack(pady=5)
        
        self.idle_time_label = ttk.Label(info_frame, text="Tempo ocioso: 0s", font=('Arial', 10))
        self.idle_time_label.pack(pady=5)
        
        recent_frame = ttk.LabelFrame(status_frame, text="Sessões Recentes", padding=10)
        recent_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Início', 'Fim', 'Tipo', 'Duração', 'Categoria')
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=15)
        
        self.recent_tree.heading('ID', text='ID')
        self.recent_tree.heading('Início', text='Início')
        self.recent_tree.heading('Fim', text='Fim')
        self.recent_tree.heading('Tipo', text='Tipo')
        self.recent_tree.heading('Duração', text='Duração')
        self.recent_tree.heading('Categoria', text='Categoria')
        
        self.recent_tree.column('ID', width=50)
        self.recent_tree.column('Início', width=150)
        self.recent_tree.column('Fim', width=150)
        self.recent_tree.column('Tipo', width=80)
        self.recent_tree.column('Duração', width=100)
        self.recent_tree.column('Categoria', width=150)
        
        scrollbar = ttk.Scrollbar(recent_frame, orient='vertical', command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recent_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Atualizar", command=self.refresh_recent_sessions).pack(side='left', padx=5)
    
    def setup_categorize_tab(self, notebook):
        cat_frame = ttk.Frame(notebook)
        notebook.add(cat_frame, text='Categorizar Pausas')
        
        info_label = ttk.Label(cat_frame, text="Categorize suas pausas não categorizadas:", font=('Arial', 10))
        info_label.pack(pady=10)
        
        list_frame = ttk.LabelFrame(cat_frame, text="Pausas Não Categorizadas", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Início', 'Fim', 'Duração')
        self.uncategorized_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.uncategorized_tree.heading('ID', text='ID')
        self.uncategorized_tree.heading('Início', text='Início')
        self.uncategorized_tree.heading('Fim', text='Fim')
        self.uncategorized_tree.heading('Duração', text='Duração')
        
        self.uncategorized_tree.column('ID', width=50)
        self.uncategorized_tree.column('Início', width=200)
        self.uncategorized_tree.column('Fim', width=200)
        self.uncategorized_tree.column('Duração', width=100)
        
        self.uncategorized_tree.pack(fill='both', expand=True, pady=5)
        
        cat_input_frame = ttk.Frame(cat_frame)
        cat_input_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(cat_input_frame, text="Categoria:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        categories = [cat[0] for cat in self.database.get_break_categories()]
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(cat_input_frame, textvariable=self.category_var, values=categories, width=30)
        self.category_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(cat_input_frame, text="Notas (opcional):").grid(row=1, column=0, padx=5, pady=5, sticky='nw')
        
        self.notes_text = tk.Text(cat_input_frame, height=3, width=40)
        self.notes_text.grid(row=1, column=1, padx=5, pady=5)
        
        button_frame = ttk.Frame(cat_frame)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Categorizar Selecionada", command=self.categorize_selected).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Atualizar Lista", command=self.refresh_uncategorized).pack(side='left', padx=5)
    
    def setup_reports_tab(self, notebook):
        report_frame = ttk.Frame(notebook)
        notebook.add(report_frame, text='Relatórios')
        
        filter_frame = ttk.LabelFrame(report_frame, text="Filtros", padding=10)
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Período:").grid(row=0, column=0, padx=5, pady=5)
        
        self.period_var = tk.StringVar(value="Hoje")
        period_combo = ttk.Combobox(filter_frame, textvariable=self.period_var, 
                                     values=["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Tudo"], 
                                     state='readonly', width=20)
        period_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="Gerar Relatório", command=self.generate_report).grid(row=0, column=2, padx=5, pady=5)
        
        stats_frame = ttk.LabelFrame(report_frame, text="Estatísticas", padding=10)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.report_text = scrolledtext.ScrolledText(stats_frame, height=20, width=80, font=('Courier', 10))
        self.report_text.pack(fill='both', expand=True)
    
    def setup_settings_tab(self, notebook):
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text='Configurações')
        
        idle_frame = ttk.LabelFrame(settings_frame, text="Detecção de Inatividade", padding=10)
        idle_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(idle_frame, text="Tempo de inatividade (segundos):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.idle_threshold_var = tk.IntVar(value=60)
        idle_spinbox = ttk.Spinbox(idle_frame, from_=10, to=600, textvariable=self.idle_threshold_var, width=10)
        idle_spinbox.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(idle_frame, text="Aplicar", command=self.apply_idle_threshold).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(idle_frame, text="Define após quantos segundos sem atividade o sistema considera você ausente.").grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='w')
        
        startup_frame = ttk.LabelFrame(settings_frame, text="Inicialização", padding=10)
        startup_frame.pack(fill='x', padx=10, pady=10)
        
        self.autostart_var = tk.BooleanVar()
        self.check_autostart_status()
        
        ttk.Checkbutton(startup_frame, text="Iniciar com o Windows", 
                       variable=self.autostart_var, command=self.toggle_autostart).pack(anchor='w', padx=5, pady=5)
        
        ttk.Label(startup_frame, text="Quando ativado, o aplicativo iniciará automaticamente ao ligar o computador.").pack(anchor='w', padx=5, pady=5)
    
    def on_state_change(self, state, session_id):
        self.current_state = state
        self.current_session_id = session_id
        self.update_status()
        
        if state == 'idle':
            self.show_notification("Inatividade detectada", "Você está ausente do computador.")
        else:
            self.show_notification("Atividade detectada", "Você voltou ao computador!")
    
    def update_status(self):
        if self.current_state == 'active':
            self.status_label.config(text="Estado: 🟢 Ativo", foreground='green')
        else:
            self.status_label.config(text="Estado: 🔴 Inativo", foreground='red')
        
        idle_time = int(self.monitor.get_idle_duration())
        self.idle_time_label.config(text=f"Tempo ocioso: {idle_time}s")
    
    def refresh_recent_sessions(self):
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        
        sessions = self.database.get_sessions()[:50]
        
        for session in sessions:
            sid, start, end, stype, duration, category, notes = session
            
            start_str = datetime.fromisoformat(start).strftime('%d/%m/%Y %H:%M:%S') if start else ''
            end_str = datetime.fromisoformat(end).strftime('%d/%m/%Y %H:%M:%S') if end else 'Em andamento'
            
            if duration:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = "N/A"
            
            type_str = "Ativo" if stype == 'active' else "Inativo"
            category_str = category if category else ""
            
            self.recent_tree.insert('', 'end', values=(sid, start_str, end_str, type_str, duration_str, category_str))
    
    def refresh_uncategorized(self):
        for item in self.uncategorized_tree.get_children():
            self.uncategorized_tree.delete(item)
        
        uncategorized = self.database.get_uncategorized_breaks(limit=50)
        
        for item in uncategorized:
            sid, start, end, duration = item
            
            start_str = datetime.fromisoformat(start).strftime('%d/%m/%Y %H:%M:%S')
            end_str = datetime.fromisoformat(end).strftime('%d/%m/%Y %H:%M:%S')
            
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            self.uncategorized_tree.insert('', 'end', values=(sid, start_str, end_str, duration_str))
    
    def categorize_selected(self):
        selection = self.uncategorized_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma pausa para categorizar.")
            return
        
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("Aviso", "Selecione uma categoria.")
            return
        
        item = self.uncategorized_tree.item(selection[0])
        session_id = item['values'][0]
        notes = self.notes_text.get('1.0', 'end-1c').strip()
        
        self.monitor.categorize_break_by_id(session_id, category, notes if notes else None)
        
        messagebox.showinfo("Sucesso", "Pausa categorizada com sucesso!")
        self.refresh_uncategorized()
        self.refresh_recent_sessions()
        self.notes_text.delete('1.0', 'end')
        self.category_var.set('')
    
    def generate_report(self):
        period = self.period_var.get()
        
        end_date = datetime.now()
        if period == "Hoje":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "Últimos 7 dias":
            start_date = end_date - timedelta(days=7)
        elif period == "Últimos 30 dias":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = None
        
        stats = self.database.get_statistics(start_date, end_date)
        
        self.report_text.delete('1.0', 'end')
        
        report = f"{'='*70}\n"
        report += f"RELATÓRIO DE ATIVIDADE - {period.upper()}\n"
        report += f"{'='*70}\n\n"
        
        if start_date:
            report += f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}\n\n"
        else:
            report += f"Período: Todo o histórico\n\n"
        
        total_active = 0
        total_idle = 0
        category_times = {}
        
        for stat in stats:
            stype, category, total_seconds, count = stat
            
            if stype == 'active':
                total_active += total_seconds
            else:
                total_idle += total_seconds
                if category:
                    category_times[category] = category_times.get(category, 0) + total_seconds
        
        report += f"RESUMO GERAL:\n"
        report += f"{'-'*70}\n"
        report += f"Tempo Ativo:   {self.format_duration(total_active)}\n"
        report += f"Tempo Inativo: {self.format_duration(total_idle)}\n"
        
        total_time = total_active + total_idle
        if total_time > 0:
            active_pct = (total_active / total_time) * 100
            idle_pct = (total_idle / total_time) * 100
            report += f"\nPercentuais:\n"
            report += f"  Ativo:   {active_pct:.1f}%\n"
            report += f"  Inativo: {idle_pct:.1f}%\n"
        
        report += f"\n{'='*70}\n"
        report += f"PAUSAS POR CATEGORIA:\n"
        report += f"{'-'*70}\n"
        
        if category_times:
            sorted_categories = sorted(category_times.items(), key=lambda x: x[1], reverse=True)
            for category, seconds in sorted_categories:
                report += f"{category:<30} {self.format_duration(seconds)}\n"
        else:
            report += "Nenhuma pausa categorizada no período.\n"
        
        report += f"\n{'='*70}\n"
        
        self.report_text.insert('1.0', report)
    
    def format_duration(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def apply_idle_threshold(self):
        threshold = self.idle_threshold_var.get()
        self.monitor.set_idle_threshold(threshold)
        messagebox.showinfo("Sucesso", f"Limite de inatividade alterado para {threshold} segundos.")
    
    def check_autostart_status(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "ActivityTracker")
                self.autostart_var.set(True)
            except:
                self.autostart_var.set(False)
            winreg.CloseKey(key)
        except:
            self.autostart_var.set(False)
    
    def toggle_autostart(self):
        import winreg
        import sys
        import os
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run",
                           0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
        
        if self.autostart_var.get():
            app_path = os.path.abspath(sys.argv[0])
            if app_path.endswith('.py'):
                executable = sys.executable
                app_path = f'"{executable}" "{app_path}"'
            else:
                app_path = f'"{app_path}"'
            
            winreg.SetValueEx(key, "ActivityTracker", 0, winreg.REG_SZ, app_path)
            messagebox.showinfo("Sucesso", "Aplicativo configurado para iniciar com o Windows.")
        else:
            try:
                winreg.DeleteValue(key, "ActivityTracker")
                messagebox.showinfo("Sucesso", "Inicialização automática desativada.")
            except:
                pass
        
        winreg.CloseKey(key)
    
    def start_auto_refresh(self):
        self.refresh_recent_sessions()
        self.refresh_uncategorized()
        self.root.after(5000, self.periodic_refresh)
    
    def periodic_refresh(self):
        self.update_status()
        self.root.after(5000, self.periodic_refresh)
    
    def show_notification(self, title, message):
        pass
    
    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
        
        menu = pystray.Menu(
            pystray.MenuItem("Abrir", self.show_window, default=True),
            pystray.MenuItem("Sair", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("ActivityTracker", image, "Rastreador de Atividade", menu)

    def ensure_tray_icon(self):
        if not self.tray_icon:
            self.create_tray_icon()
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_window(self, icon=None, item=None):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        self.root.withdraw()

    def on_minimize(self, event):
        # Quando minimizar, esconder e ir para bandeja
        if self.root.state() == 'iconic':
            self.ensure_tray_icon()
            self.hide_window()
    
    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja minimizar para a bandeja ou sair completamente?\n\nOK = Minimizar para bandeja\nCancelar = Continuar usando"):
            self.ensure_tray_icon()
            self.hide_window()

    def quit_app(self, icon=None, item=None):
        self.monitor.stop_monitoring()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ActivityTrackerGUI()
    app.run()
