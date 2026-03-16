import sys
import os

if __name__ == "__main__":
    from gui import ActivityTrackerGUI
    
    try:
        app = ActivityTrackerGUI()
        app.run()
    except Exception as e:
        import traceback
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"Erro ao iniciar aplicação:\n")
            f.write(traceback.format_exc())
        print(f"Erro: {e}")
        print("Detalhes salvos em error_log.txt")
        input("Pressione Enter para sair...")
