import matplotlib.pyplot as plt

def my_figure():
    fig, ax = plt.subplots()
    ax.plot([1, 3, 4], [3, 2, 5])
    return fig