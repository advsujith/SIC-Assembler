import tkinter as tk
from tkinter import scrolledtext

class AssemblerGUI2(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Assembler")
        self.geometry("800x600")

        self.input_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.input_area.insert(tk.INSERT, "Input Code")
        self.input_area.grid(row=0, column=0)
        
        self.optab_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.optab_area.insert(tk.INSERT, "Optab")
        self.optab_area.grid(row=0, column=1)

        self.intermediate_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.intermediate_area.insert(tk.INSERT, "Intermediate File")
        self.intermediate_area.grid(row=1, column=0)

        self.symtab_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.symtab_area.insert(tk.INSERT, "Symtab")
        self.symtab_area.grid(row=1, column=1)

        self.output_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.output_area.insert(tk.INSERT, "Output File")
        self.output_area.grid(row=2, column=0)

        self.objcode_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.objcode_area.insert(tk.INSERT, "Object Code")
        self.objcode_area.grid(row=2, column=1)

        self.generate_button = tk.Button(self, text="Generate", command=self.generate)
        self.generate_button.grid(row=3, column=0, columnspan=2)

    def generate(self):
        input_code = self.input_area.get("1.0", tk.END)
        optab_text = self.optab_area.get("1.0", tk.END)

        optab = self.parse_optab(optab_text)
        assembler = Assembler(optab)

        assembler.pass1(input_code)
        assembler.pass2()

        self.intermediate_area.delete("1.0", tk.END)
        self.intermediate_area.insert(tk.INSERT, assembler.get_intermediate_file())

        self.symtab_area.delete("1.0", tk.END)
        self.symtab_area.insert(tk.INSERT, assembler.get_symtab())

        self.output_area.delete("1.0", tk.END)
        self.output_area.insert(tk.INSERT, assembler.get_output_file())

        self.objcode_area.delete("1.0", tk.END)
        self.objcode_area.insert(tk.INSERT, assembler.get_object_code())

    def parse_optab(self, optab_text):
        optab = {}
        lines = optab_text.split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) == 2:
                optab[parts[0]] = parts[1]
        return optab

class Assembler:
    def __init__(self, optab):
        self.optab = optab
        self.symtab = {}
        self.intermediate_file = []
        self.output_file = []
        self.object_code = []
        self.locctr = 0

    def pass1(self, input_code):
        lines = input_code.split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) == 3:
                if parts[1] == "START":
                    self.locctr = int(parts[2], 16)
                    self.intermediate_file.append(f"-\t{line}")
                else:
                    self.process_line_pass1(parts)
            elif len(parts) == 2:
                self.process_line_pass1(parts)

    def process_line_pass1(self, parts):
        label = parts[0]
        opcode = parts[1]
        operand = parts[2] if len(parts) == 3 else ""

        if label != "-":
            self.symtab[label] = hex(self.locctr)[2:]

        self.intermediate_file.append(f"{hex(self.locctr)[2:]}\t{label}\t{opcode}\t{operand}")

        if opcode in self.optab:
            self.locctr += 3
        elif opcode == "WORD":
            self.locctr += 3
        elif opcode == "RESW":
            self.locctr += 3 * int(operand)
        elif opcode == "RESB":
            self.locctr += int(operand)
        elif opcode == "BYTE":
            self.locctr += len(operand) - 3

    def pass2(self):
        self.generate_output_file()
        self.generate_object_code()

    def generate_output_file(self):
        lines = self.intermediate_file
        for line in lines:
            parts = line.split()
            if len(parts) == 4:
                self.process_line_pass2(parts)
            elif len(parts) == 3:
                self.process_line_pass2(parts)

    def process_line_pass2(self, parts):
        address = parts[0]
        label = parts[1]
        opcode = parts[2]
        operand = parts[3] if len(parts) == 4 else ""

        obj_code = ""
        if opcode in self.optab:
            obj_code = self.optab[opcode]
            if operand in self.symtab:
                obj_code += self.symtab[operand]
            else:
                obj_code += "0000"
        elif opcode == "BYTE":
            obj_code = operand[2:-1]
        elif opcode == "WORD":
            obj_code = f"{int(operand):06X}"

        self.output_file.append(f"{address}\t{label}\t{opcode}\t{operand}\t{obj_code}")

    def generate_object_code(self):
        start_address = 0
        length = 0
        count = 0
        lines = self.intermediate_file
        for line in lines:
            parts = line.split()
            if len(parts) == 4:
                loc, label, opcode, operand = parts
                if opcode == "START":
                    start_address = int(operand, 16)
                elif opcode == "BYTE":
                    count += len(operand) - 3
                elif opcode not in ["START", "END", "RESW", "RESB"]:
                    count += 3

        end_address = int(lines[-1].split()[0], 16)
        length = end_address - start_address

        self.object_code.append(f"H^{lines[0].split()[1]}^00{lines[0].split()[3]}^0000{length:06X}")
        self.object_code.append(f"T^00{lines[0].split()[3]}^{count:02X}^")

        text_record = ""
        
        for line in lines:
            parts = line.split()
            if len(parts) == 4:
                loc, label, opcode, operand = parts
                if opcode in ["START", "END", "RESW", "RESB"]:
                    continue
                elif opcode in self.optab:
                    obj_code = self.optab[opcode]
                    if operand in self.symtab:
                        obj_code += self.symtab[operand]
                    else:
                        obj_code += "0000"
                    text_record += f"{obj_code}^"
                elif opcode == "WORD":
                    text_record += f"{int(operand):06X}^"
                elif opcode == "BYTE":
                    byte_code = ''.join(format(ord(c), 'X') for c in operand[2:-1])
                    text_record += f"{byte_code}^"
        
        self.object_code.append(text_record.rstrip('^'))
        self.object_code.append(f"E^00{format(start_address, '06X')}")

    def get_intermediate_file(self):
        return "\n".join(self.intermediate_file)

    def get_symtab(self):
        return "\n".join(f"{k}\t{v}\t0" for k, v in self.symtab.items())

    def get_output_file(self):
        return "\n".join(self.output_file)

    def get_object_code(self):
        return "\n".join(self.object_code)

if __name__ == "__main__":
    app = AssemblerGUI2()
    app.mainloop()