# Author: Ayesha Akhtar
# Version: 08.06.2020
# Features implemented:
#   - +, -, multiplication, divide, powers, roots, percentage
#   - two 'modes' of game: levels, and choosing operations and their respective
#       level of difficulty (e.g. 1: 1 digit, power of two, square root etc.)
#   - table of questions and answers
#   - speedometer (??)
#   - skip button (NOTE: total time takes into account skipped questions,
#       avg time excludes skipped questions)


import tkinter as tk  # used for DISABLED and other key words
from tkinter import Button, Canvas, Entry, Frame, Label, Radiobutton, Scrollbar
from tkinter.ttk import Progressbar
import tkinter.font as font
from random import randint, sample  # used in generate
from functools import reduce  # used in factors
from time import time  # used in game
import operator  # used in generate
from itertools import chain  # used in factors
from os import path  # used in show_settings
from abc import ABC, abstractmethod  # used in Game


class Options(Radiobutton):
    def __init__(self, master, **kw):
        Radiobutton.__init__(self, master=master, **kw)
        self["padx"] = 10
        self["pady"] = 5
        self["indicatoron"] = 0
        self["bg"] = sbgc
        self["state"] = state
        self["fg"] = "white"
        self["selectcolor"] = tbgc
        self["font"] = f
        self["command"] = disable_start


class SpeedGraph():
    def __init__(self, canvas, x0, y0, x1, y1, width, avg):
        self.custom_font = font.Font(family="Consolas", size=20)
        self.canvas = canvas
        self.x0, self.y0 = x0+width, y0+width
        self.x1, self.y1 = x1-width, y1-width
        self.labelx, self.labely = (x1+x0) / 2, (y1+y0) / 2
        self.width = width
        self.start_angle = -140
        self.current_angle = 0
        self.running = True
        # draw static bar outline
        w2 = width / 2
        self.bg = self.canvas.create_arc(self.x0, self.y0, self.x1, self.y1,
                                         start=self.start_angle, extent=-260,
                                         width=self.width, style='arc',
                                         outline="#2a2a2a")
        # extent must be negative so it is drawn clockwise
        self.avg = avg
        if avg == 0:
            self.per = 0
            self.running = False
        elif 0 < avg <= 1:
            self.per = 1
        elif 1 < avg <= 2:
            self.per = 0.9
        elif 2 < avg <= 3:
            self.per = 0.8
        elif 3 < avg <= 5:
            self.per = 0.7
        elif 5 < avg <= 7:
            self.per = 0.6
        elif 7 < avg <= 10:
            self.per = 0.5
        elif 10 < avg <= 12:
            self.per = 0.4
        elif 12 < avg <= 15:
            self.per = 0.3
        elif 15 < avg <= 20:
            self.per = 0.2
        elif 20 < avg <= 30:
            self.per = 0.1
        else:
            self.per = 0.05

        self.limit = (self.per)*260
        self.start()

    def start(self, interval=30):
        self.interval = interval
        self.increment = 360 / interval
        self.filling = self.canvas.create_arc(
            self.x0, self.y0, self.x1, self.y1, start=self.start_angle,
            extent=0, width=self.width, style='arc', outline="#BB86FC"
        )
        self.label_id = self.canvas.create_text(
            self.labelx, self.labely, text=("{0:0.1f}s").format(self.avg),
            font=self.custom_font, fill="#BB86FC"
        )
        self.canvas.after(500, self.step, self.increment)

    def step(self, delta):
        if self.running:
            self.current_angle = (self.current_angle + delta) % 360
            self.canvas.itemconfigure(self.filling, extent=-self.current_angle)
            if self.current_angle > self.limit:
                self.running = False

        self.after_id = self.canvas.after(self.interval, self.step, delta)


class Result(Label):
    def __init__(self, master, **kw):
        Label.__init__(self, master=master, **kw)
        self["background"] = sbgc
        self["foreground"] = fc
        self["font"] = f


# class ToggleButton(Button):
#     def __init__(self, master, alttext="", **kw):
#         super().__init__(master=master,**kw)
#         #self["command"] = self.toggle
#         self["relief"] = tk.RAISED
#     def toggle(self):
#         if self["relief"] == tk.RAISED:
#             self["relief"] = tk.SUNKEN
#         else:
#             self["relief"] = tk.RAISED


