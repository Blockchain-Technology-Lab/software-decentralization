import pathlib
import matplotlib.pyplot as plt
import numpy as np
import logging
import seaborn as sns
import colorcet as cc
import pandas as pd
import helper as hlp


def plot_lines(data, x_label, y_label, filepath, xtick_labels, colors, title=''):
    data.plot(figsize=(10, 6), color=colors)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend(frameon=False)
    plt.xticks(ticks=xtick_labels.index, labels=xtick_labels, rotation=45)
    locs, x_labels = plt.xticks()
    for i, label in enumerate(x_labels):
        if i % 5 == 0:  # only keep every 5th xtick label
            continue
        label.set_visible(False)
    plt.savefig(filepath, bbox_inches='tight')


def plot_stack_area_chart(values, execution_id, path, ylabel, legend_labels, tick_labels, legend):
    """

    :param values: the data to be plotted. numpy array of shape (number of total entities, number of time steps)
    :param path: the path to save the figure to
    """
    fig = plt.figure(figsize=(6, 4))
    num_entities = values.shape[0]
    num_time_steps = values.shape[1]
    col = sns.color_palette(cc.glasbey, n_colors=num_entities)
    plt.stackplot(range(num_time_steps), values, colors=col, edgecolor='face', linewidth=0.0001, labels=legend_labels)
    plt.margins(0)
    plt.xlabel("Time")
    plt.ylabel(ylabel)
    plt.xticks(ticks=range(num_time_steps), labels=tick_labels, rotation=45)
    locs, x_labels = plt.xticks()
    for i, label in enumerate(x_labels):
        if i % 5 == 0:  # only keep every 5th xtick label
            continue
        label.set_visible(False)
    if legend:
        execution_id += '_with_legend'
        visible_legend_labels = [label for label in legend_labels if not label.startswith('_')]
        if len(visible_legend_labels) > 0:
            max_labels_per_column = 25
            ncols = len(visible_legend_labels) // (max_labels_per_column + 1) + 1
            fig.legend(loc='upper right', bbox_to_anchor=(0.9, -0.1), ncol=ncols, fancybox=True, borderpad=0.2,
                       labelspacing=0.3, handlelength=1)
    filename = "dynamics-" + execution_id + ".png"
    plt.savefig(path / filename, bbox_inches='tight')
    plt.close(fig)


def plot_dynamics(ledger_repos, data_dir, figures_dir, top_k=-1, unit='relative', legend=False):
    """
    Plots the dynamics for each repository in terms of commit contribution
    :param ledger_repos: dictionary that contains the repositories for each ledger
    :param top_k: if > 0, then only the evolution of the top k contributors will be shown in the graph. Otherwise,
    all contributors will be plotted.
    :param unit: string that specifies whether the plots to be generated will be in absolute or relative values (i.e.
        number of commits or share of commits). It can be one of: absolute, relative
    """
    for ledger, repos in ledger_repos.items():
        for repo in repos:
            filename = f"{ledger}_{repo}_commits_per_entity.csv"
            time_chunks, blocks_per_entity = hlp.get_blocks_per_entity_from_file(filepath=data_dir / filename)

            total_blocks_per_time_chunk = [0] * len(time_chunks)
            for entity, block_values in blocks_per_entity.items():
                for time_chunk, nblocks in block_values.items():
                    total_blocks_per_time_chunk[time_chunks.index(time_chunk)] += nblocks

            total_blocks_per_time_chunk = np.array(total_blocks_per_time_chunk)
            nonzero_idx = total_blocks_per_time_chunk.nonzero()[0]  # only keep time chunks with at least one block
            total_blocks_per_time_chunk = total_blocks_per_time_chunk[nonzero_idx]
            time_chunks = [time_chunks[i] for i in nonzero_idx]

            blocks_array = []
            for entity, block_values in blocks_per_entity.items():
                entity_array = []
                for time_chunk in time_chunks:
                    try:
                        entity_array.append(block_values[time_chunk])
                    except KeyError:
                        entity_array.append(0)
                blocks_array.append(entity_array)

            blocks_array = np.array(blocks_array)

            if unit == 'relative':
                block_shares_array = blocks_array / total_blocks_per_time_chunk * 100
                values = block_shares_array
                ylabel = 'Share of commits (%)'
                legend_threshold = 0 * total_blocks_per_time_chunk + 5  # only show in the legend contributors that have a contribution of at least 5% in some sample window
            else:
                values = blocks_array
                ylabel = 'Number of commits'
                legend_threshold = 0.05 * total_blocks_per_time_chunk
            max_values_per_contributor = values.max(axis=1)
            labels = [
                f"{entity_name if len(entity_name) <= 15 else entity_name[:15] + '..'}"
                f"({round(max_values_per_contributor[i], 1)}{'%' if unit == 'relative' else ''})"
                if any(values[i] > legend_threshold) else f'_{entity_name}'
                for i, entity_name in enumerate(blocks_per_entity.keys())
            ]
            if top_k > 0:  # only keep the top k contributors (i.e. the contributors that contributed the most commits in total)
                total_value_per_contributor = values.sum(axis=1)
                top_k_idx = total_value_per_contributor.argpartition(-top_k)[-top_k:]
                values = values[top_k_idx]
                labels = [labels[i] for i in top_k_idx]

            plot_stack_area_chart(
                values=values,
                execution_id=f'{ledger}_{repo}_{unit}_values_top_{top_k}' if top_k > 0 else f'{ledger}_{repo}_{unit}_values_all',
                path=figures_dir,
                ylabel=ylabel,
                legend_labels=labels,
                tick_labels=time_chunks,
                legend=legend
            )


