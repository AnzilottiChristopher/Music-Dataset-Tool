import tkinter as tk
from app.pages.start_page import StartPage
from app.pages.analysis_page import AnalysisPage


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dataset Creation Tool")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")

        # container for pages
        self.container = tk.Frame(self.root, bg="#1e1e1e")
        self.container.pack(fill="both", expand=True)

        # start page
        self.show_start_page()

    def show_start_page(self):
        self.clear_container()
        self.page = StartPage(self.container, on_continue=self.show_analysis_page)
        self.page.pack(fill="both", expand=True)

    def show_analysis_page(self, file_path, folder_path):
        self.clear_container()
        self.page = AnalysisPage(self.container, file_path, folder_path)
        self.page.pack(fill="both", expand=True)

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def run(self):
        print("app is now running")
        self.root.mainloop()