class HoverButton(Button):
    def __init__(self, master, level="", **kw):
        Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        # default = white

        if self["activebackground"] == "SystemButtonFace":
            self["activebackground"] = tbgc
            # default
        self["background"] = self["activebackground"]

        self["fg"] = fc
        self["font"] = f

        if self["command"] == "":
            self["command"] = lambda: MainGame(level)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        # . = attribute
        # [] = option

    def on_enter(self, e):
        if self["state"] != tk.DISABLED:
            self["background"] = self.defaultBackground
            self["fg"] = "black"

    def on_leave(self, e):
        self["background"] = self["activebackground"]
        self["fg"] = fc


class Game(ABC):
    def __init__(self):
        self.frame = Frame(window, bg=bgc)
        self.start = 0
        self.end = 0
        self.qstart = 0
        self.qend = 0
        self.questions = self.generate()
        self.progress = 0
        self.cq = self.questions[self.progress]
        self.sv = tk.StringVar()
        self.start_questions()

    def factors(self, n):
        # chain.from_iterable takes (x, y) as input and returns x y
        return(set(chain.from_iterable(((self.check(i, n//i) for i in range(
            2, min(int(n**0.5) + 1, 13)) if n % i == 0)))))

    def format_percentage(self, v):
        p = v["first"]*100
        if p % 1 != 0.5:
            p = round(p)
        return ("{first}% of {second}").format(first=p, second=v["second"])

    def check(self, a, b):
        if 1 < b < 13:
            return (a, b)
        else:
            return(a, a)

    @abstractmethod
    def generate(self):
        pass

    def create_grid(self):
        self.ans.config(justify=tk.RIGHT)
        self.first.config(anchor="e", text=self.cq["first"])
        self.second.config(text=self.cq["second"])
        self.op.config(text=self.cq["op"])
        self.iframe.columnconfigure(0, weight=0)
        self.iframe.columnconfigure(1, weight=0)

    def create_one_line(self):
        self.ans.config(justify=tk.CENTER)
        self.iframe.columnconfigure(0, weight=1)
        self.iframe.columnconfigure(1, weight=1)
        self.first.config(anchor="center", text=self.cq["format"])
        self.second.config(text="")
        self.op.config(text="")

    def start_questions(self):
        # self.show_stats()
        self.frame.grid(row=0, column=0, sticky="news")
        for i in range(3):
            self.frame.rowconfigure(i, weight=1)
            self.frame.columnconfigure(i, weight=1)
        self.progressbar = Progressbar(self.frame, orient=tk.HORIZONTAL,
                                       length=200, mode="determinate", value=0)
        self.progressbar.grid(row=0, column=1, sticky="ew")
        Button(self.frame, text="x", anchor="se", bg=bgc, fg=fc, bd=0,
               activebackground=bgc, command=main_menu,
               font=(font.Font(family="Consolas", size=25))
               ).grid(row=0, column=0, sticky="nw")
        HoverButton(self.frame, command=lambda: self.next_question(True),
                    text="skip").grid(row=2, column=1, sticky="new")

        self.iframe = Frame(self.frame, bg=bgc)
        self.first = Label(self.iframe, font=qF, anchor="e", bg=bgc, fg=fc)
        self.second = Label(self.iframe, font=qF, anchor="e", bg=bgc, fg=fc)
        self.op = Label(self.iframe, font=qF, anchor="e", bg=bgc, fg=fc)
        self.ans = Entry(self.iframe, font=qF, bg=bgc, fg=fc, width=10,
                         textvariable=self.sv, insertbackground=fc, bd=0)

        self.iframe.grid(row=1, column=1, sticky="news")
        self.iframe.rowconfigure(0, weight=1)
        self.iframe.rowconfigure(4, weight=1)
        self.ans.delete(0, "end")
        self.sv.trace_add("write", self.check_value)

        if self.cq["op"] not in normal_op:
            self.create_one_line()
        else:
            self.create_grid()

        self.first.grid(row=1, column=0, columnspan=2, sticky="news")
        self.second.grid(row=2, column=1, sticky="news")
        self.op.grid(row=2, column=0, sticky="news")
        self.ans.grid(row=3, column=0, columnspan=2, sticky="news")
        self.ans.focus_set()

        self.start = time()
        self.qstart = time()

    def check_value(self, name, index, mode):
        if self.sv.get() == self.cq["answer"]:
            window.after(150, self.next_question)

    def next_question(self, skip=False):
            self.qend = time()
            if (skip):
                self.cq["time"] = "SKIP"
            else:
                self.cq["time"] = self.qend - self.qstart
            self.progress += 1
            if self.progress < len(self.questions):
                self.cq = self.questions[self.progress]
                self.progressbar["value"] = 100*(
                    self.progress/len(self.questions)
                )
                if self.cq["op"] not in normal_op:
                    self.create_one_line()
                else:
                    self.create_grid()
                self.ans.delete(0, "end")
                self.qstart = time()
            else:
                self.end = time()
                self.show_stats()

    def show_stats(self):
            self.frame.destroy()
            self.frame = Frame(window, bg=bgc)
            self.frame.grid(row=0, column=0, sticky="news")
            self.frame.rowconfigure(0, weight=1)
            self.frame.rowconfigure(4, weight=1)
            self.frame.columnconfigure(0, weight=1)
            self.frame.columnconfigure(3, weight=1)
            lblFrame = Frame(self.frame, bg=bgc)
            # lblFrame.grid_propagate(False)
            # lblFrame.rowconfigure(0, weight=1)
            # lblFrame.rowconfigure(3, weight=1)
            # lblFrame.columnconfigure(0, weight=1)
            # lblFrame.columnconfigure(2, weight=1)
            lblFrame.grid(row=2, column=2, sticky="news")
            diff = self.end-self.start
            Label(lblFrame, text=("Time taken: {0:0.1f}s".format(diff)),
                  font=f, anchor="w", bg=bgc, fg=fc
                  ).grid(row=0, column=0, padx=20, pady=(30, 0), sticky="news")

            avg = c = 0
            for q in self.questions:
                if q["time"] != "SKIP":
                    avg += q["time"]
                    c += 1
            if c != 0:
                avg /= c
            else:
                avg = 0
            # Label(lblFrame, text="Avg time taken: {0:0.1f}s".format(avg),
            # font=f, anchor="w", bg=bgc, fg=fc).grid(row=1, column=0, padx=20,
            # sticky="news")
            HoverButton(self.frame, text="choose level", command=main_menu
                        ).grid(row=3, column=2, padx=10, pady=20, sticky="ew")
            # play again button is added on in respective inherited methods

            graphFrame = Frame(self.frame, bg=bgc)
            graphFrame.grid(row=1, column=2, sticky="news")
            # graphFrame.grid_propagate(False)
            graphCanvas = Canvas(graphFrame, bg=bgc, highlightthickness=0)
            graphCanvas.grid()
            graph = SpeedGraph(graphCanvas, 50, 50, 250, 250, 15, avg)
            graphCanvas.create_text(
                150, 25, text="Average time taken", fill=tbgc,
                font=(font.Font(family="Consolas", size=20))
            )

            oframe = Frame(
                self.frame, bg=sbgc, bd=5, relief=tk.GROOVE, padx=10
            )
            oframe.grid(row=1, column=1, rowspan=2, sticky='nw')
            oframe.grid_rowconfigure(0, weight=1)
            oframe.grid_columnconfigure(0, weight=1)
            # prevents children of the frame resizing frame
            oframe.grid_propagate(False)

            # Add a canvas in that frame
            canvas = Canvas(oframe, bg=sbgc, highlightbackground=sbgc)
            canvas.grid(row=0, column=0, sticky="news", padx=20, pady=20)

            # Link a scrollbar to the canvas
            vsb = Scrollbar(oframe, orient=tk.VERTICAL, command=canvas.yview)
            vsb.grid(row=0, column=1, sticky='ns', padx=5, pady=5)
            canvas.configure(yscrollcommand=vsb.set)

            hsb = Scrollbar(oframe, orient=tk.HORIZONTAL, command=canvas.xview)
            hsb.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
            canvas.configure(xscrollcommand=hsb.set)

            # Create a frame to contain the results
            self.iframe = Frame(canvas, bg=sbgc)
            canvas.create_window((0, 0), window=self.iframe, anchor='nw')

            Result(self.iframe, text="Question"
                   ).grid(row=0, column=0, padx=5, sticky="news")
            Result(self.iframe, text="Answer"
                   ).grid(row=0, column=1, padx=5, sticky="news")
            Result(self.iframe, text="Time"
                   ).grid(row=0, column=2, padx=5, sticky="news")
            global normal_op
            for c, v in enumerate(self.questions):
                if v["op"] in normal_op:
                    Result(self.iframe, text=v["format"]
                           ).grid(row=c+1, column=0, padx=5, sticky="news")
                else:
                    Result(self.iframe, text=v["format"]
                           ).grid(row=c+1, column=0, padx=5, sticky="news")

                Result(self.iframe, text=v["answer"]
                       ).grid(row=c+1, column=1, padx=5, sticky="news")
                if v["time"] == "SKIP":
                    Result(self.iframe, text=v["time"]
                           ).grid(row=c+1, column=2, padx=5, sticky="news")
                else:
                    Result(self.iframe, text=("{0:0.1f} sec").format(v["time"])
                           ).grid(row=c+1, column=2, padx=5, sticky="news")

            self.iframe.update_idletasks()  # NEED THIS for BBOX INFO
            oframe.config(width=400, height=400)
            canvas.config(scrollregion=canvas.bbox("all"))


