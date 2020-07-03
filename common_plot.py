# Para generar bytes de la img de plot "on the fly"
from io import BytesIO
# Trabajo con fechas
from datetime import timedelta, datetime
# Para random plot
from random import seed, randint
# Para hacer plots con Matplotlib
import matplotlib
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
matplotlib.use('Agg')
plt.style.use('ggplot')

def plot_common_graph(n, ylabel, pre_x, trans_x, tot_x, post_x, pre_y, trans_y, tot_y, post_y):
    pre_x_line = pre_x + trans_x
    post_x_line = tot_x + post_x
    x = pre_x_line + post_x_line
    pre_y_line = pre_y + trans_y
    post_y_line = tot_y + post_y
    y = pre_y_line + post_y_line
    hfont = {'fontname':'Microsoft Yi Baiti'}
    font = font_manager.FontProperties(family='Microsoft Yi Baiti')
    fig, ax = plt.subplots(num=n)
    plt.clf()
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=15, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.xlabel('Fecha', **hfont)
    plt.ylabel(ylabel, **hfont)
    plt.ylim(0, top=max(y) + 10)
    plt.xlim(left=x[0] + timedelta(-1), right=max(x) + timedelta(1))
    font = font_manager.FontProperties(family='Microsoft Yi Baiti')
    plt.scatter(pre_x, pre_y, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_x, trans_y, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_x, tot_y, color='green', label='Plena cuarentena')
    plt.scatter(post_x, post_y, color='blue', label='Post cuarentena')
    plt.legend(prop=font)
    try:
        plt.plot([pre_x_line[0], pre_x_line[-1]], [pre_y_line[0], pre_y_line[-1]], color='red', linestyle=':')
        plt.plot([post_x_line[0], post_x_line[-1]], [post_y_line[0], post_y_line[-1]], color='blue', linestyle=':')
    except:
        pass
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    return img

def unavailable_plot(j):
    fig, _ = plt.subplots(num=j)
    plt.clf()
    plt.tight_layout()
    plt.axis('off')
    plt.tick_params(top='off', bottom='off', left='off', right='off', labelleft='off', labelbottom='off')
    plt.text(0.5, 0.5, "Información no disponible", size=20, ha="center", va="center", bbox=dict(
        boxstyle="round",
        ec=(1., 0.2, 0.2),
        fc=(1., 0.8, 0.8),
    ))
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    return img

def random_plot(j):
    seed(datetime.now())
    n = 10
    p1 = [randint(0, 10) for _ in range(n)]
    p2 = [randint(0, 10) for _ in range(n)]
    t = [i for i in range(n)]
    fig = plt.figure(j)
    plt.clf()
    plt.margins(x=0, y=0, tight=True)
    plt.plot(t, p1, color='blue')
    plt.plot(t, p2, color='orange')
    plt.xlabel('Time')
    plt.ylabel('Value')
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    return img