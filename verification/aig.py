# -*- coding: utf-8 -*-

# Copyright (C) 2017, Maximilian Köhl <mail@koehlma.de>


def _literal(string):
    literal = int(string)
    if literal == 1:
        return True
    elif literal == 0:
        return False
    return -(literal // 2) if literal & 1 else literal // 2


class Signal:
    def __init__(self, literal, name=None):
        self.literal = literal
        self.name = name

    def __str__(self):
        kind = self.__class__.__name__
        return '<{} {} name="{}">'.format(kind, self.literal, self.name or '')


class Input(Signal):
    pass


class Output(Signal):
    pass


class Latch(Signal):
    def __init__(self, literal, successor, name=None):
        super().__init__(literal, name)
        self.successor = successor


class And(Signal):
    def __init__(self, literal, left, right, name=None):
        super().__init__(literal, name)
        self.left = left
        self.right = right


class AIG:
    def __init__(self, inputs, latches, outputs, ands, variables, comments):
        self.inputs = inputs
        self.latches = latches
        self.outputs = outputs
        self.ands = ands
        self.variables = variables
        self.comments = comments

    @classmethod
    def from_file(cls, filename: str):
        """ Read a file in the AIGER ASCII format and returns an AIG. """
        with open(filename, 'rt') as file:
            magic, *numbers = file.readline().split()
            assert magic == 'aag'
            max_var, num_ins, num_latches, num_outs, num_ands = map(int, numbers)

            variables = {}

            inputs = []
            for _ in range(num_ins):
                input = Input(_literal(file.readline().strip()))
                variables[abs(input.literal)] = input
                inputs.append(input)

            latches = []
            for _ in range(num_latches):
                literal, successor = map(_literal, file.readline().split())
                latch = Latch(literal, successor)
                variables[abs(latch.literal)] = latch
                latches.append(latch)

            outputs = []
            for _ in range(num_outs):
                outputs.append(Output(_literal(file.readline().strip())))

            ands = []
            for _ in range(num_ands):
                literal, left, right = map(_literal, file.readline().split())
                gate = And(literal, left, right)
                variables[abs(gate.literal)] = gate
                ands.append(gate)

            for line in file:
                if line.strip() == 'c':
                    break
                if line[0] in {'i', 'l', 'o'}:
                    position, _, name = line[1:].partition(' ')
                    index = int(position)
                    name = name.strip()
                    if line[0] == 'i':
                        inputs[index].name = name
                    elif line[0] == 'l':
                        latches[index].name = name
                    elif line[0] == 'o':
                        outputs[index].name = name

            comments = file.readlines()

            return cls(inputs, latches, outputs, ands, variables, comments)