class MainGame(Game):
    # NOTE: The child's __init__() function OVERRIDES the
    # inheritance of the parent's __init__() function !!!!
    # To keep the inheritance of the parent's __init__() function,
    # add a call to the parent's __init__() function:

    def __init__(self, level):
        self.difficulty = level
        super().__init__()

    def generate(self):
        questions = []
        op = {
            '+': operator.add,
            '-': operator.sub,
            'x': operator.mul,
            '\u00F7': operator.floordiv,
            "\u00B2": operator.pow,
            "\u221A": operator.pow,
            "%": operator.mul,
            # "£": operator.mul,
        }

        diff_op = {
            "warmup": 3,
            "easy": 3,
            "medium": 6,
            "hard": 6,
        }

        firstswitch_secondadd = {
            "warmup": (1, 10),
            "easy": (1, 100),
            "medium": (10, 1000),
            "hard": (100, 10000)
        }

        second_mul = {
            "warmup": (1, 10),
            "easy": (1, 10),
            "medium": (1, 10),
            "hard": (10, 100)
        }

        second_sub = {
            "warmup": 1,
            "easy": 1,
            "medium": 10,
            "hard": 100,
        }

        exp_switch = {
            3: "\u00B3",
            4: "\u2074",
            5: "\u2075",
            6: "\u2076",
        }

        root_switch = {
            3: "\u221B",
            4: "\u221C",
            5: "\u2155",
            6: "\u2159",
        }

        per_switch = {
            "medium": (5, 10),
            "hard": (1, 10),
        }

        while len(questions) < 10:
            q = {
                "first": "",
                "op": "",
                "second": "",
                "answer": "",
                "time": 0,
                "format": "",
            }

            q["op"] = list(op.keys())[
                randint(0, diff_op.get(self.difficulty, 6))
            ]

            global normal_op
            if q["op"] in normal_op:
                q["first"] = randint(
                    *(firstswitch_secondadd.get(self.difficulty, (1, 10)))
                )
                if q["op"] == "\u00F7":
                    f = self.factors(q["first"])
                    if len(f) == 0:
                        continue
                    q["second"] = sample(f, 1)[0]
                    # second generated from 1-12 factors of the first number
                elif q["op"] == "-":
                    q["second"] = randint(
                        second_sub.get(self.difficulty, 1),
                        q["first"]
                    )
                elif q["op"] == "x":
                    q["second"] = randint(
                        *(second_mul.get(self.difficulty, (1, 10)))
                    )
                elif q["op"] == "+":
                    q["second"] = randint(
                        *(firstswitch_secondadd.get(self.difficulty, (1, 10)))
                    )  # same as generating first number
                q["format"] = "{} {} {}".format(
                    q["first"],
                    q["op"],
                    q["second"]
                )
            else:
                if q["op"] == "\u00B2":
                    q["first"] = randint(1, 10)
                    if self.difficulty == "medium":
                        q["second"] = 2
                    elif self.difficulty == "hard":
                        q["second"] = randint(2, 3)
                    q["format"] = "{}{}".format(
                        q["first"],
                        exp_switch.get(q["second"], "\u00B2")
                    )
                elif q["op"] == "\u221A":
                    i = 1
                    if self.difficulty == "medium":
                        i = 2
                    elif self.difficulty == "hard":
                        i = randint(2, 3)
                    q["second"] = 1/i
                    q["first"] = randint(1, 10) ** i
                    q["format"] = "{}{}".format(
                        root_switch.get(i, "\u221A"),
                        q["first"]
                    )
                elif q["op"] == "%":
                    x = per_switch.get(self.difficulty, (10, 10))
                    q["first"] = ((randint(1, 100/x[0])) * x[0]) / 100
                    q["second"] = randint(1, 100) * x[1]
                    q["format"] = self.format_percentage(q)
                    # percentage = level1: 10s, level2: 5s w/ large numbers,
                    # level3: 1s w/ large numbers, level4: 1s with small number
                    # level5: 0.5s with any range
            q["answer"] = op[q["op"]](q["first"], q["second"])
            if q["answer"] % 1 == 0:
                q["answer"] = str(round(q["answer"]))
            else:
                q["answer"] = str(round(q["answer"], 4))
            questions.append(q)
        return(questions)

    def show_stats(self):
        super().show_stats()
        HoverButton(self.frame, text="play again", level=self.difficulty
                    ).grid(row=3, column=1, padx=10, pady=20, sticky="ew")