def plot_comparative_metrics(ledger_repos, metrics, data_dir, figures_dir):
    repos = [f'{ledger}_{repo}' for ledger, repos in ledger_repos.items() for repo in repos]
    for metric in metrics:
        filename = f'{metric}.csv'
        metric_df = pd.read_csv(data_dir / filename)
        # only keep rows that contain at least one (non-nan) value in the columns that correspond to the ledgers
        metric_df = metric_df[metric_df.iloc[:, 1:].notna().any(axis=1)]
        repo_columns_to_keep = [col for col in metric_df.columns if col in repos]
        num_lines = metric_df.shape[1]
        colors = sns.color_palette(cc.glasbey, n_colors=num_lines)
        if len(repo_columns_to_keep) > 0:
            index = metric_df['sample']
            metric_df = metric_df[repo_columns_to_keep]
            plot_lines(
                data=metric_df,
                x_label='Sample',
                y_label=metric,
                filepath=figures_dir / f"{metric}.png",
                xtick_labels=index,
                colors=colors
            )


def plot_doughnut_chart(data_dict, title='', filepath='figures/doughnut_chart.png'):
    fig, ax = plt.subplots()
    plt.title(title)
    labels = [(f'{label[:15]}...' if len(label) > 15 else label) for label in data_dict.keys()]
    wedges, texts = ax.pie(data_dict.values(), wedgeprops=dict(width=0.5), startangle=0)

    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

    for i, wedge in enumerate(wedges):
        fraction = (wedge.theta2 - wedge.theta1) / 360
        label_threshold = 0.02  # only show labels for the values that exceed the threshold
        if fraction > label_threshold:
            ang = (wedge.theta2 - wedge.theta1)/2. + wedge.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            ax.annotate(labels[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                        horizontalalignment=horizontalalignment, **kw)
    plt.savefig(filepath, bbox_inches='tight')


def plot():
    ledger_repos = hlp.get_ledger_repos()
    metrics = hlp.get_metrics()
    granularity = hlp.get_granularity()
    commits_per_entity_dir = pathlib.Path(f'output/commits_per_entity_{granularity}')
    metrics_dir = pathlib.Path('output/metrics')
    dynamics_figures_dir = pathlib.Path('output/figures/dynamics')
    dynamics_figures_dir.mkdir(parents=True, exist_ok=True)
    metrics_figures_dir = pathlib.Path('output/figures/metrics')
    metrics_figures_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Plotting dynamics for each repo..")
    plot_dynamics(ledger_repos=ledger_repos, data_dir=commits_per_entity_dir, figures_dir=dynamics_figures_dir, legend=True)
    logging.info("Plotting metrics..")
    plot_comparative_metrics(ledger_repos=ledger_repos, metrics=metrics, data_dir=metrics_dir,
                             figures_dir=metrics_figures_dir)


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)
    plot()
