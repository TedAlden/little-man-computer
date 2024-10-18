import tkinter as tk

from tkinter import simpledialog
from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font
from lmc import Assembler, Simulator


EDITOR_TAB_SIZE = 4


class MenuBar(tk.Menu):

    def __init__(self, root, master):
        super().__init__(master)
        self.root = root
        # Create main menu cascades (dropdowns)
        self.file_menu = tk.Menu(self)
        # Add options to each cascade
        self.file_menu.add_command(label="Exit", command=self.btn_exit)
        # Add each cascade to the menu bar
        self.add_cascade(label="File", menu=self.file_menu)

    def btn_exit(self):
        self.root.destroy()


class CodeEditorFrame(tk.Frame):

    def __init__(self, root, master):
        self.root = root
        super().__init__(master)
        self.wrapper = tk.LabelFrame(master, padx=5, pady=5, text="Code Editor")
        self.wrapper.pack(fill="both", expand=True)
        self.program_code = ScrolledText(self.wrapper, undo=True, tabs=True, )
        self.program_code.pack(fill="both", expand=True)
        # Configure tabspacing in the editor
        font = Font(font=self.program_code["font"])
        tab_width = font.measure(" " * EDITOR_TAB_SIZE)
        self.program_code.config(tabs=tab_width)

    def get_code(self):
        return self.program_code.get("1.0", "end")


class SimulationControlsFrame(tk.Frame):

    def __init__(self, root, master):
        self.root = root
        super().__init__(master)
        self.wrapper = tk.LabelFrame(master, padx=5, pady=5, text="Controls")
        self.wrapper.pack(fill="x")
        self.btn_reset = tk.Button(self.wrapper, text="Reset", command=self.btn_reset)
        self.btn_reset.pack()
        self.btn_load_program = tk.Button(self.wrapper, text="Load", command=self.btn_load)
        self.btn_load_program.pack()
        self.btn_step_program = tk.Button(self.wrapper, text="Step", command=self.btn_step)
        self.btn_step_program.pack()

    def btn_reset(self):
        # Clear output
        self.root.output.clear()
        # Reset LMC model
        self.root.lmc.reset()
        # Clear register labels
        self.root.registers.update()
        self.root.mailboxes.update()
        # Stop autoplay
        self.root.autoplay.cancel()

    def btn_load(self):
        program = self.root.editor.get_code()
        # Assemble code into LMC
        assembled_code = self.root.assembler.assemble(program)
        self.root.lmc.load_program(assembled_code)
        # Update visual component for mailboxes
        self.root.mailboxes.update()

    def btn_step(self):
        # Step does nothing if LMC is not running
        if self.root.lmc.halted:
            return
        # Perform one FDE cycle/step in the LMC     
        output = self.root.lmc.step()
        # Print any output
        if output is not None:
            self.root.output.append(output)
        # Ask user for input if needed
        if self.root.lmc.awaiting_input:
            user_input = self._ask_user_input() or 0  # 0 if empty input
            self.root.lmc.load_input(user_input)
        # Update visual components for registers and mailboxes
        self.root.registers.update()
        self.root.mailboxes.update()
        # Check if machine is halted, AFTER the step has been done
        if self.root.lmc.halted:
            self.root.output.append("---- HALTED ----")

    def _ask_user_input(self):
        return simpledialog.askinteger(title="Input", prompt="Enter an input value:")


class AutoPlayFrame(tk.Frame):

    def __init__(self, root, master):
        self.root = root
        self.playing = False
        super().__init__(master)
        self.wrapper = tk.LabelFrame(master, padx=5, pady=5, text="Autoplay")
        self.wrapper.pack(fill="both")
        self.btn_play = tk.Button(self.wrapper, text="Play", command=self.btn_play)
        self.btn_play.pack()
        self.btn_pause = tk.Button(self.wrapper, text="Pause", command=self.btn_pause)
        self.btn_pause.pack()
        self.scl_speed = tk.Scale(self.wrapper, from_=1, to_=100, orient="horizontal")
        self.scl_speed.pack()
        self.scl_speed.set(5)

    def tick(self):
        if self.playing:
            # Step the simulation
            self.root.controls.btn_step()
            if self.root.lmc.halted:
                self.cancel()
            # Set delay before next step plays
            update_rate = int(self.scl_speed.get())
            update_period = 1000 // update_rate
            self.after(update_period, self.tick)

    def cancel(self):
        self.playing = False

    def btn_play(self):
        # Prevent several autoplay 'schedules' from running at once
        if not self.playing:
            self.playing = True
            self.tick()

    def btn_pause(self):
        self.cancel()


