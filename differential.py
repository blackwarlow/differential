import re
from parser import *
from typing import Any


def runge_kutta(eq: Node, x0: float, y0: float, h: float) -> float:
    """
    Нахождение решения в следующей точке методом Рунге-Кутты.

    Шаг: h
    Предыдущее решение: x0, y0
    Уравнение: eq
    """
    k1 = eq.compute(x0, y0)
    k2 = eq.compute(x0 + h / 2, y0 + h / 2 * k1)
    k3 = eq.compute(x0 + h / 2, y0 + h / 2 * k2)
    k4 = eq.compute(x0 + h, y0 + h * k3)
    return y0 + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


def get_rg_4(eq: Node, x0: float, y0: float, h: float) -> list[tuple[float, float]]:
    """
    Нахождение 4 точек решения методом Рунге-Кутты.
    Используется для метода Адамса.

    Шаг: h
    Изначальное решение: x0, y0
    Уравнение: eq
    """
    values = [(x0, y0)]
    for i in range(3):
        x, y = values[i]
        y = runge_kutta(eq, x, y, h)
        x += h
        values.append((x, y))
    return values


def lmultistep(eq: Node, v: list[tuple[float, float]], h: float) -> tuple[float, float]:
    """
    Linear multistep method.
    Нахождение решения в следующей точке методом Адамса.

    Шаг: h
    4 точки предварительного решения: v
    Уравнение: eq
    """
    return (
        v[-1][0] + h,
        v[-1][1]
        + h
        * (
            55 / 24 * eq.compute(v[-1][0], v[-1][1])
            - 59 / 24 * eq.compute(v[-2][0], v[-2][1])
            + 37 / 24 * eq.compute(v[-3][0], v[-3][1])
            - 9 / 24 * eq.compute(v[-4][0], v[-4][1])
        ),
    )


def euler_cauchy(eq: Node, x0: float, y0: float, h: float) -> tuple[float, float]:
    """
    Нахождение решения в следующей точке методом Эйлера-Коши.

    Шаг: h
    Предыдущее решение: x0, y0
    Уравнение: eq
    """
    y = eq.compute(x0, y0)
    x = x0 + h
    yi = y0 + h * y
    return (
        x,
        y0 + (h / 2) * (y + eq.compute(x, yi)),
    )


def print_table(v: list[tuple[float, float]], h: float):
    """
    Выводит таблицу x, y с форматом строк.

    Пары значений [(x, y), ...]: v
    Размер шага: h
    """
    w1 = max(list(map(lambda x: len(str(round(x[0]))) + len(str(h)) + 1, v)))
    w2 = max(list(map(lambda x: len(str(round(x[1]))) + 8, v)))
    k = len(str(h)) - 2
    hl = "+" + "-" * (w1 + 2) + "+" + "-" * (w2 + 2) + "+\n"
    l = "| {:<" + str(w1) + "} | {:<" + str(w2) + "} |\n"
    fl = "| {:" + str(w1) + "." + str(k) + "f} | {:" + str(w2) + ".6f} |\n"

    print(hl + l.format("x", "y") + hl, end="")
    for x, y in v:
        print(fl.format(x, y) + hl, end="")


def user_input(target: list[Any], msg: str) -> list[Any]:
    """
    Обрабатывает ввод пользователя согласно target-списку данных для ввода.
    Показывает перед вводом сообщение msg.

    Если указано одно значение, возвращаего его, иначе возвращает список.
    """

    done: bool = False
    while not done:
        print(msg)
        try:
            cmd: str | list[str] = input("> ")
            if len(target) > 1:
                cmd = re.split(" |,|;", cmd)
            else:
                cmd = [cmd]
            if len(cmd) != len(target):
                print("\n\tОшибка ввода, некорректное количество значений!\n")
                continue
            v: list[Any] = [func(item) for item, func in zip(cmd, target)]
            return v[0] if len(target) == 1 else tuple(v)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            print("\n\tОшибка ввода, неверный тип данных ввода!\n")


def main():
    """
    Главная функция работы с программой.
    Обрабатывает ввод и передаёт его на решение 2 методам.
    """
    exit: bool = False
    done: bool = False
    eq: Node = None
    a: float = 0
    b: float = 0
    n: int = 0
    h: float = 0
    x0: float = 0
    y0: float = 0

    while not exit:
        done = False
        while not (done or exit):
            try:
                cmd = user_input(
                    [str],
                    "Введите уравнение ОДУ строкой, используя переменные (x, y и y') :",
                )
                eq = parse(cmd)
                done = True
            except KeyboardInterrupt:
                done = True
                exit = True
            except Exception as e:
                print("\n\t{}: {}\n".format(type(e).__name__, e.args[0]))
        done = False

        while not (done or exit):
            try:
                a, b = user_input(
                    [float, float],
                    "Введите границы отрезка для нахождения значений (a b) :",
                )
                a, b = min(a, b), max(a, b)
                done = True
            except KeyboardInterrupt:
                exit = True
                done = True
            except Exception as e:
                print("\n\t{}: {}\n".format(type(e).__name__, e.args[0]))
        done = False

        while not (done or exit):
            try:
                n = user_input([int], "Введите количество точек внутри отрезка (n) :")
                h = (b - a) / n
                done = True
            except KeyboardInterrupt:
                exit = True
                done = True
            except ZeroDivisionError:
                print("\n\tОшибка ввода, количество шагов должно быть больше 0!\n")
            except Exception as e:
                print("\n\t{}: {}\n".format(type(e).__name__, e.args[0]))
        done = False

        while not (done or exit):
            try:
                x0, y0 = user_input(
                    [float, float], "Введите начальное решение (x0 y0) :"
                )

                eq.compute(x0, y0)
                done = True
            except KeyboardInterrupt:
                exit = True
                done = True
            except ZeroDivisionError:
                print(
                    "\n\tОшибка ввода, данные начальные условия ОДУ не являются решением!\n"
                )
            except Exception as e:
                print("\n\t{}: {}\n".format(type(e).__name__, e.args[0]))
        done = False

        while not (done or exit):
            try:
                cmd = user_input(
                    [str],
                    "Выберите метод решения:\n1) Метод Адамса\n2) Метод Эйлера-Коши\ne) Выйти из программы\n*) Решить другое уравнение",
                )
                if cmd == "1":
                    print("Решение задания методом Адамса 4 ранга.")
                    values = get_rg_4(eq, x0, y0, h)
                    for i in range(n - 3):
                        values.append(lmultistep(eq, values, h))
                    print_table(values, h)
                elif cmd == "2":
                    print("Решение задачи методом Эйлера-Коши.")
                    values = [(x0, y0)]
                    for i in range(n):
                        item = values[i]
                        values.append(euler_cauchy(eq, item[0], item[1], h))
                    print_table(values, h)
                elif cmd == "e":
                    exit = True
                    done = True
                else:
                    done = True
            except KeyboardInterrupt:
                exit = True
                done = True
            except ZeroDivisionError:
                print(
                    "\n\tОшибка ввода, данные начальные условия ОДУ не являются решением!\n"
                )
            except Exception as e:
                print("\n\t{}: {}\n".format(type(e).__name__, e.args[0]))


if __name__ == "__main__":
    main()
