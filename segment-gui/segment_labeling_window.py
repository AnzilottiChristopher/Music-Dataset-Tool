import tkinter as tk
from app.pages.segment_start_page import SegmentStartPage
from app.pages.segment_labeling_page import SegmentLabelingPage

class SegmentLabelingWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Song Segment Labeling Tool")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e")
        
        # Make window resizable
        self.root.minsize(800, 600)
        
        # Container for pages
        self.container = tk.Frame(self.root, bg="#1e1e1e")
        self.container.pack(fill="both", expand=True)
        
        # Start with the start page
        self.show_start_page()
    
    def show_start_page(self):
        """Display the start page"""
        self.clear_container()
        self.page = SegmentStartPage(self.container, on_continue=self.show_labeling_page)
        self.page.pack(fill="both", expand=True)
    
    def show_labeling_page(self, file_path, folder_path, output_json_path=None):
        """Display the segment labeling page"""
        self.clear_container()
        self.page = SegmentLabelingPage(
            self.container, 
            file_path, 
            folder_path,
            output_json_path=output_json_path,
            on_complete=self.on_labeling_complete
        )
        self.page.pack(fill="both", expand=True)
    
    def on_labeling_complete(self, segmented_json_path):
        """Handle completion of labeling"""
        # Could return to start page or show a completion screen
        self.show_completion_screen(segmented_json_path)
    
    def show_completion_screen(self, json_path):
        """Show a completion screen"""
        self.clear_container()
        
        completion_frame = tk.Frame(self.container, bg="#1e1e1e")
        completion_frame.pack(fill="both", expand=True)
        
        tk.Label(
            completion_frame,
            text="✓ Labeling Complete!",
            font=("Helvetica", 24, "bold"),
            bg="#1e1e1e",
            fg="#27ae60"
        ).pack(pady=50)
        
        tk.Label(
            completion_frame,
            text=f"Segmented data saved to:",
            font=("Helvetica", 12),
            bg="#1e1e1e",
            fg="white"
        ).pack(pady=10)
        
        tk.Label(
            completion_frame,
            text=str(json_path),
            font=("Helvetica", 10),
            bg="#1e1e1e",
            fg="#5ad",
            wraplength=600
        ).pack(pady=5)
        
        button_frame = tk.Frame(completion_frame, bg="#1e1e1e")
        button_frame.pack(pady=40)
        
        tk.Button(
            button_frame,
            text="Start New Session",
            command=self.show_start_page,
            bg="#3498db",
            fg="white",
            font=("Helvetica", 12),
            padx=20,
            pady=10
        ).pack(side="left", padx=10)
        
        tk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit,
            bg="#e74c3c",
            fg="white",
            font=("Helvetica", 12),
            padx=20,
            pady=10
        ).pack(side="left", padx=10)
    
    def clear_container(self):
        """Clear all widgets from the container"""
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def run(self):
        """Run the application"""
        print("Segment Labeling Tool is now running")
        self.root.mainloop()


def main():
    """Main entry point for the application"""
    app = SegmentLabelingWindow()
    app.run()


if __name__ == "__main__":
    main()