class RegistersFrame(tk.Frame):
    
    def __init__(self, root, master):
        super().__init__(master)
        self.root = root
        self.wrapper = tk.LabelFrame(master, padx=5, pady=5, text="Registers")
        self.wrapper.pack(fill="x")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        # Program Counter
        self.pc = tk.StringVar()
        self.label_pc = tk.Label(self.wrapper, text="PC:")
        self.label_pc.grid(row=0, column=0, sticky="e")
        self.entry_pc = tk.Entry(self.wrapper, width=6, state="disabled", textvariable=self.pc)
        self.entry_pc.grid(row=0, column=1)
        # Accumulator
        self.acc = tk.StringVar()
        self.label_acc = tk.Label(self.wrapper, text="ACC:")
        self.label_acc.grid(row=4, column=0, sticky="e")
        self.entry_acc = tk.Entry(self.wrapper, width=6, state="disabled", textvariable=self.acc)
        self.entry_acc.grid(row=4, column=1)
        # Initialise
        self.update()

    def update(self):
        self.pc.set(self.root.lmc.pc)
        self.acc.set(self.root.lmc.acc)


class MailboxesFrame(tk.Frame):
     
    def __init__(self, root, master):
        super().__init__(master)
        self.root = root
        self.wrapper = tk.LabelFrame(master, padx=5, pady=5, text="Mailboxes")
        self.wrapper.pack(fill="both", expand=True)
        self.entries = []
        self.vars = []
        for i in range(100):
            row, col = divmod(i, 10)
            var = tk.StringVar(value="000")
            entry = tk.Entry(self.wrapper, width=4, state="disabled", textvariable=var)
            entry.grid(row=row, column=col)
            self.entries.append(entry)
            self.vars.append(var)

    def update(self):
        for i in range(len(self.vars)):
            self.vars[i].set(str(self.root.lmc.mailboxes[i]).zfill(3))


class SimulationOutputFrame(tk.Frame):

    def __init__(self, root, master):
        self.root = root
        super().__init__(master)
        self.wrapper = tk.LabelFrame(master, padx=5, pady=5, text="Output")
        self.wrapper.pack(fill="both", expand=True)
        self.program_output = ScrolledText(self.wrapper, state="disabled")
        self.program_output.pack(side=tk.BOTTOM, fill="both", expand=True)

    def append(self, output):
        self.program_output.configure(state="normal")
        self.program_output.insert("end", str(output) + "\n")
        self.program_output.configure(state="disabled")
        self.program_output.update()

    def clear(self):
        self.program_output.configure(state="normal")
        self.program_output.delete('1.0', "end")
        self.program_output.configure(state="disabled")


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        # LMC Model
        self.assembler = Assembler()
        self.lmc = Simulator()
        # Main window configuration
        self.title("Little Man Computer")
        self.geometry("800x500")
        # Create menu bar
        self.root_menu = MenuBar(self, self)
        self.config(menu=self.root_menu)
        # Create three padded column frames
        self.left_col = tk.Frame(self, padx=5, pady=5)
        self.left_col.grid(column=0, row=0, sticky="ewsn")
        self.middle_col = tk.Frame(self, padx=5, pady=5, width=100)
        self.middle_col.grid(column=1, row=0, sticky="ewsn")
        self.right_col = tk.Frame(self, padx=5, pady=5)
        self.right_col.grid(column=2, row=0, sticky="ewsn")
        # Configure three column layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # Create widget frames
        self.editor = CodeEditorFrame(self, self.left_col)
        self.controls = SimulationControlsFrame(self, self.middle_col)
        self.autoplay = AutoPlayFrame(self, self.middle_col)
        self.registers = RegistersFrame(self, self.middle_col)
        self.mailboxes = MailboxesFrame(self, self.right_col)
        self.output = SimulationOutputFrame(self, self.right_col)


def main():
    # Create and run TKinter GUI window
    win = MainWindow()
    win.mainloop()


if __name__ == "__main__":
    main()
