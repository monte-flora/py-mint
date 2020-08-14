#import matplotlib
#matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import (MaxNLocator, FormatStrFormatter,
                               AutoMinorLocator)
from matplotlib import rcParams
from matplotlib.colors import ListedColormap

from ..common.utils import combine_like_features, is_outlier
import shap 


class PlotStructure:
    """
    Plot handles figure and subplot generation
    """
    # Setting the font style to serif
    rcParams['font.family'] = 'serif'
    
    # Set up the font sizes for matplotlib
    BASE_FONT_SIZE = 14

    GENERIC_FONT_SIZE_NAMES = ['teensie',
                            'tiny',
                           'small',
                           'normal',
                           'big',
                           'large',
                           'huge'
                          ] 

    FONT_SIZES_ARRAY = np.arange(-6, 8, 2) + BASE_FONT_SIZE

    FONT_SIZES = {name : size for name, size in zip(GENERIC_FONT_SIZE_NAMES,
                                  FONT_SIZES_ARRAY)} 

    plt.rc("font", size=FONT_SIZES['normal'])        # controls default text sizes
    plt.rc("axes", titlesize=FONT_SIZES['normal'])   # fontsize of the axes title
    plt.rc("axes", labelsize=FONT_SIZES['normal'])   # fontsize of the x and y labels
    plt.rc("xtick", labelsize=FONT_SIZES['teensie']) # fontsize of the x-axis tick marks
    plt.rc("ytick", labelsize=FONT_SIZES['teensie']) # fontsize of the y-axis tick marks
    plt.rc("legend", fontsize=FONT_SIZES['teensie']) # legend fontsize
    plt.rc("figure", titlesize=FONT_SIZES['big'])    # fontsize of the figure title 

    def create_subplots(self, n_panels, **kwargs):
        """
        Create a series of subplots (MxN) based on the 
        number of panels and number of columns (optionally).
        
        Args:
        -----------------------
            n_panels : int
                Number of subplots to create 
            Optional keyword args:
                n_columns : int 
                    The number of columns for a plot (default=3 for n_panels >=3)
                figsize: 2-tuple of figure size (width, height in inches) 
                wspace : float 
                    the amount of width reserved for space between subplots,
                    expressed as a fraction of the average axis width
                hspace : float
                sharex : boolean 
                sharey : boolean 
        """
        figsize = kwargs.get("figsize", (6.4, 4.8))
        wspace = kwargs.get("wspace", 0.4)
        hspace = kwargs.get("hspace", 0.3)
        sharex = kwargs.get("sharex", False)
        sharey = kwargs.get("sharey", False)

        delete = True
        if n_panels <= 3:
            n_columns = n_panels
            delete = False
        else:
            n_columns = kwargs.get("n_columns", 3)

        n_rows = int(n_panels / n_columns)
        extra_row = 0 if (n_panels % n_columns) == 0 else 1

        fig, axes = plt.subplots(
            n_rows + extra_row,
            n_columns,
            sharex=sharex,
            sharey=sharey,
            figsize=figsize,
            dpi=300,
        )
        plt.subplots_adjust(wspace=wspace, hspace=hspace)

        if delete:
            n_axes_to_delete = len(axes.flat) - n_panels

            if n_axes_to_delete > 0:
                for i in range(n_axes_to_delete):
                    fig.delaxes(axes.flat[-(i + 1)])

        return fig, axes
    
    def axes_to_iterator(self, n_panels, axes):
        """Turns axes list into iterable """
        ax_iterator = [axes] if n_panels == 1 else axes.flat
        
        return ax_iterator
    
    def set_major_axis_labels(
        self, fig, xlabel=None, ylabel_left=None, ylabel_right=None, **kwargs
    ):
        """
        Generate a single X- and Y-axis labels for 
        a series of subplot panels. E.g., 
        """
        fontsize = kwargs.get("fontsize", self.FONT_SIZES['normal'])
        labelpad = kwargs.get("labelpad", 15)

        # add a big axis, hide frame
        ax = fig.add_subplot(111, frameon=False)

        # hide tick and tick label of the big axis
        plt.tick_params(
            labelcolor="none", top=False, bottom=False, left=False, right=False
        )

        # set axes labels
        ax.set_xlabel(xlabel, fontsize=fontsize, labelpad=labelpad)
        ax.set_ylabel(ylabel_left, fontsize=fontsize, labelpad=labelpad)

        if ylabel_right is not None:
            ax_right = fig.add_subplot(1, 1, 1, sharex=ax, frameon=False)
            plt.tick_params(
                labelcolor="none", top=False, bottom=False, left=False, right=False
            )

            ax_right.yaxis.set_label_position("right")
            ax_right.set_ylabel(ylabel_right, labelpad=2*labelpad, fontsize=fontsize)
        
        return ax
    
    def set_row_labels(self, labels, axes, pos=-1):
        """
        Give a label to each row in a series of subplots
        """
        pad=1.15
        
        if np.ndim(axes) == 2:
            iterator = axes[:,pos]
        else:
            iterator = [axes[pos]]
        
        for ax, row in zip(iterator, labels):
            ax.yaxis.set_label_position("right")
            ax.annotate(row, xy=(1, 1), xytext=(pad, 0.5), xycoords = ax.transAxes, rotation=270,
                    size=8, ha='center', va='center', color='xkcd:vermillion', alpha=0.65)
    
    def add_alphabet_label(self, n_panels, axes):
        """
        A alphabet character to each subpanel.
        """
        alphabet_list = [chr(x) for x in range(ord("a"), ord("z") + 1)]

        ax_iterator = self.axes_to_iterator(n_panels, axes)
    
        for i, ax in enumerate(ax_iterator):
            ax.text(
                    0.9,
                    0.09,
                    f"({alphabet_list[i]})",
                    fontsize=10,
                    alpha=0.8,
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
    
    def calculate_ticks(self, ax, nticks, round_to=1, center=False):
        """
        Calculate the y-axis ticks marks for the line plots
        """
        upperbound = round(ax.get_ybound()[1], round_to)
        lowerbound = round(ax.get_ybound()[0], round_to)
        
        max_value = max(abs(upperbound), abs(lowerbound))
        if max_value > 10:
            round_to = 0
 
        def round_to_a_base(a_number, base=5):
            return base * round(a_number/base)

        if max_value > 5:
            max_value = round_to_a_base(max_value)
        
        if center:
            values = np.linspace(-max_value, max_value, nticks)
            values = np.round(values, round_to)
        else:
            dy = upperbound - lowerbound
            fit = np.floor(dy / (nticks - 1)) + 1
            dy_new = (nticks - 1) * fit
            values = np.linspace(lowerbound, lowerbound + dy_new, nticks)
            values = np.round(values, round_to)
            
        return values 
    
    def set_tick_labels(self, ax, feature_names, readable_feature_names):
        """
        Setting the tick labels for the tree interpreter plots. 
        """
        if isinstance(readable_feature_names, dict):
            labels = [readable_feature_names.get(feature_name, 
                                             feature_name) 
                      for feature_name in feature_names ]
        else:
            labels = readable_feature_names 
        
        labels = [fr'{l}' for l in labels] 
        ax.set_yticklabels(labels)
    
    
    def set_axis_label(self, ax, xaxis_label=None, yaxis_label = None):
        """
        Setting the x- and y-axis labels with fancy labels (and optionally 
        physical units) 
        """
        if xaxis_label is not None: 
            xaxis_label_pretty = self.readable_feature_names.get(xaxis_label, xaxis_label)
            units = self.feature_units.get(xaxis_label, '')
            if units == '':
                xaxis_label_with_units = fr'{xaxis_label_pretty}'
            else:
                xaxis_label_with_units = fr'{xaxis_label_pretty} ({units})'
        
            ax.set_xlabel(xaxis_label_with_units, fontsize=8)
        
        if yaxis_label is not None: 
            yaxis_label_pretty = self.readable_feature_names.get(yaxis_label, yaxis_label)
            units = self.feature_units.get(yaxis_label, '')
            if units == '':
                yaxis_label_with_units = fr'{yaxis_label_pretty}'
            else:
                yaxis_label_with_units = fr'{yaxis_label_pretty} ({units})'

            ax.set_ylabel(yaxis_label_with_units, fontsize=10)
        
    def set_legend(self, n_panels, fig, ax, major_ax):
        """
        Set a single legend on the bottom of a figure 
        for a set of subplots. 
        """
        handles, labels = ax.get_legend_handles_labels()
        
        if n_panels > 3:
            bbox_to_anchor=(0.5, -0.35)
        else:
            bbox_to_anchor=(0.5, -0.5)
        
        # Shrink current axis's height by 10% on the bottom
        box = major_ax.get_position()
        major_ax.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])

        # Put a legend below current axis
        major_ax.legend(handles, labels, loc='lower center', 
                        bbox_to_anchor=bbox_to_anchor,
                        fancybox=True, shadow=True, 
                        ncol=3
                       )
        
    def set_minor_ticks(self, ax):
        """
        Adds minor tick marks to the x- and y-axis to a subplot ax
        to increase readability. 
        """
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        
    def set_n_ticks(self, ax):
        """
        Set the max number of ticks per x- and y-axis for a
        subplot ax
        """
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.yaxis.set_major_locator(MaxNLocator(4))
        
    def despine_plt(self, ax):
        """
        remove all four spines of plot
        """
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
    
    def save_figure(self, fname, fig=None, bbox_inches="tight", dpi=300, aformat="png"):
        """ Saves the current figure """
        plt.savefig(fname=fname, bbox_inches=bbox_inches, dpi=dpi, format=aformat)
        if fig is not None:
            plt.closefig(fig)
    
    