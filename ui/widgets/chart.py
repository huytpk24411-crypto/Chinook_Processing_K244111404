from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import pandas as pd


class RevenueChart(FigureCanvasQTAgg):
    def __init__(self, translator):
        self.figure = Figure(figsize=(8, 3), dpi=100, layout='constrained', facecolor='#ffffff')
        super().__init__(self.figure)
        self.tr = translator
        self.setMinimumHeight(210)
        self.plot()

    def plot(self, history=None, predicted=None, boundary=None):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#ffffff')
        if history is not None and len(history):
            ax.plot(history.index, history.values, color='#596775', lw=1.8, label=self.tr('history'))
        if predicted is not None and len(predicted):
            ax.plot(predicted.index, predicted.values, color='#137d89', lw=2, marker='o', ms=4,
                    label=self.tr('predicted'))
        if boundary is not None:
            ax.axvline(boundary, color='#a66b29', ls='--', lw=1.2)
            end_date = predicted.index.max() if predicted is not None and len(predicted) else boundary
            ax.axvspan(boundary, end_date, color='#137d89', alpha=.04)
        ax.set_ylabel(self.tr('unit'), fontsize=9)
        ax.set_xlabel(self.tr('month'), fontsize=9)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda n, _: self.tr.number(n, 0)))
        if history is not None and len(history):
            dates = history.index if predicted is None else history.index.union(predicted.index)
            positions = dates[::max(1, len(dates)//7)]
            ax.set_xticks(positions, [self.tr.month(pd.Timestamp(d)) for d in positions], fontsize=8)
        ax.grid(axis='y', alpha=.18)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(loc='upper left', fontsize=9, frameon=False)
        self.draw_idle()
