"""A command line interface for running LMC assembly programs.

This module should be run via the command line with the first argument being
the path to the source program file to be simulated.

Typical usage example:

  $ python cli.py --help
  $ python cli.py ../programs/countdown.asm
"""

import argparse

from lmc import Assembler, Simulator
from pathlib import Path


def main():
    # CLI argument parser
    parser = argparse.ArgumentParser(description="LMC Simulator.")
    parser.add_argument("path", type=str, help="path to LMC source program.")
    args = parser.parse_args()

    # Attempt to resolve the path
    program_path = Path(args.path).resolve()
    if not program_path.exists():
        print("The source file doesn't exist.")
        raise SystemExit(1)

    # Read the program source code from the file
    program_text = ""
    with open(program_path, "r") as f:
        program_text = f.read()

    # Assemble program source code into machine code
    asm = Assembler()
    program = asm.assemble(program_text)

    # Load machine code into the interpreter
    sim = Simulator()
    sim.load_program(program)

    # Run the interpreter
    while not sim.halted:
        output = sim.step()
        if output is not None:
            print(output)
        if sim.awaiting_input:
            x = int(input("INPUT> "))
            sim.load_input(x)
        if sim.halted:
            print("---- HALTED ----")


if __name__ == "__main__":
    main()
