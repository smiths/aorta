import tkinter.filedialog
import tkinter as tk


class Aorta_Starter_frame(object):
    def __init__(self, master, **kwargs):
        frame = tk.Frame(master, width=400, height=200)
        folder_label = tk.Label(frame, text="Please select folder to start")
        folder_label.bind(
            '<Button-1>',
            lambda event: self.get_source_folder()
        )
        folder_label.place(relx=0.5, rely=0.5, anchor="center")
        self.directory = ""
        canvas = tk.Canvas(
            frame,
            bg="#FFFFFF",
            height=720,
            width=1280,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )

        # canvas.place(x = 0, y = 0)
        canvas.create_text(
            400.0,
            185.0,
            anchor="nw",
            text="Aorta GeomRecon",
            fill="#084A41",
            font=("Inter", 64 * -1)
        )
        canvas.create_text(
            1032.0,
            668.0,
            anchor="nw",
            text="@copyrightMcMaster2022",
            fill="#084A41",
            font=("Inter", 16 * -1)
        )

        canvas.pack()
        frame.pack()
        # folder_label.pack()

    def get_source_folder(self):
        self.directory = tk.filedialog.askdirectory()
        print(self.directory)


if __name__ == "__main__":
    display_module_root = tk.Tk()
    display_module_root.title("Aorta GeomRecon")
    display_module_root.config(height=720, width=1280)
    first_frame = Aorta_Starter_frame(display_module_root)
    display_module_root.mainloop()
