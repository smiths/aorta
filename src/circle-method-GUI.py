from tkinter import Tk
from tkinter import Label
from tkinter import Button
from tkinter import Entry
from tkinter import ttk
# from tkinter.ttk import Progressbar
from tkinter import filedialog
from os import path
# import SimpleITK as sitk


root = Tk()
root.title("GeomRecon")
root.geometry('500x500')

# all positions
# Section input file path
file_label_pos = (200, 5)
input_path_pos = (0, 0)

# Section Inputs
crap_sep_pos = (0, 40)
crapped_label_pos = (0, crap_sep_pos[1] + 5)
index_pos_x = 60
x_pos_y = crapped_label_pos[1] + 35
y_pos_y = x_pos_y + 20
z_pos_y = y_pos_y + 20
label_size_pos_x = index_pos_x*2
label_pos_x = label_size_pos_x + 60

# SITK show command
sitk_show_pos = (label_pos_x + 60, x_pos_y)


inputpath = Label(root, text="dicoms file path")
inputpath.place(x=file_label_pos[0], y=file_label_pos[1])

dicoms_path = "."


def askinput(): 
    dicoms_path = filedialog.askdirectory(initialdir=path.dirname(__file__))
    inputpath.configure(text=dicoms_path)
    print(dicoms_path)


btn = Button(root, text="Click to choose your input folder",
             command=askinput)
btn.place(x=0, y=5)

#############################################################################

separator = ttk.Separator(root, orient='horizontal')
separator.place(x=crap_sep_pos[0], y=crap_sep_pos[1], relwidth=1)

crapped_label = Label(root, text="Crapped images inputs")
crapped_label.place(x=crapped_label_pos[0], y=crapped_label_pos[1])

X_label = Label(root, text="X index")
X_label.place(x=0, y=x_pos_y)
X_index = Entry(root, width=5)
X_index.place(x=index_pos_x, y=x_pos_y)

Y_label = Label(root, text="Y index")
Y_label.place(x=0, y=y_pos_y)
Y_index = Entry(root, width=5)
Y_index.place(x=index_pos_x, y=y_pos_y)

Z_label = Label(root, text="Z index")
Z_label.place(x=0, y=z_pos_y)
Z_index = Entry(root, width=5)
Z_index.place(x=index_pos_x, y=z_pos_y)


#############################################################################


X_size_label = Label(root, text="X sizes")
X_size_label.place(x=label_size_pos_x, y=x_pos_y)
X_size = Entry(root, width=5)
X_size.place(x=label_pos_x, y=x_pos_y)

Y_size_label = Label(root, text="Y sizes")
Y_size_label.place(x=label_size_pos_x, y=y_pos_y)
Y_size = Entry(root, width=5)
Y_size.place(x=label_pos_x, y=y_pos_y)

Z_size_label = Label(root, text="Z sizes")
Z_size_label.place(x=label_size_pos_x, y=z_pos_y)
Z_size = Entry(root, width=5)
Z_size.place(x=label_pos_x, y=z_pos_y)

#############################################################################


def sitk_show():
    pass


sitk_btn = Button(root, text="Click to use SITK see the CT scan",
                  command=sitk_show)
sitk_btn.place(x=sitk_show_pos[0], y=sitk_show_pos[1])

root.mainloop()