import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import calendar
import threading
import math
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
        self.root.geometry("1100x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.database = Database()
        # Fecha sessões que ficaram abertas por desligamento/reboot
        self.database.close_open_sessions()
        self.monitor = ActivityMonitor(idle_threshold=60, callback=self.on_state_change)
        
        self.current_state = "active"
        self.current_session_id = None
        self.tray_icon = None
        self.tray_thread = None
        self.is_window_visible = True
        self.last_state_change_time = datetime.now()
        self.dashboard_initialized = False
        self.tooltip = None
        self.pie_data = {}
        self.bar_item_info = {}
        self._bar_data = None
        self._bar_drawer = None
        self.top_idle_category = (None, 0)

        self.setup_ui()
        self.monitor.start_monitoring()
        self.update_status()
        self.start_auto_refresh()
        self.root.bind("<Unmap>", self.on_minimize)
        # Garantir ícone na bandeja desde o início
        self.ensure_tray_icon()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.setup_status_tab(self.notebook)
        self.setup_dashboard_tab(self.notebook)
        self.setup_categorize_tab(self.notebook)
        self.setup_reports_tab(self.notebook)
        self.setup_settings_tab(self.notebook)
    
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
        info_label.pack(pady=(10, 5))

        # Filtros de período
        filter_frame = ttk.Frame(cat_frame)
        filter_frame.pack(fill='x', padx=10, pady=(0, 8))

        ttk.Label(filter_frame, text="Início (AAAA-MM-DD):").grid(row=0, column=0, padx=4, pady=2, sticky='w')
        self.cat_start_var = tk.StringVar()
        cat_start_entry = ttk.Entry(filter_frame, textvariable=self.cat_start_var, width=14, validate='key')
        cat_start_entry['validatecommand'] = (self.root.register(self.validate_date_input), '%P')
        cat_start_entry.grid(row=0, column=1, padx=4, pady=2)
        ttk.Button(filter_frame, text="📅", width=3, command=lambda: self.open_date_picker(self.cat_start_var)).grid(row=0, column=2, padx=2, pady=2)

        ttk.Label(filter_frame, text="Fim (AAAA-MM-DD):").grid(row=0, column=3, padx=4, pady=2, sticky='w')
        self.cat_end_var = tk.StringVar()
        cat_end_entry = ttk.Entry(filter_frame, textvariable=self.cat_end_var, width=14, validate='key')
        cat_end_entry['validatecommand'] = (self.root.register(self.validate_date_input), '%P')
        cat_end_entry.grid(row=0, column=4, padx=4, pady=2)
        ttk.Button(filter_frame, text="📅", width=3, command=lambda: self.open_date_picker(self.cat_end_var)).grid(row=0, column=5, padx=2, pady=2)

        ttk.Button(filter_frame, text="Aplicar filtros", command=lambda: self.refresh_uncategorized(show_warning=True)).grid(row=0, column=6, padx=8, pady=2)
        for col in range(7):
            filter_frame.columnconfigure(col, weight=0)

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

        scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.uncategorized_tree.yview)
        self.uncategorized_tree.configure(yscrollcommand=scroll.set)
        self.uncategorized_tree.pack(side='left', fill='both', expand=True, pady=5)
        scroll.pack(side='right', fill='y')
        
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
                                     values=["Hoje", "Ontem", "Últimos 7 dias", "Últimos 30 dias", "Tudo", "Personalizado"], 
                                     state='readonly', width=20)
        period_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="Gerar Relatório", command=self.generate_report).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(filter_frame, text="Início (AAAA-MM-DD)").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.custom_start_var = tk.StringVar()
        start_entry = ttk.Entry(filter_frame, textvariable=self.custom_start_var, width=18, validate='key')
        start_entry['validatecommand'] = (self.root.register(self.validate_date_input), '%P')
        start_entry.grid(row=1, column=1, padx=5, pady=2, sticky='w')

        ttk.Label(filter_frame, text="Fim (AAAA-MM-DD)").grid(row=2, column=0, padx=5, pady=2, sticky='w')
        self.custom_end_var = tk.StringVar()
        end_entry = ttk.Entry(filter_frame, textvariable=self.custom_end_var, width=18, validate='key')
        end_entry['validatecommand'] = (self.root.register(self.validate_date_input), '%P')
        end_entry.grid(row=2, column=1, padx=5, pady=2, sticky='w')
        
        stats_frame = ttk.LabelFrame(report_frame, text="Estatísticas", padding=10)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.report_text = scrolledtext.ScrolledText(stats_frame, height=20, width=80, font=('Courier', 10))
        self.report_text.pack(fill='both', expand=True)

    def setup_settings_tab(self, notebook):
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text='Configurações')
        
        threshold_frame = ttk.LabelFrame(settings_frame, text="Limite de Inatividade", padding=10)
        threshold_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(threshold_frame, text="Tempo (segundos):").grid(row=0, column=0, padx=5, pady=5)
        
        self.idle_threshold_var = tk.IntVar(value=60)
        threshold_spinbox = ttk.Spinbox(threshold_frame, from_=10, to=600, textvariable=self.idle_threshold_var, width=10)
        threshold_spinbox.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(threshold_frame, text="Aplicar", command=self.apply_idle_threshold).grid(row=0, column=2, padx=5, pady=5)
        
        autostart_frame = ttk.LabelFrame(settings_frame, text="Inicialização Automática", padding=10)
        autostart_frame.pack(fill='x', padx=10, pady=10)
        
        self.autostart_var = tk.BooleanVar()
        self.check_autostart_status()
        
        autostart_check = ttk.Checkbutton(autostart_frame, text="Iniciar com o Windows", 
                                          variable=self.autostart_var, command=self.toggle_autostart)
        autostart_check.pack(pady=5)
        
        week_frame = ttk.LabelFrame(settings_frame, text="Início da Semana", padding=10)
        week_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(week_frame, text="Considerar semana iniciando em:").grid(row=0, column=0, padx=5, pady=5)
        
        self.week_start_var = tk.StringVar(value="Segunda")
        week_combo = ttk.Combobox(week_frame, textvariable=self.week_start_var, 
                                  values=["Segunda", "Domingo"], state='readonly', width=15)
        week_combo.grid(row=0, column=1, padx=5, pady=5)

    def on_state_change(self, state, session_id):
        self.current_state = state
        self.current_session_id = session_id
        self.last_state_change_time = datetime.now()
        self.update_status()
        if state == 'idle':
            self.show_notification("Inatividade detectada", "Você está ausente do computador.")
        else:
            self.show_notification("Atividade detectada", "Você voltou ao computador!")

    def refresh_recent_sessions(self):
        selected_id = None
        sel = self.recent_tree.selection()
        if sel:
            try:
                selected_id = self.recent_tree.item(sel[0]).get('values', [None])[0]
            except Exception:
                selected_id = None
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

            node = self.recent_tree.insert('', 'end', values=(sid, start_str, end_str, type_str, duration_str, category_str))
            if selected_id is not None and sid == selected_id:
                self.recent_tree.selection_set(node)

    def refresh_uncategorized(self, show_warning=False):
        selected_id = None
        sel = self.uncategorized_tree.selection()
        if sel:
            try:
                selected_id = self.uncategorized_tree.item(sel[0]).get('values', [None])[0]
            except Exception:
                selected_id = None
        for item in self.uncategorized_tree.get_children():
            self.uncategorized_tree.delete(item)

        # Filtros de período (somente início/fim)
        start_str = self.cat_start_var.get().strip()
        end_str = self.cat_end_var.get().strip()

        def parse_date(val):
            if not val:
                return None
            try:
                return datetime.strptime(val, '%Y-%m-%d')
            except ValueError:
                if show_warning:
                    messagebox.showwarning("Data inválida", "Use o formato AAAA-MM-DD.")
                    return "INVALID"
                return None

        start_dt = end_dt = None
        if start_str:
            dt = parse_date(start_str)
            if dt == "INVALID":
                return
            start_dt = dt
        if end_str:
            dt = parse_date(end_str)
            if dt == "INVALID":
                return
            end_dt = dt

        # Se só início preenchido, usar aquele dia inteiro
        if start_dt and not end_dt:
            end_dt = start_dt

        # Inclusivo: adicionar fim do dia
        if end_dt:
            end_dt = end_dt + timedelta(days=1) - timedelta(milliseconds=1)

        # Quando há filtros, não limitar resultados; sem filtros, manter limite padrão
        limit = None if (start_str or end_str) else 50

        def fmt_db(dt_obj):
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S') if dt_obj else None

        start_db = fmt_db(start_dt)
        end_db = fmt_db(end_dt)

        uncategorized = self.database.get_uncategorized_breaks(limit=limit, start_date=start_db, end_date=end_db)

        for item in uncategorized:
            sid, start, end, duration = item

            start_str_fmt = datetime.fromisoformat(start).strftime('%d/%m/%Y %H:%M:%S')
            end_str_fmt = datetime.fromisoformat(end).strftime('%d/%m/%Y %H:%M:%S')

            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            node = self.uncategorized_tree.insert('', 'end', values=(sid, start_str_fmt, end_str_fmt, duration_str))
            if selected_id is not None and sid == selected_id:
                self.uncategorized_tree.selection_set(node)

    def update_status(self):
        if self.current_state == 'active':
            self.status_label.config(text="Estado: Ativo", foreground='green')
        else:
            self.status_label.config(text="Estado: Inativo", foreground='red')
        idle_time = int(self.monitor.get_idle_duration())
        self.idle_time_label.config(text=f"Tempo ocioso: {idle_time}s")
        if self.last_state_change_time:
            elapsed = int((datetime.now() - self.last_state_change_time).total_seconds())
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.duration_label.config(text=f"Duração: {hours:02d}:{minutes:02d}:{seconds:02d}")

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
            end_date = start_date + timedelta(days=1)
        elif period == "Ontem":
            start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif period == "Últimos 7 dias":
            start_date = end_date - timedelta(days=7)
        elif period == "Últimos 30 dias":
            start_date = end_date - timedelta(days=30)
        elif period == "Tudo":
            start_date = None
        elif period == "Personalizado":
            try:
                start_date = datetime.strptime(self.custom_start_var.get(), '%Y-%m-%d')
                end_date = datetime.strptime(self.custom_end_var.get(), '%Y-%m-%d') + timedelta(days=1)
            except ValueError:
                messagebox.showwarning("Datas inválidas", "Informe datas no formato AAAA-MM-DD para início e fim.")
                return
        stats = self.database.get_statistics(start_date, end_date)
        self.report_text.delete('1.0', 'end')
        report = f"{'='*70}\n"
        report += f"RELATÓRIO DE ATIVIDADE - {period.upper()}\n"
        report += f"{'='*70}\n\n"
        if start_date:
            report += f"Período: {start_date.strftime('%d/%m/%Y')} a {(end_date - timedelta(seconds=1)).strftime('%d/%m/%Y')}\n\n"
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

    def show_tooltip(self, event, text):
        if not self.tooltip:
            self.tooltip = tk.Label(self.root, text=text, bg="#111827", fg="white", padx=6, pady=2, font=('Segoe UI', 9), relief='solid', bd=1)
        self.tooltip.config(text=text)
        # Posição básica à direita/abaixo do ponteiro
        x = self.root.winfo_pointerx() - self.root.winfo_rootx() + 12
        y = self.root.winfo_pointery() - self.root.winfo_rooty() + 12
        self.tooltip.place(x=-1000, y=-1000)  # coloca fora para medir
        self.tooltip.update_idletasks()
        tw = self.tooltip.winfo_reqwidth()
        th = self.tooltip.winfo_reqheight()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        # Se ultrapassar a direita, coloca à esquerda do ponteiro
        if x + tw > root_w:
            x = max(0, self.root.winfo_pointerx() - self.root.winfo_rootx() - tw - 12)
        # Se ultrapassar abaixo, sobe
        if y + th > root_h:
            y = max(0, self.root.winfo_pointery() - self.root.winfo_rooty() - th - 12)
        self.tooltip.place(x=x, y=y)

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.place_forget()

    def on_pie_motion(self, key, event):
        slices = self.pie_data.get(key)
        if not slices:
            return
        total = sum(v for _, v, _ in slices)
        if total <= 0:
            self.hide_tooltip()
            return
        cx, cy = 75, 75
        dx, dy = event.x - cx, event.y - cy
        angle = (math.degrees(math.atan2(-dy, dx)) + 360) % 360
        accum = 0
        hovered_tag = None
        hovered_label = None
        hovered_value = None
        for label, value, tag in slices:
            extent = (value / total) * 360
            if accum <= angle < accum + extent:
                hovered_tag = tag
                hovered_label = label
                hovered_value = value
                break
            accum += extent
        event.widget.itemconfigure('slice', width=1)
        if hovered_tag:
            event.widget.itemconfigure(hovered_tag, width=2)
            pct = hovered_value * 100 / total if total else 0
            extra = ""
            if hovered_label.startswith("Inativo") and self.top_idle_category[0]:
                cat, secs = self.top_idle_category
                extra = f"\nTop cat: {cat} ({self.format_duration(secs)})"
            self.show_tooltip(event, f"{hovered_label}: {self.format_duration(int(hovered_value))} ({pct:.1f}%)" + extra)
        else:
            self.hide_tooltip()

    def on_pie_leave(self, event):
        try:
            event.widget.itemconfigure('slice', width=1)
        except Exception:
            pass
        self.hide_tooltip()

    def on_bar_motion(self, event):
        items = event.widget.find_withtag('current')
        if not items:
            self.hide_tooltip()
            return
        info_map = self.bar_item_info.get(event.widget)
        if not info_map:
            self.hide_tooltip()
            return
        item = items[0]
        if item not in info_map:
            self.hide_tooltip()
            return
        day, act, idle, segment = info_map[item]
        total = act + idle
        if segment == 'active':
            pct = act * 100 / total if total else 0
            text = f"Dia {day}: Ativo {self.format_duration(act)} ({pct:.1f}%)"
        else:
            pct = idle * 100 / total if total else 0
            text = f"Dia {day}: Inativo {self.format_duration(idle)} ({pct:.1f}%)"
        event.widget.itemconfigure('bar', width=0)
        event.widget.itemconfigure(item, width=1)
        self.show_tooltip(event, text)

    def on_bar_leave(self, event):
        event.widget.itemconfigure('bar', width=0)
        self.hide_tooltip()

    def on_bar_resize(self, event):
        if self._bar_data and self._bar_drawer:
            daily_active, daily_idle = self._bar_data
            self._bar_drawer(event.widget, daily_active, daily_idle)

    def setup_dashboard_tab(self, notebook):
        dash_frame = ttk.Frame(notebook)
        notebook.add(dash_frame, text='Dashboard')

        container = ttk.Frame(dash_frame, padding=10)
        container.pack(fill='both', expand=True)

        cards_frame = ttk.Frame(container)
        cards_frame.pack(fill='x', pady=(0, 10))

        self.dash_labels = {}

        def make_card(parent, title, key, bg_color, accent):
            card = tk.Frame(parent, bg=bg_color, bd=0, relief='flat', padx=12, pady=10)
            title_lbl = tk.Label(card, text=title.upper(), bg=bg_color, fg=accent, font=('Segoe UI', 9, 'bold'))
            title_lbl.pack(anchor='w')
            value_lbl = tk.Label(card, text="--", bg=bg_color, fg='white', font=('Segoe UI', 26, 'bold'))
            value_lbl.pack(anchor='w', pady=(2, 0))
            pct_lbl = tk.Label(card, text="--", bg=bg_color, fg='white', font=('Segoe UI', 11))
            pct_lbl.pack(anchor='w', pady=(0, 2))
            self.dash_labels[key] = {'value': value_lbl, 'pct': pct_lbl}
            return card

        card_specs = [
            ("Ativo hoje", "active_day", '#0ea36f', '#aef5d8'),
            ("Inativo hoje", "idle_day", '#e63b3b', '#ffd7d7'),
            ("Ativo semana", "active_week", '#0ea5e9', '#d9f3ff'),
            ("Inativo semana", "idle_week", '#ef8f00', '#fff0d9'),
            ("Ativo mês (dias úteis)", "active_month", '#6366f1', '#e2e7ff'),
            ("Inativo mês (dias úteis)", "idle_month", '#9333ea', '#f3e8ff')
        ]

        for idx, (title, key, bg, accent) in enumerate(card_specs):
            card = make_card(cards_frame, title, key, bg, accent)
            card.grid(row=idx//3, column=idx%3, sticky='nsew', padx=6, pady=6)
        for col in range(3):
            cards_frame.columnconfigure(col, weight=1)

        summary_frame = ttk.Frame(container)
        summary_frame.pack(fill='x', pady=(0, 10))

        extra_specs = [
            ("Maior pausa", "longest_idle", '#111827', '#9ca3af'),
            ("Média diária (inativo)", "avg_day", '#2563eb', '#dbeafe'),
            ("Média semanal (inativo)", "avg_week", '#0891b2', '#ccfbf1'),
            ("Média mensal (dias úteis)", "avg_month", '#c026d3', '#f3e8ff')
        ]

        for idx, (title, key, bg, accent) in enumerate(extra_specs):
            card = tk.Frame(summary_frame, bg=bg, bd=0, relief='flat', padx=12, pady=10)
            title_lbl = tk.Label(card, text=title.upper(), bg=bg, fg=accent, font=('Segoe UI', 9, 'bold'))
            title_lbl.pack(anchor='w')
            value_lbl = tk.Label(card, text="--", bg=bg, fg='white', font=('Segoe UI', 22, 'bold'))
            value_lbl.pack(anchor='w', pady=(2, 0))
            pct_lbl = tk.Label(card, text="--", bg=bg, fg='white', font=('Segoe UI', 11))
            pct_lbl.pack(anchor='w')
            extra_lbl = tk.Label(card, text="", bg=bg, fg=accent, font=('Segoe UI', 9))
            extra_lbl.pack(anchor='w')
            self.dash_labels[key] = {'value': value_lbl, 'pct': pct_lbl, 'extra': extra_lbl}
            card.grid(row=0, column=idx, sticky='nsew', padx=6, pady=6)
        for col in range(4):
            summary_frame.columnconfigure(col, weight=1)

        # chart_bg = container.cget('background')
        charts_frame = ttk.Frame(container)
        charts_frame.pack(fill='x', pady=(0, 10))
        style = ttk.Style()
        chart_bg = style.lookup('TFrame', 'background') or self.root.cget('bg') or '#f0f0f0'
        pies_frame = ttk.LabelFrame(charts_frame, text="Distribuição Ativo x Inativo")



        charts_row = ttk.Frame(container)
        charts_row.pack(fill='x', pady=(0, 10))

        pies_frame = ttk.LabelFrame(charts_row, text="Distribuição Ativo x Inativo")
        pies_frame.pack(side='left', fill='both', expand=True, padx=(0, 6))

        self.pie_canvases = {}
        for idx, label in enumerate(["Hoje", "Semana", "Mês"]):
            sub = ttk.Frame(pies_frame)
            sub.grid(row=0, column=idx, padx=4, pady=4, sticky='n')
            ttk.Label(sub, text=label).pack()
            canvas = tk.Canvas(sub, width=150, height=150, bg=chart_bg, highlightthickness=0)
            canvas.pack()
            self.pie_canvases[label.lower()] = canvas
            canvas.bind("<Motion>", lambda e, key=label.lower(): self.on_pie_motion(key, e))
            canvas.bind("<Leave>", self.on_pie_leave)
        pies_frame.columnconfigure(0, weight=1)
        pies_frame.columnconfigure(1, weight=1)
        pies_frame.columnconfigure(2, weight=1)

        cat_frame = ttk.LabelFrame(charts_row, text="Categorias de inatividade")
        cat_frame.pack(side='left', fill='both', expand=True, padx=(6, 0))
        self.cat_pies = {}
        for idx, label in enumerate(["Hoje", "Semana", "Mês"]):
            sub = ttk.Frame(cat_frame)
            sub.grid(row=0, column=idx, padx=4, pady=4, sticky='n')
            ttk.Label(sub, text=label).pack()
            canvas = tk.Canvas(sub, width=150, height=150, bg=chart_bg, highlightthickness=0)
            canvas.pack()
            key = f"cat_{label.lower()}"
            self.cat_pies[key] = canvas
            canvas.bind("<Motion>", lambda e, key=key: self.on_pie_motion(key, e))
            canvas.bind("<Leave>", self.on_pie_leave)
        cat_frame.columnconfigure(0, weight=1)
        cat_frame.columnconfigure(1, weight=1)
        cat_frame.columnconfigure(2, weight=1)

        bars_frame = ttk.LabelFrame(container, text="Evolução no mês (dias)")
        bars_frame.pack(fill='both', expand=True, pady=(0, 5))
        self.bar_canvas = tk.Canvas(bars_frame, width=480, height=170, bg=chart_bg, highlightthickness=0)
        self.bar_canvas.pack(fill='both', expand=True)
        self.bar_canvas.bind("<Motion>", self.on_bar_motion)
        self.bar_canvas.bind("<Leave>", self.on_bar_leave)
        self.bar_canvas.bind("<Configure>", self.on_bar_resize)

    def apply_idle_threshold(self):
        threshold = self.idle_threshold_var.get()
        self.monitor.set_idle_threshold(threshold)
        messagebox.showinfo("Sucesso", f"Limite de inatividade alterado para {threshold} segundos.")

    def check_autostart_status(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
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
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
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
        self.refresh_all()
        self.root.after(5000, self.periodic_refresh)

    def periodic_refresh(self):
        if self.is_window_visible and self.root.state() == 'normal':
            self.refresh_all()
        else:
            self.update_status()
        self.root.after(5000, self.periodic_refresh)

    def refresh_all(self):
        self.update_status()
        self.refresh_recent_sessions()
        self.refresh_uncategorized()
        if self.is_window_visible and self.notebook.tab(self.notebook.select(), "text") == 'Dashboard':
            self.load_dashboard()

    def show_notification(self, title, message):
        pass

    def on_tab_changed(self, event):
        if self.is_window_visible and self.notebook.tab(self.notebook.select(), "text") == 'Dashboard':
            self.load_dashboard()

    def validate_date_input(self, text):
        import re
        return re.fullmatch(r"\d{0,4}(?:-\d{0,2}(?:-\d{0,2})?)?", text) is not None

    def get_week_start(self, reference):
        start_weekday = 0 if self.week_start_var.get() == "Segunda" else 6
        ref = reference.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = (ref.weekday() - start_weekday) % 7
        return ref - timedelta(days=delta)

    def working_days_in_month_until(self, reference):
        first = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        days = 0
        current = first
        while current.date() <= reference.date():
            if current.weekday() < 5:
                days += 1
            current += timedelta(days=1)
        return days or 1

    def open_date_picker(self, target_var):
        # Simple month-view picker
        top = tk.Toplevel(self.root)
        top.title("Selecionar data")
        top.grab_set()
        top.resizable(False, False)

        today = datetime.today()
        sel_year = tk.IntVar(value=today.year)
        sel_month = tk.IntVar(value=today.month)

        def build_calendar(year, month):
            for w in cal_frame.winfo_children():
                w.destroy()
            ttk.Label(cal_frame, text=f"{calendar.month_name[month]} {year}", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=7, pady=(0,4))
            days_hdr = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D']
            for i, d in enumerate(days_hdr):
                ttk.Label(cal_frame, text=d, width=3, anchor='center').grid(row=1, column=i)
            month_days = calendar.monthcalendar(year, month)
            for r, week in enumerate(month_days, start=2):
                for c, day in enumerate(week):
                    if day == 0:
                        ttk.Label(cal_frame, text="", width=3).grid(row=r, column=c)
                    else:
                        btn = ttk.Button(cal_frame, text=str(day), width=3,
                                        command=lambda d=day: select_date(year, month, d))
                        btn.grid(row=r, column=c, padx=1, pady=1)

        def select_date(y, m, d):
            target_var.set(f"{y:04d}-{m:02d}-{d:02d}")
            top.destroy()

        nav_frame = ttk.Frame(top, padding=6)
        nav_frame.pack(fill='x')
        ttk.Button(nav_frame, text="<", width=3, command=lambda: shift_month(-1)).pack(side='left')
        ttk.Button(nav_frame, text=">", width=3, command=lambda: shift_month(1)).pack(side='right')

        cal_frame = ttk.Frame(top, padding=6)
        cal_frame.pack()

        def shift_month(delta):
            m = sel_month.get() + delta
            y = sel_year.get()
            if m < 1:
                m = 12
                y -= 1
            elif m > 12:
                m = 1
                y += 1
            sel_month.set(m)
            sel_year.set(y)
            build_calendar(y, m)

        build_calendar(sel_year.get(), sel_month.get())

    def load_dashboard(self):
        # Coleta dados sem rodar quando janela não visível
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = self.get_week_start(now)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Sessions
        day_idle = self.database.get_sessions_by_type('idle', today_start, now)
        day_active = self.database.get_sessions_by_type('active', today_start, now)
        week_idle = self.database.get_sessions_by_type('idle', week_start, now)
        week_active = self.database.get_sessions_by_type('active', week_start, now)
        month_idle = self.database.get_sessions_by_type('idle', month_start, now)
        month_active = self.database.get_sessions_by_type('active', month_start, now)
        all_idle = self.database.get_sessions_by_type('idle', None, now)

        def total_seconds(rows):
            total = 0
            for _, start, end, _, duration, _ in rows:
                if duration:
                    total += duration
                elif end and start:
                    total += int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())
            return total

        def longest_idle(rows):
            best = (0, None)
            for _, start, end, _, duration, cat in rows:
                dur = duration
                if dur is None and end and start:
                    dur = int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())
                if dur and dur > best[0]:
                    best = (dur, cat)
            return best

        def fmt_secs(s):
            h = s // 3600
            m = (s % 3600) // 60
            sec = s % 60
            return f"{h:02d}:{m:02d}:{sec:02d}"

        def duration_from_row(row):
            _, start, end, _, duration, _ = row
            if duration:
                return duration
            if end and start:
                return int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())
            return 0

        def aggregate_daily(rows):
            totals = {}
            for row in rows:
                _, start, _, _, _, _ = row
                if not start:
                    continue
                day_num = datetime.fromisoformat(start).day
                totals[day_num] = totals.get(day_num, 0) + duration_from_row(row)
            return totals

        def update_card(key, main_secs, pct_value):
            labels = self.dash_labels[key]
            labels['value'].config(text=fmt_secs(main_secs) if main_secs is not None else "--")
            if pct_value is None:
                labels['pct'].config(text="--")
            else:
                labels['pct'].config(text=f"{pct_value:.1f}%")

        def draw_pie(canvas, key, slices):
            canvas.delete('all')
            total = sum(v for _, v, _ in slices)
            if total <= 0:
                canvas.create_text(75, 75, text="Sem dados", fill="#666", font=('Segoe UI', 10))
                return
            start = 0
            for label, value, tag in slices:
                extent = (value / total) * 360
                canvas.create_arc(10, 10, 140, 140, start=start, extent=extent, fill=tag, outline='#111', width=0.5, tags=('slice', tag))
                start += extent
            # Texto central do maior segmento
            if slices:
                biggest = max(slices, key=lambda x: x[1])
                pct = biggest[1] * 100 / total if total else 0
                canvas.create_text(75, 75, text=f"{biggest[0]}\n{pct:.1f}%", fill='#111', font=('Segoe UI', 9, 'bold'))
            self.pie_data[key] = slices

        def draw_bars(canvas, daily_active, daily_idle):
            canvas.delete('all')
            info_map = {}
            days = sorted(set(daily_active.keys()) | set(daily_idle.keys()))
            if not days:
                canvas.create_text(int(canvas['width'])//2, int(canvas['height'])//2, text="Sem dados", fill="#666", font=('Segoe UI', 10))
                return
            width = canvas.winfo_width() or int(canvas['width']) or 520
            height = canvas.winfo_height() or int(canvas['height']) or 170
            base_y = height - 30
            max_val = max([daily_active.get(d, 0) + daily_idle.get(d, 0) for d in days] + [1])
            usable_height = base_y - 12

            # Dimensionamento horizontal dinâmico para ocupar a largura disponível
            total_width = max(80, width - 32)
            n = len(days)
            gap = 8
            bar_width = (total_width - gap * (n - 1)) / n
            if bar_width < 12:
                bar_width = 12
                gap = max(4, (total_width - bar_width * n) / max(1, n - 1))
            bar_width = min(bar_width, 120)
            used = n * bar_width + (n - 1) * gap
            start_x = (width - used) / 2
            x = start_x
            for day in days:
                act = daily_active.get(day, 0)
                idle_val = daily_idle.get(day, 0)
                total_day = act + idle_val
                scale = usable_height / max_val if max_val else 0
                idle_h = idle_val * scale
                act_h = act * scale
                # idle stacked on top of active
                act_id = canvas.create_rectangle(x, base_y - act_h, x + bar_width, base_y, fill='#0ea36f', outline='', tags=('bar','active'))
                idle_id = canvas.create_rectangle(x, base_y - act_h - idle_h, x + bar_width, base_y - act_h, fill='#e63b3b', outline='', tags=('bar','idle'))
                info_map[act_id] = (day, act, idle_val, 'active')
                info_map[idle_id] = (day, act, idle_val, 'idle')
                if total_day:
                    canvas.create_text(x + bar_width/2, base_y - act_h - idle_h - 10, text=f"{total_day//3600}h", font=('Segoe UI', 8), fill='#111')
                canvas.create_text(x + bar_width/2, base_y + 6, text=str(day), font=('Segoe UI', 8), anchor='n', fill='#111')
                x += bar_width + gap
            self.bar_item_info[canvas] = info_map
            self._bar_data = (daily_active, daily_idle)
            self._bar_drawer = draw_bars

        def update_extra_card(key, seconds_value, percent_value, extra_text=""):
            card = self.dash_labels[key]
            card['value'].config(text=fmt_secs(int(seconds_value)) if seconds_value is not None else "--")
            card['pct'].config(text=(f"{percent_value:.1f}%" if percent_value is not None else "--"))
            card['extra'].config(text=extra_text)

        # Maior pausa (total histórico)
        longest_sec, longest_cat = longest_idle(all_idle)
        total_idle_all = total_seconds(all_idle)
        longest_pct = (longest_sec * 100 / total_idle_all) if total_idle_all and longest_sec else None
        update_extra_card("longest_idle", longest_sec if longest_sec else None, longest_pct, f"Categoria: {longest_cat if longest_cat else '--'}")
        self.top_idle_category = (longest_cat, longest_sec or 0)

        # Médias de inatividade
        day_idle_secs = total_seconds(day_idle)
        day_total = day_idle_secs + total_seconds(day_active)
        day_avg = day_idle_secs  # já é o total do dia
        day_pct = (day_idle_secs * 100 / day_total) if day_total else None
        update_extra_card("avg_day", day_avg, day_pct, "Dia atual")

        week_idle_secs = total_seconds(week_idle)
        week_active_secs = total_seconds(week_active)
        week_total = week_idle_secs + week_active_secs
        days_week = max(1, (now.date() - week_start.date()).days + 1)
        week_avg = week_idle_secs / days_week
        week_pct = (week_idle_secs * 100 / week_total) if week_total else None
        update_extra_card("avg_week", week_avg, week_pct, f"{days_week} dias")

        month_idle_secs = total_seconds(month_idle)
        month_active_secs = total_seconds(month_active)
        month_total = month_idle_secs + month_active_secs
        workdays = self.working_days_in_month_until(now)
        month_avg = month_idle_secs / workdays
        month_pct = (month_idle_secs * 100 / month_total) if month_total else None
        update_extra_card("avg_month", month_avg, month_pct, f"{workdays} dias úteis")

        # Totais e percentuais + visual
        day_active_secs = total_seconds(day_active)
        day_active_pct = (day_active_secs * 100 / day_total) if day_total else None
        day_idle_pct = (day_idle_secs * 100 / day_total) if day_total else None
        update_card("active_day", day_active_secs, day_active_pct)
        update_card("idle_day", day_idle_secs, day_idle_pct)

        week_total = week_active_secs + week_idle_secs
        week_active_pct = (week_active_secs * 100 / week_total) if week_total else None
        week_idle_pct = (week_idle_secs * 100 / week_total) if week_total else None
        update_card("active_week", week_active_secs, week_active_pct)
        update_card("idle_week", week_idle_secs, week_idle_pct)

        month_total = month_active_secs + month_idle_secs
        month_active_pct = (month_active_secs * 100 / month_total) if month_total else None
        month_idle_pct = (month_idle_secs * 100 / month_total) if month_total else None
        update_card("active_month", month_active_secs, month_active_pct)
        update_card("idle_month", month_idle_secs, month_idle_pct)

        # Pies
        dist_today = [("Ativo", day_active_secs, '#0ea36f'), ("Inativo", day_idle_secs, '#e63b3b')]
        dist_week = [("Ativo", week_active_secs, '#0ea36f'), ("Inativo", week_idle_secs, '#e63b3b')]
        dist_month = [("Ativo", month_active_secs, '#0ea36f'), ("Inativo", month_idle_secs, '#e63b3b')]
        draw_pie(self.pie_canvases["hoje"], "hoje", dist_today)
        draw_pie(self.pie_canvases["semana"], "semana", dist_week)
        draw_pie(self.pie_canvases["mês"], "mês", dist_month)

        # Barras (evolução no mês)
        daily_active = aggregate_daily(month_active)
        daily_idle = aggregate_daily(month_idle)
        draw_bars(self.bar_canvas, daily_active, daily_idle)

        # Pies por categoria (idle)
        def aggregate_categories(rows):
            totals = {}
            for _, start, end, _, duration, cat in rows:
                dur = duration
                if dur is None and end and start:
                    dur = int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())
                if dur:
                    key = cat if cat else "Não categorizado"
                    totals[key] = totals.get(key, 0) + dur
            return totals

        cat_pal = ["#e63b3b", "#0ea36f", "#6366f1", "#f59e0b", "#06b6d4", "#9333ea", "#14b8a6", "#ef4444", "#84cc16"]

        def cat_slices(cat_totals):
            if not cat_totals:
                return [("Sem dados", 1, '#e5e7eb')]
            items = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
            slices = []
            for i, (name, secs) in enumerate(items):
                # Garantir cor visível para "Não categorizado"
                if name.lower().startswith('não categorizado'):
                    color = '#9ca3af'
                else:
                    color = cat_pal[i % len(cat_pal)]
                slices.append((name, secs, color))
            return slices

        cat_day = cat_slices(aggregate_categories(day_idle))
        cat_week = cat_slices(aggregate_categories(week_idle))
        cat_month = cat_slices(aggregate_categories(month_idle))
        draw_pie(self.cat_pies["cat_hoje"], "cat_hoje", cat_day)
        draw_pie(self.cat_pies["cat_semana"], "cat_semana", cat_week)
        draw_pie(self.cat_pies["cat_mês"], "cat_mês", cat_month)
    
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
            # run_detached cria o loop interno; não precisa gerenciar thread manual
            self.tray_icon.run_detached()
        if self.tray_icon:
            self.tray_icon.visible = True
        
    def show_window(self, icon=None, item=None):
        # restaurar a partir do ícone (duplo clique no default item)
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_window_visible = True
        self.refresh_all()

    def hide_window(self):
        self.root.withdraw()
        self.is_window_visible = False

    def on_minimize(self, event):
        # Quando minimizar, esconder e ir para bandeja
        if self.root.state() == 'iconic':
            self.ensure_tray_icon()
            self.hide_window()
    
    def on_closing(self):
        result = messagebox.askyesno(
            "Sair",
            "Fechar completamente?\n\nSim = encerrar e parar o monitoramento\nNão = continuar ativo na bandeja"
        )
        if result:
            self.quit_app()
        else:
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
