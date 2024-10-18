"""Contains the components needed for simulating the Little Man Computer.

The assembler is used to convert program source code in a string format into
numerical machine code which can be stored in the LMC's mailbox registers. The
interpreter is then used to execute the machine code from these registers.

Typical usage example:

  a = Assembler()
  program = a.assemble('''
    INP
    STA count
    count DAT 0
    HLT
  ''')
  s = Simulator()
  s.load_program(program)
  output = i.step()
"""

class Assembler:
    """Assembler for the Little Man Computer.

    Translates a source program (assembly code) into machine code that can be
    stored in the Little Man Computer's mailbox registers.

    Attributes:
      comment_delimeter:
        The delimeter used to mark comments in the source code.
      instructions:
        A dictionary of assembly mnemonics and corresponding opcodes.
    """

    def __init__(self, comment_delimeter: str = "#") -> None:
        """Initializes the assembler.
        
        Args:
          comment_delimeter:
            The character used to mark text in the source program as a comment.
        """
        self.comment_delimeter = comment_delimeter
        self.instructions = {
            "ADD" : 100,
            "SUB" : 200,
            "STA" : 300,
            "LDA" : 500,
            "BRA" : 600,
            "BRZ" : 700,
            "BRP" : 800,
            "INP" : 901,
            "OUT" : 902,
            "HLT" : 000,
            "DAT" : None
        }

    def _normalise(self, program: str) -> list[str]:
        """Normalise a source program.

        Breaks the source program string into a list of lines of code. Also
        removes tabspaces, trims whitespace, filters out comments. This makes
        the source program ready to be tokenised.
        
        Args:
          program:
            The assembly source program as a string.

        Returns:
          The normalised program as a list of lines of code. For example:

          ['INP',
           'STA count',
           'count DAT 0']
        """
        lines = []
        for line in program.split("\n"):
            # Remove tabspaces
            line = line.replace("\t", " ").strip()
            # Ignore empty or commented lines
            if line == "" or line.startswith(self.comment_delimeter):
                continue
            # Splice off comments at the end of a line
            line = line.split(self.comment_delimeter)[0]
            # Strip whitespace and add line to list
            lines.append(line.strip())
        return lines

    def _tokenise(self, lines: list[str]) -> list[tuple[str, str, str]]:
        """Tokenise a normalised source program.

        Args:
          lines:
            List of normalised lines of assembly code.

        Returns:
          The program tokenised as a list of tuples. Each tuple being an
          assembly label, instruction mnemonic, and operand. For example:

          [('', 'INP', ''),
           ('', 'STA', 'count'),
           ('count', 'DAT', '0')]
        """
        tokenised_lines = []
        for line in lines:
            tokens = line.split()
            label = None
            mnemonic = None
            operand = None
            if len(tokens) == 0:
                continue
            # only mnemonic
            if len(tokens) == 1:
                mnemonic = tokens[0].upper()
            # label & mnemonic -OR- mnemonic & operand
            elif len(tokens) == 2:
                # mnemonic & operand
                if tokens[0].upper() in self.instructions.keys():
                    mnemonic = tokens[0].upper()
                    operand = tokens[1]
                # label & mnemonic
                elif tokens[1].upper() in self.instructions.keys():
                    label = tokens[0]
                    mnemonic = tokens[1].upper()
            # label & mnemonic & operand
            elif len(tokens) == 3:
                label = tokens[0]
                mnemonic = tokens[1].upper()
                operand = tokens[2]
            tokenised_lines.append((label, mnemonic, operand))
        return tokenised_lines
    
    def _unlabel_lines(self, lines: list[tuple[str, str, str]]) -> list[tuple[str, str]]:
        """Convert text labels in the code to mailbox addresses.
        
        Labels that prefix an instruction are removed. Labels that are used as
        an operand are replaced with the corresponding mailbox address for that
        label.

        Args:
          lines:
            List of tokenised lines of assembly code.

        Returns:
          The program with any labels replaced to their corresponding mailbox
          addresses. For example:

          [('INP', ''),
           ('STA', '2'),
           ('DAT', '0')]
        """
        labels = {}
        for mailbox, line in enumerate(lines):          
            label, mnemonic, operand = line
            if label:
                labels[label] = mailbox
        
        unlabelled_lines = []
        for label, mnemonic, operand in lines:
            if operand and not operand.isnumeric() and mnemonic != "DAT":
                operand = str(labels[operand])
            unlabelled_lines.append((mnemonic, operand))
        return unlabelled_lines

    def _generate_machine_code(self, lines: list[tuple[str, str]]) -> list[int]:
        """Convert unlabelled tokenised assembly into numerical machine code.

        Args:
          lines:
            List of unlabelled tokenised lines of assembly code.

        Returns:
          The program as a list of three-digit integers, each an instruction.
          For example:

          [901, 302, 0]
        """
        machine_code = [[] for _ in range(len(lines))]
        for index, (mnemonic, operand) in enumerate(lines):
            if mnemonic == "DAT":
                machine_code[index] = int(operand or 0)
            else:
                opcode = self.instructions[mnemonic]
                instruction = opcode
                if opcode in (100, 200, 300, 500, 600, 700, 800):
                    instruction += int(operand)
                machine_code[index] = instruction
        return machine_code
    
    def assemble(self, program: str) -> list[int]:
        """Convert string source program into numerical machine code.

        Args:
          lines:
            Source program as a single multiline string with new lines
            delimited by a `\n`.

        Returns:
          The program as a list of three-digit integers, each an instruction.
          For example:

          [901, 302, 0]
        """
        # split program into lines, remove tabs & whitespace & comments
        normalised_program = self._normalise(program)
        # tokenise each line of code into (label, mnemonic, operand)
        tokenised_lines = self._tokenise(normalised_program)
        # replace assembly lables with mailbox addresses
        unlabelled_lines = self._unlabel_lines(tokenised_lines)
        # generate machine code by replacing mnemonics with opcodes, and
        # combining opcodes+operands into a single 3 digit value
        return self._generate_machine_code(unlabelled_lines)


