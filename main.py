import sys
import os
from datetime import datetime

if __name__ == "__main__":
    from gui import ActivityTrackerGUI
    
    try:
        app = ActivityTrackerGUI()
        app.run()
    except Exception as e:
        import traceback
        base_dir = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        log_dir = os.path.join(base_dir, "TempoInativo")
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_dir, f"error_log_{ts}.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("Erro ao iniciar aplicação:\n")
            f.write(traceback.format_exc())
        print(f"Erro: {e}")
        print(f"Detalhes salvos em {log_path}")
        input("Pressione Enter para sair...")
