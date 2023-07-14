"""
MIT License

Copyright (c) 2023 Nikita Belomestnykh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import math
import operator
import re
from enum import Enum, auto, unique

from typing_extensions import Self


@unique
class TokenType(Enum):
    """Фиксированное описание всех возможных типов нод парсера"""
    T_VR1 = auto()
    T_VR2 = auto()
    T_NUM = auto()
    T_E = auto()
    T_PNT = auto()
    T_ADD = auto()
    T_NEG = auto()
    T_SUB = auto()
    T_MUL = auto()
    T_DIV = auto()
    T_DIF = auto()
    T_POW = auto()
    T_LPR = auto()
    T_RPR = auto()
    T_EQU = auto()
    T_END = auto()


# Список унарных операций
UNARY = [TokenType.T_NEG]

# Маппинг токенов на типы нод
TOKEN_MAP = {
    "(": TokenType.T_LPR,
    ")": TokenType.T_RPR,
    "+": TokenType.T_ADD,
    "-": TokenType.T_NEG,
    "*": TokenType.T_MUL,
    "/": TokenType.T_DIV,
    "^": TokenType.T_POW,
    "'": TokenType.T_DIF,
    ".": TokenType.T_PNT,
    ",": TokenType.T_PNT,
    "=": TokenType.T_EQU,
    "x": TokenType.T_VR1,
    "y": TokenType.T_VR2,
    "e": TokenType.T_E,
}

# Обратный маппинг
TOKEN_MAP_REV = {v: k for k, v in TOKEN_MAP.items()}

# Маппинг операторов
OPERATIONS = {
    TokenType.T_ADD: operator.add,
    TokenType.T_NEG: operator.neg,
    TokenType.T_MUL: operator.mul,
    TokenType.T_DIV: operator.truediv,
    TokenType.T_SUB: operator.sub,
    TokenType.T_POW: operator.pow,
}


class LexerError(Exception):
    """Базовая ошибка лексера"""
    pass


class NoEquationError(LexerError):
    """Ошибка лексера - отсутствие уравнения"""
    pass


class NoArgumentError(LexerError):
    """Ошибка лексера - нет аргумента х"""
    pass


class NoODEError(LexerError):
    """Ошибка лексера - уравнение не ОДУ"""
    pass


class NoDifferentialError(LexerError):
    """Ошибка лексера - нет производной"""
    pass


class UndefinedLexem(LexerError):
    """Ошибка лексера - неизвестная лексема"""
    pass


class ParserError(Exception):
    """Ошибка парсера"""
    pass


class EvaluateError(Exception):
    """Ошибка вычисления"""
    pass


class Node:
    """
    Класс ноды ast-дерева математического выражения
    """
    def __init__(
        self, token_type: TokenType, value: str = None, children: list[Self] = []
    ) -> Self:
        self.token_type = token_type
        self.children = list(children)
        self.value: str = value

    def find(self, token_type: TokenType) -> bool:
        """Рекурсивный поиск ноды среди детей"""
        return (
            any(c.find(token_type) for c in self.children)
            or self.token_type == token_type
        )

    def path(self, token_type: TokenType) -> bool:
        """Рекурсивный путь к ноде"""
        if self.token_type == token_type:
            return []
        for i, c in enumerate(self.children):
            p = c._path(token_type, i)
            if p is not None:
                return p
        return None

    def _path(self, token_type: TokenType, index: int) -> bool:
        """Обработка поиска пути""""
        if self.token_type == token_type:
            return [index]
        for i, c in enumerate(self.children):
            p = c._path(token_type, i)
            if p is not None:
                return [index] + p
        return None

    def navigate(self, path: list[int]) -> Self:
        """Прохождение по ast-дереву вглубь"""
        if len(path) == 0:
            return self
        index = path.pop(0)
        return self.children[index].navigate(path)

    def reverse(self, path: list[int], second: Self) -> Self:
        """Обработка решения дерева относительно указанной ноды"""
        item_prev = self
        while len(path) > 0:
            index = path.pop(0)
            item = item_prev.children[index]

            if item_prev.token_type == TokenType.T_NEG:
                second = Node(TokenType.T_NEG, "-", [second])

            elif item_prev.token_type == TokenType.T_SUB:
                if index == 0:
                    second = Node(
                        TokenType.T_ADD,
                        "+",
                        [
                            item_prev.children[not index],
                            second,
                        ],
                    )
                else:
                    second = Node(
                        TokenType.T_SUB,
                        "-",
                        [
                            item_prev.children[not index],
                            second,
                        ],
                    )

            elif item_prev.token_type == TokenType.T_ADD:
                second = Node(
                    TokenType.T_SUB,
                    "-",
                    [
                        second,
                        item_prev.children[not index],
                    ],
                )

            elif item_prev.token_type == TokenType.T_MUL:
                second = Node(
                    TokenType.T_DIV,
                    "/",
                    [
                        second,
                        item_prev.children[not index],
                    ],
                )

            elif item_prev.token_type == TokenType.T_DIV:
                if index == 0:
                    second = Node(
                        TokenType.T_MUL,
                        "*",
                        [
                            item_prev.children[not index],
                            second,
                        ],
                    )
                else:
                    second = Node(
                        TokenType.T_DIV,
                        "/",
                        [
                            item_prev.children[not index],
                            second,
                        ],
                    )
            elif item_prev.token_type == TokenType.T_POW:
                second = Node(
                    TokenType.T_POW,
                    "^",
                    [
                        second,
                        Node(
                            TokenType.T_DIV,
                            "/",
                            [
                                Node(TokenType.T_NUM, "1"),
                                item_prev.children[not index],
                            ],
                        ),
                    ],
                )

            item_prev = item
        return second

    def compute(self, x: float, y: float) -> float:
        """Вычислить результат ОДУ"""
        if self.token_type == TokenType.T_DIF:
            print(self)
            raise EvaluateError(
                "Произошла ошибка вычисления, значение дифференциала не вычисляется, проверьте дерево вывода."
            )

        if self.token_type == TokenType.T_NUM:
            return float(self.value)
        elif self.token_type == TokenType.T_E:
            return math.e
        elif self.token_type == TokenType.T_VR1:
            return x
        elif self.token_type == TokenType.T_VR2:
            return y
        elif self.token_type in UNARY:
            return OPERATIONS[self.token_type](self.children[0].compute(x, y)) # Убрать x, y
        else:
            left = self.children[0].compute(x, y)
            right = self.children[1].compute(x, y)
            return OPERATIONS[self.token_type](left, right)

    def to_string(self, placeholders: bool = False):
        """Привести ast-дерево к строке"""
        s: str = ""
        if self.token_type == TokenType.T_DIF:
            raise EvaluateError(
                "Value of differential is not computable, please check tree for reordering"
            )
        if len(self.children) == 1:
            s += "{}({})".format(self.value, self.children[0].to_string(placeholders))
        elif len(self.children) == 2:
            s += "({}){}({})".format(
                self.children[0].to_string(placeholders),
                self.value,
                self.children[1].to_string(placeholders),
            )
        else:
            if self.token_type == TokenType.T_NUM:
                s += self.value
            else:
                s += str("{" + self.value + "}") if placeholders else self.value
        return s

    def __str__(self) -> str:
        """Строковое представление объекта"""
        return "Node({}, {}{})".format(
            self.token_type,
            self.value,
            ", [\n{}\n]".format(
                "\n".join(
                    [
                        "    " + line
                        for child in map(str, self.children)
                        for line in child.split("\n")
                    ]
                )
            )
            if len(self.children)
            else "",
        )


def ast_equ(ts: list[Node]) -> Node:
    """Оператор равенства"""
    l_n = ast_sum(ts)
    while check(ts, TokenType.T_EQU):
        n = consume(ts)
        n.children.append(l_n)
        n.children.append(ast_sum(ts))
        l_n = n
    return l_n


def ast_sum(ts: list[Node]) -> Node:
    """Оператор суммы"""
    l_n = ast_mul(ts)
    while check(ts, [TokenType.T_ADD, TokenType.T_NEG]):
        n = consume(ts)
        if n.token_type == TokenType.T_NEG:
            n.token_type = TokenType.T_SUB
        n.children.append(l_n)
        n.children.append(ast_mul(ts))
        l_n = n
    return l_n


def ast_mul(ts: list[Node]) -> Node:
    """Оператор умножения"""
    l_n = ast_pow(ts)
    while check(ts, [TokenType.T_MUL, TokenType.T_DIV]):
        n = consume(ts)
        n.children.append(l_n)
        n.children.append(ast_pow(ts))
        l_n = n
    return l_n


def ast_pow(ts: list[Node]) -> Node:
    """Оператор степени"""
    l_n = ast_fun(ts)
    while check(ts, [TokenType.T_POW]):
        n = consume(ts)
        n.children.append(l_n)
        n.children.append(ast_fun(ts))
        l_n = n
    return l_n


def ast_fun(ts: list[Node]) -> Node:
    if ts[0].token_type == TokenType.T_NEG:
        n = consume(ts)
        n.children.append(ast_val(ts))
        return n
    return ast_val(ts)


def ast_val(ts: list[Node]) -> Node:
    """Оператор производной"""
    if check(ts, TokenType.T_VR1):
        n = consume(ts)
        if check(ts, TokenType.T_DIF):
            raise ParserError("Аргумент х не может быть дифференциирован!")
        return n

    elif check(ts, TokenType.T_NUM):
        n = consume(ts)
        while check(ts, [TokenType.T_NUM, TokenType.T_PNT]):
            r_n = consume(ts)
            n.value += "." if r_n.token_type == TokenType.T_PNT else r_n.value
        if check(ts, TokenType.T_DIF):
            consume(ts)
            n.value = "0"
        return n

    elif check(ts, TokenType.T_VR2):
        n = consume(ts)
        if check(ts, TokenType.T_DIF):
            wrap = consume(ts)
            wrap.children.append(n)
            n = wrap
        return n

    elif check(ts, TokenType.T_E):
        n = consume(ts)
        return n

    match(ts, TokenType.T_LPR)
    expression = ast_sum(ts)
    match(ts, TokenType.T_RPR)
    if check(ts, TokenType.T_DIF):
        wrap = consume(ts)
        wrap.children.append(expression)
        expression = wrap
    return expression


def match(ts: list[Node], exp: TokenType) -> Node:
    """Нахождение совпадения"""
    if check(ts, exp):
        return consume(ts)
    else:
        raise ParserError("Ошибка синтаксиса на операнде '{}'".format(ts[0]))


def consume(ts: list[Node]) -> Node:
    """Удаление ноды из списка"""
    return ts.pop(0)


def check(ts: list[Node], exp: TokenType | list[TokenType]):
    """Проверка соответствия ноды указанной/ым"""
    if isinstance(exp, list):
        return ts[0].token_type in exp
    return ts[0].token_type == exp


def lex_analyse(s: str) -> list:
    """Провести лексемный анализ выражения"""
    s = s.lower()
    ts = []

    if not TOKEN_MAP_REV[TokenType.T_EQU] in s:
        raise NoEquationError("Выражение должно содержать одно уравнение!")

    if not TOKEN_MAP_REV[TokenType.T_VR1] in s:
        raise NoArgumentError("Уравнение должно содержать хотя бы один аргумент!")

    if len(re.findall(TOKEN_MAP_REV[TokenType.T_VR2], s)) != 2:
        raise NoODEError("Уравенение должно содержать функцию и её производную!")
    if (
        len(
            re.findall(
                TOKEN_MAP_REV[TokenType.T_VR2] + TOKEN_MAP_REV[TokenType.T_DIF], s
            )
        )
        != 1
    ):
        raise NoDifferentialError("Уравнение должно содержать одну производную!")

    for i, c in enumerate(s):
        if c in TOKEN_MAP:
            tk = Node(TOKEN_MAP[c], value=c)
        elif re.match(r"\d", c):
            tk = Node(TokenType.T_NUM, value=c)
        elif re.match(r"x", c) or re.match(r"y", c):
            tk = Node(TokenType.T_VAR, value=c)
        else:
            raise UndefinedLexem(
                "Неизвестный символ: '{}' в строке, позиция {}".format(c, i)
            )
        ts.append(tk)
    ts.append(Node(TokenType.T_END))
    return ts


def reorder(tk: Node) -> Node:
    """Переобпределить выражения для решения ОДУ"""
    # Find in which half of equasion y' is located at
    r: bool = tk.children[1].find(TokenType.T_DIF)
    pr = tk.children[r]
    s = tk.children[not r]

    p = pr.path(TokenType.T_DIF)
    return pr.reverse(p, s)


def parse(s: str) -> Node:
    """Выполнить парсинг выражения"""
    ts: list[Node] = lex_analyse("".join(s.split()))
    ast = ast_equ(ts)
    match(ts, TokenType.T_END)
    ast = reorder(ast)
    return ast