class Simulator:
    """Simulator for the Little Man Computer.

    Simulates the LMC's fetch-decode-execute step by step with a given machine
    code program.

    Attributes:
      pc:
        The program counter register.
      acc:
        The accumulator register.
      mailboxes:
        The 100-length list representing the general purpose registers.
      halted:
        Boolean state indicating if the LMC's execution is halted.
      awaiting_input:
        Boolean state indicating if the LMC is awaiting input before continuing
        execution.
    """

    def __init__(self) -> None:
        """Initializes the simulator.
        """
        self.reset()

    def reset(self) -> None:
        """Resets the state of the simulator.

        Resets the registers for the simulator, as well as the `halted` and
        `awaiting_input` flag variables.
        """
        self.pc = 0
        self.acc = 0
        self.mailboxes = [0 for _ in range(100)]
        self.halted = False
        self.awaiting_input = False

    def load_program(self, program: list[int]) -> None:
        """Loads a machine code program into the simulator.

        Loads each numerical machine code instruction into a successive
        register.

        Args:
          program:
            The program as a list of integers, being numerical machine code
            instructions.
        """
        for i in range(min(len(self.mailboxes), len(program))):
            self.mailboxes[i] = program[i]
        self.halted = False

    def load_input(self, value: int) -> None:
        """Loads an input value into the accumulator register.
        
        Args:
          value:
            Integer value to load into the accumulator.
        """
        assert value <= 999, "Value exceeds maximum register size."
        self.acc = int(value)
        self.awaiting_input = False

    def step(self) -> int | None:
        """Performs one simulation step: one fetch, decode, and execute.
        
        Returns:
          The output generated by the instructions execution, or `None` if no
          output.
        """
        if not self.halted:
            # Fetch-decode-execute cycle
            instruction = self._fetch()
            opcode, operand = self._decode(instruction)
            result = self._execute(opcode, operand)
            return result

    def _fetch(self) -> int:
        """Fetch an instruction from the mailboxes, using the program counter.
        
        Returns:
          The instruction in numerical machine code.
        """
        return self.mailboxes[self.pc]

    def _decode(self, instruction: int) -> tuple[int, int]:
        """Decode a given instruction into an opcode and operand.

        Args:
          instruction:
            The numerical machine code instruction to decode.
        
        Returns:
          The decoded opcode and operand in numerical form.
        """
        opcode, operand = divmod(instruction, 100)
        if opcode == 9:
            return opcode * 100 + operand, 0
        return opcode, operand

    def _execute(self, opcode: int, operand: int) -> int | None:
        """Execute a given opcode and operand.
        
        Args:
          opcode:
            The numerical opcode of the instruction.
          operand:
            The numerical operand of the instruction.

        Returns:
          The output generated by the instructions execution, or `None` if no
          output.
        """
        self.pc += 1
        result = None
        # 000 = Halt
        if opcode == 0:
            self.halted = True
        # 1xx = Add
        elif opcode == 1:
            self.acc += self.mailboxes[operand]
        # 2xx = Subtract
        elif opcode == 2:
            self.acc -= self.mailboxes[operand]
        # 3xx = Store
        elif opcode == 3:
            self.mailboxes[operand] = self.acc
        # 5xx = Load
        elif opcode == 5:
            self.acc = self.mailboxes[operand]
        # 6xx = Branch (always)
        elif opcode == 6:
            self.pc = operand
        # 7xx = Branch (if zero)
        elif opcode == 7:
            if self.acc == 0:
                self.pc = operand
        # 8xx = Branch (if positive)
        elif opcode == 8:
            if self.acc >= 0:
                self.pc = operand
        # 901 = Input
        elif opcode == 901:
            self.awaiting_input = True
            self.acc = 0
        # 902 = Output
        elif opcode == 902:
            result = self.acc
        return result
