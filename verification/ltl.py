# -*- coding: utf-8 -*-

# Copyright (C) 2017, Maximilian Köhl <mail@koehlma.de>

import enum
import re

from collections import namedtuple
from re import escape


class LTL(enum.Enum):
    # boolean connectives
    AND = '∧', (escape('&'), escape('/\\'), escape('∧'),)
    OR = '∨', (escape('|'), escape('\\/'), escape('∨'),)
    NOT = '¬', (escape('!'), escape('~'), escape('¬'),)
    IMPL = '⇒', (escape('->'), escape('⇒'),)
    EQUIV = '⇔', (escape('='), escape('⇔'),)
    XOR = '^', (escape('^'),)

    # temporal connectives
    NEXT = 'X', (escape('X'),)
    UNTIL = 'U', (escape('U'),)
    WEAK = 'W', (escape('W'),)
    RELEASE = 'R', (escape('R'),)
    FINALLY = 'F', (escape('F'), escape('<>'), escape('◇'),)
    GLOBALLY = 'G', (escape('G'), escape('[]'), escape('☐'),)

    # parenthesis
    LEFT_PAR = '(', (escape('('),)
    RIGHT_PAR = ')', (escape(')'),)

    # booleans
    TRUE = 'true', (escape('true'),)
    FALSE = 'false', (escape('false'),)

    # propositions
    PROPOSITION = 'proposition', ('\w+',)

    # whitespaces
    WHITESPACE = None, ('\s+',)

    # error
    ERROR = None, ('.',)

    # end of formula
    EOF = None, ('',)


_regex = re.compile('|'.join('(?P<' + name + '>' + '|'.join(member.value[1]) + ')'
                             for name, member in LTL.__members__.items()))


Token = namedtuple('Token', ['kind', 'start', 'end', 'value'])


def tokenize(string):
    for match in _regex.finditer(string):
        kind = LTL[match.lastgroup]
        if kind is LTL.WHITESPACE:
            continue
        elif kind is LTL.ERROR:
            raise Exception('unknown token at position {}'.format(match.start()))
        yield Token(kind, match.start(), match.end(), match.group(0))
    yield Token(LTL.EOF, len(string), len(string), '')


_atoms = {LTL.TRUE, LTL.FALSE, LTL.PROPOSITION}
_unary_operators = {LTL.NOT, LTL.NEXT, LTL.FINALLY, LTL.GLOBALLY}

_binary_operators = {LTL.OR: 3, LTL.AND: 4, LTL.IMPL: 2, LTL.EQUIV: 1,
                     LTL.XOR: 5, LTL.UNTIL: 0, LTL.WEAK: 0, LTL.RELEASE: 0}


class LTLAst:
    def __init__(self, kind: LTL):
        self.kind = kind

    def is_atom(self):
        return self.kind in _atoms

    def is_proposition(self):
        return isinstance(self, LTLProposition)

    def is_binary_operator(self):
        return isinstance(self, LTLBinaryOperator)

    def is_unary_operator(self):
        return isinstance(self, LTLUnaryOperator)

    def __eq__(self, other):
        return self.kind is other.kind

    def __hash__(self):
        return hash(self.kind)

    def __str__(self):
        return self.kind.value[0]


class LTLProposition(LTLAst):
    def __init__(self, proposition: str):
        super().__init__(LTL.PROPOSITION)
        self.proposition = proposition

    def __str__(self):
        return str(self.proposition)

    def __eq__(self, other):
        return self.kind is other.kind and self.proposition == other.proposition

    def __hash__(self):
        return hash((self.kind, self.proposition))


class LTLBinaryOperator(LTLAst):
    def __init__(self, kind: LTL, left: LTLAst, right: LTLAst):
        super().__init__(kind)
        self.left = left
        self.right = right

    def __str__(self):
        return '({} {} {})'.format(self.left, super().__str__(), self.right)

    def __eq__(self, other):
        if self.kind is not other.kind:
            return False
        return self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash((self.kind, self.left, self.right))


class LTLUnaryOperator(LTLAst):
    def __init__(self, kind: LTL, operand: LTLAst):
        super().__init__(kind)
        self.operand = operand

    def __str__(self):
        return '{} {}'.format(super().__str__(), self.operand)

    def __eq__(self, other):
        return self.kind is other.kind and self.operand == other.operand

    def __hash__(self):
        return hash((self.kind, self.operand))


class Tokenizer:
    def __init__(self, string):
        self.generator = tokenize(string)
        self.current = next(self.generator)

    def advance(self):
        previous = self.current
        try:
            self.current = next(self.generator)
        except StopIteration:
            pass
        return previous

    def is_atom(self):
        return self.current.kind in _atoms

    def is_proposition(self):
        return self.current.kind is LTL.PROPOSITION

    def is_binary_operator(self):
        return self.current.kind in _binary_operators

    def is_unary_operator(self):
        return self.current.kind in _unary_operators

    def is_end(self):
        return self.current.kind is LTL.EOF

    def precedence(self):
        return _binary_operators[self.current.kind]


def _parse_primary_expression(tokenizer: Tokenizer) -> LTLAst:
    if tokenizer.is_proposition():
        return LTLProposition(tokenizer.advance().value)
    elif tokenizer.is_atom():
        return LTLAst(tokenizer.advance().kind)
    elif tokenizer.current.kind is LTL.LEFT_PAR:
        tokenizer.advance()
        expression = _parse_binary_expression(tokenizer, 0)
        token = tokenizer.advance()
        if token.kind is not LTL.RIGHT_PAR:
            raise Exception('expected closing parenthesis but got {}'.format(token))
        return expression
    else:
        raise Exception('unexpected token {}'.format(tokenizer.current))


def _parse_unary_expression(tokenizer: Tokenizer) -> LTLAst:
    if tokenizer.is_unary_operator():
        operator = tokenizer.advance()
        operand = _parse_unary_expression(tokenizer)
        return LTLUnaryOperator(operator.kind, operand)
    else:
        return _parse_primary_expression(tokenizer)


def _parse_binary_expression(tokenizer: Tokenizer, min_precedence: int) -> LTLAst:
    left = _parse_unary_expression(tokenizer)
    while tokenizer.is_binary_operator() and tokenizer.precedence() >= min_precedence:
        precedence = tokenizer.precedence()
        operator = tokenizer.advance()
        right = _parse_binary_expression(tokenizer, precedence + 1)
        left = LTLBinaryOperator(operator.kind, left, right)
    return left


def parse(string: str) -> LTLAst:
    tokenizer = Tokenizer(string)
    ast = _parse_binary_expression(tokenizer, 0)
    if not tokenizer.is_end():
        raise Exception('expected end of formula but found {}'.format(tokenizer.current))
    return ast
