from cmath import pi
from random import random
from tkinter import Y
import modules
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from time import sleep
from random import randint
import numpy as np
from experiments import *
from experiments import Results

global pause
pause = False


class Display:
    def __init__(self, results, title=""):
        self.info = results
        self.x = results.get("time")
        self.y = []
        self.title = title


        for result_name in results.list_results():
            if result_name != "time":
                self.add_source(results.get(result_name), result_name)

    def add_source(self, series, source_name="", source_color="black", source_lim=[-0.2, 1.2]):
        new_source = {
            "source": series,
            "color": source_color,
            "name": source_name,
            "ylim": source_lim,
        }
        self.y.append(new_source)

    def show(self):
        display(self.x, self.y, self.title)

    def animate(self):
        demo(self.x, self.y)

    def show_erp(self, signal="y"):
        result = self.info
        assert("stim" in result.list_results() and signal in result.list_results())
        stim = result.get("stim")
        signals = result.get(signal)
        avg, avg_time, n = ERP(stim, signals, pre=50, post=100, target=1)

        plt.figure()
        plt.plot(avg_time, avg)
        plt.suptitle(f"ERP over {n} trials")
        plt.title(signal)
        plt.xlabel("time (ms)")
        plt.ylabel("amplitude")
        plt.show()


# Display results in animated demonstration
def demo(x_source, y_sources, colors=[], titles=[], ylims=[]):
    def animate(i):
        x = x_source[i]
        xdata.append(x)
        for plot in range(num_plots):
            y = y_sources[plot]["source"][i]
            ydata[plot].append(y)
            lines[plot].set_data(xdata, ydata[plot])
        return lines

    def toggleAnimation(event):
        global pause
        pause ^= True
        if pause:
            anim.event_source.stop()
        else:
            anim.event_source.start()

    duration = len(x_source)
    num_plots = len(y_sources)

    if num_plots == 1:
        fig = plt.figure()
        ax = plt.axes(xlim=(0, duration), ylim=ylims)
        (line,) = ax.plot([], [], lw=2)
        line.set_data([], [])
        lines = [line]

    elif num_plots > 1:
        fig, axes = plt.subplots(num_plots, 1)
        lines = []
        for ax in axes:
            (line,) = ax.plot([], [], lw=2)
            lines.append(line)

            ax.set_xlim([0, duration])
            # ax.set_xticks([])
            # ax.set_yticks([])

    for i in range(num_plots):
        plt.subplot(num_plots, 1, i + 1)
        plt.title(y_sources[i]["name"])
        lines[i].set_color(y_sources[i]["color"])

    xdata = []
    ydata = [[] for i in range(num_plots)]  # initialize N empty lists

    fig.canvas.mpl_connect("button_press_event", toggleAnimation)

    print("Ready")

    anim = animation.FuncAnimation(
        fig, animate, frames=duration, interval=1, blit=True, repeat=False
    )

    plt.show()


def add_source(
    sources, series, source_name="", source_color="blue", source_lim=[-0.2, 1.2]
):
    new_source = {
        "source": series,
        "color": source_color,
        "name": source_name,
        "ylim": source_lim,
    }
    sources.append(new_source)
    return sources


# Display results in static manner
def display(x_source, y_sources, title, colors=[], titles=[], ylims=[]):
    duration = len(x_source)
    num_plots = len(y_sources)
    figsize = (8, 8)
    if num_plots == 1:
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(xlim=(0, duration), ylim=y_sources[0]["ylim"])
        axes = [ax]
    else:
        fig, axes = plt.subplots(num_plots, 1, figsize=figsize)


    for i in range(num_plots):
        axes[i].plot(x_source, y_sources[i]["source"], linewidth="1", color=y_sources[i]["color"])

        axes[i].set_ylabel(y_sources[i]["name"])
        axes[i].set_yticks([])
        if i < num_plots - 1:
            axes[i].set_xticks([])
            None

    plt.xlabel("time (ms)")
    plt.suptitle(title)
    fig.tight_layout(pad=1)

    plt.show(block=False)
