import sys
from tkinter import *
from tkinter.messagebox import askyesno, showwarning
import numpy as np


class Checkbar(Frame):
    def __init__(self, parent=None, picks=[], side=LEFT, anchor=W):
        super().__init__(parent)
        self.vars = []
        for pick in picks:
            var = BooleanVar(value=True)
            chk = Checkbutton(self, text=pick, variable=var)
            chk.pack(side=side, anchor=anchor, expand=YES)
            self.vars.append(var)

    def state(self):
        return map(lambda var: var.get(), self.vars)


class ParameterPicker:
    def __init__(self):
        self.GMM_parameters = [
            "graphene/90nm/20x",
            "wse2/70nm/20x",
            "tas2/90nm/20x",
            "hbn/90nm/20x",
        ]

        self.user_closed = False
        self.scan_save_directory = "C://path/to/the/save/directory"
        self.serverURL = "http://localhost:4999/upload"
        self.scan_name = ""
        self.scan_user = ""
        self.scan_magnification = None
        self.scan_exfoliated_material = None
        self.scan_chip_thickness = None
        self.scan_comment = ""
        self.size_threshold = "400"
        self.standard_deviation_threshold = "5"
        self.used_channels = [True, True, True]
        self.use_auto_AF = True

        self.__create_parameter_picker()

    def __create_input(self, label_text, entry_text, grid_row):
        label = Label(self.parameter_picker, text=label_text)
        label.grid(row=grid_row, column=0, padx=10)
        entry = Entry(self.parameter_picker, width=50, borderwidth=5)
        entry.insert(0, entry_text)
        entry.grid(row=grid_row, column=1, sticky="ew", padx=10)
        return entry

    def __create_dropdown(self, options, grid_row):
        parameter = StringVar()
        parameter.set(options[0])
        dropdown = OptionMenu(self.parameter_picker, parameter, *options)
        label = Label(self.parameter_picker, text="Used Parameters")
        label.grid(row=grid_row, column=0)
        dropdown.grid(row=grid_row, column=1, sticky="ew", padx=10)
        return parameter

    def __create_heading(self, title, grid_row):
        heading = Label(self.parameter_picker, text=title)
        heading.grid(row=grid_row, columnspan=2, sticky="e", padx=10, pady=10)
        return heading

    def __create_start_button(self, grid_row):
        button = Button(
            self.parameter_picker,
            text="START SCAN",
            height=4,
            command=self.validate_input,
        )
        button.grid(row=grid_row, columnspan=2, sticky="ew", padx=10, pady=10)
        return button

    def __create_checkboxes(self, grid_row):
        label = Label(self.parameter_picker, text="Used Channels")
        checkboxes = Checkbar(self.parameter_picker, ["Blue", "Green", "Red"])
        label.grid(row=grid_row, column=0, padx=10)
        checkboxes.grid(row=grid_row, column=1, sticky="ew", padx=10)
        return checkboxes

    def __create_checkbox(self, label_text, state: bool, grid_row):
        label = Label(self.parameter_picker, text=label_text)
        var = BooleanVar(value=state)
        checkbox = Checkbutton(self.parameter_picker, variable=var)
        label.grid(row=grid_row, column=0, padx=10)
        checkbox.grid(row=grid_row, column=1, sticky="w", padx=10)
        return var

    def __create_parameter_picker(self):
        self.parameter_picker = Tk()

        self.parameter_picker.protocol("WM_DELETE_WINDOW", self.on_close)
        self.parameter_picker.title("Automated 2D Material System")
        self.parameter_picker.grid_columnconfigure((0, 1), weight=1)
        self.parameter_picker.resizable(0, 0)

        ############################ Scan Parameters ############################
        grid_row = 1
        self.__create_heading("Scan Parameters", grid_row)

        grid_row += 1
        self.input_scan_name = self.__create_input(
            "Scan Name", self.scan_name, grid_row
        )

        grid_row += 1
        self.input_scan_user = self.__create_input(
            "Scan User", self.scan_user, grid_row
        )

        grid_row += 1
        self.var_GMM_parameters = self.__create_dropdown(self.GMM_parameters, grid_row)

        ############################ Filter Parameters ############################
        grid_row += 1
        self.__create_heading("Filter Parameters", grid_row)

        grid_row += 1
        self.input_standard_deviation_threshold = self.__create_input(
            "Standard Deviation Threshold", self.standard_deviation_threshold, grid_row
        )

        grid_row += 1
        self.input_size_threshold = self.__create_input(
            "Size Threshold in μm²", self.size_threshold, grid_row
        )

        ############################ ETC Parameters ############################
        grid_row += 1
        self.__create_heading("ETC Parameters", grid_row)

        grid_row += 1
        self.checkbox_autofocus = self.__create_checkbox(
            "Automatic AF Calibration [Experimental]", self.use_auto_AF, grid_row
        )

        grid_row += 1
        self.channel_picker = self.__create_checkboxes(grid_row)

        grid_row += 1
        self.input_comment = self.__create_input("Comment", self.scan_comment, grid_row)

        grid_row += 1
        self.input_serverURL = self.__create_input(
            "Server URL", self.serverURL, grid_row
        )

        grid_row += 1
        self.input_image_dir = self.__create_input(
            "Image Directory", self.scan_save_directory, grid_row
        )

        grid_row += 1
        self.start_button = self.__create_start_button(grid_row)

    def on_close(self):
        self.user_closed = True
        self.parameter_picker.destroy()

    def validate_input(self):
        used_GMM_parameters = self.var_GMM_parameters.get().strip().split("/")
        self.scan_exfoliated_material = used_GMM_parameters[0]
        self.chip_thickness = used_GMM_parameters[1]
        self.scan_magnification = int(used_GMM_parameters[2][:-1])

        self.scan_name = self.input_scan_name.get().strip()
        self.scan_user = self.input_scan_user.get().lower().strip()
        self.size_threshold = self.input_size_threshold.get()
        self.standard_deviation_threshold = (
            self.input_standard_deviation_threshold.get()
        )
        self.scan_save_directory = self.input_image_dir.get().strip().replace("\\", "/")
        self.scan_comment = self.input_comment.get().strip().lower()
        self.serverURL = self.input_serverURL.get()
        self.use_auto_AF = self.checkbox_autofocus.get()
        self.used_channels = [
            i for i, channel in enumerate(list(self.channel_picker.state())) if channel
        ]
        self.used_channels = "".join(np.array(["B", "G", "R"])[self.used_channels])

        if len(self.used_channels) < 2:
            showwarning(
                title="Value Error",
                message="You cant use less than 2 channels for the detection!",
            )

        if self.scan_name == "" or self.scan_user == "":
            showwarning(
                title="Null Error",
                message="You need to specify a Scan User and Scan Name!",
            )
            return

        if self.scan_save_directory is None or self.scan_save_directory == "":
            showwarning(
                title="Null Error",
                message="You need to pick an Image Directory where to save the Scan!",
            )
            return

        try:
            self.size_threshold = float(self.size_threshold)
            self.standard_deviation_threshold = float(self.standard_deviation_threshold)
        except ValueError:
            showwarning(
                title="Type Error",
                message="Size and Standard Deviation Threshold need to be floating-point numbers or integers, not strings!",
            )
            return

        text_string = (
            f"Start the Scan with the following Parameters?\n"
            "\n--- Scan Parameters ---\n"
            f"Current User : {self.scan_user}\n"
            f"Scan Name : {self.scan_name}\n"
            f"Scan Magnification : {self.scan_magnification}\n"
            f"Exfoliated Material : {self.scan_exfoliated_material}\n"
            f"Chip Thickness : {self.chip_thickness}\n"
            "\n--- Filter Parameters ---\n"
            f"Standard Deviation Threshold : {self.standard_deviation_threshold}\n"
            f"Size Threshold : {self.size_threshold}\n"
            "\n--- Etc Parameters ---\n"
            f"Image Directory : {self.scan_save_directory}\n"
            f"Used Channels : {self.used_channels}\n"
            f"Server URL : {self.serverURL}\n"
            f"Comment : {self.scan_comment}\n"
        )

        answer = askyesno("Validation", text_string)

        if answer == 1:
            self.parameter_picker.destroy()
        else:
            return

    def take_input(self):
        mainloop()

        if self.user_closed:
            raise RuntimeError("Closed by User")

        return {
            "image_directory": self.scan_save_directory,
            "server_url": self.serverURL,
            "scan_user": self.scan_user,
            "scan_name": self.scan_name,
            "scan_exfoliated_material": self.scan_exfoliated_material,
            "scan_comment": self.scan_comment,
            "chip_thickness": self.chip_thickness,
            "size_threshold": self.size_threshold,
            "scan_magnification": int(self.scan_magnification),
            "used_channels": self.used_channels,
            "standard_deviation_threshold": self.standard_deviation_threshold,
            "use_auto_AF": bool(self.use_auto_AF),
        }


if __name__ == "__main__":
    mygui = ParameterPicker()
    try:
        input_dict = mygui.take_input()
    except RuntimeError:
        sys.exit(0)

    for item in input_dict.items():
        print(item)