class AltGame(Game):
    def __init__(self, var):
        self.var = var
        super().__init__()

    def generate(self):
        questions = []
        op = {
            '+': operator.add,
            '-': operator.sub,
            'x': operator.mul,
            '\u00F7': operator.floordiv,
            "\u00B2": operator.pow,
            "\u221A": operator.pow,
            "%": operator.mul,
            # "£": operator.mul,
        }

        per_alt_switch = {
            1: (10, 10),  # multiples of ten for second
            2: (5, 10),
            3: (1, 10),
            4: (1, 1),  # no multiple, therefore smaller numbers
            5: (0.5, 10),
        }

        selected_op = [
            (self.var[c].get(), v) for c, v in enumerate(list(op.keys()))
            if self.var[c].get() != 0
        ]

        while len(questions) < 10:
            q = {
                "first": "",
                "op": "",
                "second": "",
                "answer": "",
                "time": 0,
                "format": "",
            }
            index = randint(0, len(selected_op) - 1)
            q["op"] = selected_op[index][1]
            var = selected_op[index][0]

            global normal_op
            if q["op"] in normal_op:
                bound = 10**(var)
                q["first"] = randint(bound//10, bound)
                if q["op"] == "\u00F7":
                    f = self.factors(q["first"])
                    if len(f) == 0:
                        continue
                    q["second"] = sample(f, 1)[0]
                    # second generated from 1-12 factors of the first number
                elif q["op"] == "-":
                    q["second"] = randint(1, q["first"])
                elif q["op"] == "x":
                    q["second"] = randint(1, 12)
                elif q["op"] == "+":
                    q["second"] = randint(1, bound)
                    # same as generating first number
                q["format"] = "{} {} {}".format(
                    q["first"],
                    q["op"],
                    q["second"]
                )
            else:
                bound = 10*(var)
                if q["op"] == "\u00B2":
                    q["first"] = randint(1, bound)
                    # NOTE: base only between 1 and 10 for now
                    q["second"] = 2
                    q["format"] = "{}{}".format(q["first"], q["op"])
                elif q["op"] == "\u221A":
                    q["first"] = randint(1, bound) ** 2
                    q["second"] = 1/2
                    q["format"] = "{}{}".format(q["op"], q["first"])
                elif q["op"] == "%":
                    x = per_alt_switch.get(var, (10, 10))
                    q["first"] = ((randint(1, 100/x[0])) * x[0]) / 100
                    q["second"] = randint(1, 100) * x[1]
                    q["format"] = self.format_percentage(q)
                    # percentage = level1: 10s, level2: 5s w/ large numbers,
                    # level3: 1s w/ large numbers, level4: 1s with small number
                    # level5: 0.5s with any range

            q["answer"] = op[q["op"]](q["first"], q["second"])
            if q["answer"] % 1 == 0:
                q["answer"] = str(round(q["answer"]))
            else:
                q["answer"] = str(round(q["answer"], 4))

            questions.append(q)
        return(questions)

    def show_stats(self):
        super().show_stats()
        HoverButton(self.frame, text="play again", command=lambda: AltGame(v)
                    ).grid(row=3, column=1, padx=10, pady=20, sticky="ew")

# def show_settings():
#     settings = Frame(window, bg=bgc)
#     settings.grid(row=0, column=0, sticky="news")
#     if path.exists("settings.txt") is False:
#         file = open("settings.txt", "a")
#         for i in range(10):
#             file.write("False")
#         file.close()
#     ToggleButton(settings, text="Night Mode", alttext="Light Mode").grid()


def main_menu():
    global currentmode
    if currentmode == "main":
        main.tkraise()
    elif currentmode == "alt":
        altmain.tkraise()


def switch_mode():
    global currentmode
    if currentmode == "main":
        currentmode = "alt"
    else:
        currentmode = "main"
    main_menu()


def disable_start():
    global v, alt_start
    flag = True
    for i in v:
        if i.get() != 0:
            flag = False
            break

    if (flag):
        alt_start.config(state=tk.DISABLED)
    else:
        alt_start.config(state=tk.NORMAL)


if __name__ == "__main__":
    window = tk.Tk()
    window.geometry("800x600")
    window.title("Mental Maths")
    window.rowconfigure(0, weight=1)
    window.columnconfigure(0, weight=1)

    # CONSTANTS
    bgc = "#1d1d1d"
    sbgc = "#2a2a2a"  # 363636?
    tbgc = "#BB86FC"
    fc = "white"
    f = font.Font(family="Consolas", size=15)
    sf = font.Font(family="Consolas", size=10)
    qF = font.Font(family="Consolas", size=50)
    all_op = ["+", "-", "x", "\u00F7", "\u00B2", "\u221A", "%", "?"]
    # add, sub, mul, div, exponent, percentage, money, fraction
    normal_op = ["+", "-", "x", "\u00F7"]

    currentmode = "main"

    # BUILDING MAIN MENU
    main = Frame(window, bg=bgc)
    main.rowconfigure(7, weight=1)
    main.columnconfigure(0, weight=1)
    main.grid(row=0, column=0, sticky="news")

    warmup = HoverButton(
        main, activebackground="#fd9367", level="warmup",
        text="warmup\n1 digit +, -, x, \u00F7"
    )
    easy = HoverButton(
        main, activebackground="#f0445e", level="easy",
        text="easy\n2 digit +, -, x, \u00F7"
    )
    medium = HoverButton(
        main, activebackground="#c3305d", level="medium",
        text="medium\n3 digit +, -, x, \u00F7, \u00B2, \u221A, %"
    )
    hard = HoverButton(
        main, activebackground="#782d65", level="hard",
        text="hard\n4 digit +, -, x, \u00F7, \u00B2, \u00B3, \u221A, \u221B, %"
    )
    difficult = HoverButton(
        main, activebackground="#432967", level="difficult", state=tk.DISABLED,
        text="difficult\n+, -, x, \u00F7, \u00B2, \u00B3, \u221A, \u221B, %"
    )
    mode = HoverButton(main, text="switch mode", command=switch_mode)
    # settings = HoverButton(main, text="settings", activebackground="#d3d3d3",
    # command=show_settings, state=tk.DISABLED)
    main_btns = [easy, medium, hard, difficult, mode]
    warmup.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
    for c, v in enumerate(main_btns):
        v.grid(row=c+1, column=0, padx=20, pady=5, sticky="ew")

    # BUILDING ALT MENU
    altmain = Frame(window, bg=bgc)
    for i in range(5):
        altmain.rowconfigure(i, weight=1)
    altmain.rowconfigure(7, weight=1)
    # skipped row 5 and 6 to allow
    for i in range(6):
        altmain.columnconfigure(i, weight=1)
    altmain.grid(row=0, column=0, sticky="news")

    row = 1
    col = 1
    for i in all_op:
        Label(altmain, text=i, bg=bgc, fg=fc, font=f
              ).grid(row=row, column=col, sticky="news")
        row += 1
        if i == "\u00F7":
            col = 3
            row = 1

    v = []
    col = 2
    for i in range(8):
        v.append(tk.IntVar())
        frame = Frame(altmain, padx=20, bg=bgc)
        frame.rowconfigure(0, weight=1)
        frame.grid(row=((i % 4) + 1), column=col, sticky="news")
        for c in range(6):
            if c == 0:
                val = "x"
            else:
                val = c
            if i == 7:
                state = tk.DISABLED
            else:
                state = tk.NORMAL
            Options(frame, text=val, variable=v[i], value=c, state=state
                    ).grid(row=0, column=c, sticky="ew")
        if i == 3:
            col = 4

    btn_frame = Frame(altmain, bg=bgc)
    btn_frame.grid(row=5, column=1, columnspan=4, sticky="news")
    for i in range(4):
        btn_frame.columnconfigure(i, weight=1)
    for i in range(2):
        btn_frame.rowconfigure(i, weight=1)
    alt_start = HoverButton(btn_frame, text="start game",
                            command=lambda: AltGame(v), state=tk.DISABLED)
    alt_start.grid(row=0, column=1, columnspan=2, sticky="ew")
    HoverButton(btn_frame, text="return to main menu", command=switch_mode
                ).grid(row=1, column=1, columnspan=2, sticky="ew", pady=10)

    # START
    main_menu()
    window.mainloop()
