import utils.datasets as ds
import models.gan
import json
import numpy as np
import tensorflow as tf
import os
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as ff

hyperparameters = dict(
    num_features=12, num_epochs=2000, normalize='rescaling',
    debug=True, latent_vector_size=100,
    batch_size=1000, ns_param=.5, adpt_l=0,
    res_depth=1, dr_param=1, batch_param=1e-2,
    display_step=10, d_learning_rate=1e-3,
    reg_param=1e-3, g_learning_rate=1e-4
)

loc_name = 'net_results'
loc_str = 'results/{}/'.format(loc_name)
loc_str += '{}.json'


def get_summary(data):
    out = {}

    mats = np.array([entry['confusion_matrix'] for entry in data])

    out['avg_acc'] = np.mean([entry['accuracy'] for entry in data])
    out['std_acc'] = np.std([entry['accuracy'] for entry in data])
    out['avg_mat'] = np.mean(mats, axis=0).tolist()
    out['std_mat'] = np.std(mats, axis=0).tolist()

    return out


loc = 'results/{}'.format(loc_name)
if not os.path.exists(loc):
    os.mkdir(loc)

# exploits = ['freak', 'nginx_keyleak', 'nginx_rootdir', 'caleb']
exploits = [
    'freak', 'poodle', 'nginx_keyleak', 'nginx_rootdir', 'logjam',
    'orzhttpd_rootdir', 'orzhttpd_restore'
]

summaries = {'hyperparameters': hyperparameters}
raw_data = []
net_data = {exploit: [] for exploit in exploits}

model = models.gan.GAN(**hyperparameters)

for exploit in exploits:
    data = []

    for i in range(5):
        trX, trY = ds.load_data(
            (
                './data/ndss/ts/{}/subset_{}/train_set.csv'
            ).format(exploit, i)
        )

        model.train(trX, trY)

        for j in range(5):
            teX, teY = ds.load_data(
                (
                    './data/ndss/ts/{}/subset_{}/test_set.csv'
                ).format(exploit, j)
            )

            d = model.test(teX, teY)
            data.append(d)
            raw_data.append(d)
            net_data[exploit].append(d)

    summaries[exploit] = get_summary(data)

    with open(loc_str.format(exploit), 'w') as f:
        json.dump(data, f, indent=2)

summaries['net'] = get_summary(raw_data)

with open(loc_str.format('summary'), 'w') as f:
    json.dump(summaries, f, indent=2)

# plot data
accs = [[entry['accuracy'] for entry in net_data[ex]] for ex in exploits]

boxes = [go.Box(
    y=accs[i],
    name=exploits[i],
    boxmean='sd'
) for i in range(len(exploits))]

layout = go.Layout(
    title='ADD-GAN: Accuracy per Exploit',
    yaxis=dict(title='Accuracy (%)')
)

fig = go.Figure(data=boxes, layout=layout)
py.plot(fig, filename='add-gan-net-results')

fig = ff.create_distplot(accs, exploits, bin_size=2.5, curve_type='normal')
py.plot(fig, filename='add-gan-net-results-hist')
