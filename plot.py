import pathlib

import matplotlib.pyplot as plt
import numpy as np
import logging
import seaborn as sns
import colorcet as cc
import pandas as pd
import helper as hlp


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
    plt.xlabel("Date")
    plt.ylabel(ylabel)
    plt.xticks(ticks=range(num_time_steps), labels=tick_labels, rotation=45)
    locs, x_labels = plt.xticks()
    for i, label in enumerate(x_labels):
        if i % 10 == 0:  # only keep every 10th xtick label
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
    filename = execution_id + ".png"
    plt.savefig(path / filename, bbox_inches='tight')
    plt.close("all")


def plot_contribution_distribution(ledger_repos, data_dir, figures_dir, contribution_type, top_k=-1, unit='relative',
                                   legend=False):
    """
    Plots the dynamics for each repository in terms of commit contribution
    :param ledger_repos: dictionary that contains the repositories for each ledger
    :param top_k: if > 0, then only the evolution of the top k contributors will be shown in the graph. Otherwise,
    all contributors will be plotted.
    :param unit: string that specifies whether the plots to be generated will be in absolute or relative values (i.e.
        number of contributions or share of contributions). It can be one of: absolute, relative
    """
    for ledger, repos in ledger_repos.items():
        for repo in repos:
            filename = f"{repo}_contributions_per_entity.csv"
            sample_windows, contributions_per_entity = hlp.get_contributions_per_entity_from_file(
                filepath=data_dir / filename)

            total_contributions_per_sample_window = [0] * len(sample_windows)
            for entity, contribution_values in contributions_per_entity.items():
                for sample_window_idx, ncontributions in contribution_values.items():
                    total_contributions_per_sample_window[sample_window_idx] += ncontributions

            total_contributions_per_sample_window = np.array(total_contributions_per_sample_window)
            nonzero_idx = total_contributions_per_sample_window.nonzero()[
                0]  # only keep time chunks with at least one contribution
            total_contributions_per_sample_window = total_contributions_per_sample_window[nonzero_idx]
            sample_windows = [sample_windows[i] for i in nonzero_idx]

            contributions_array = []
            for entity, contribution_values in contributions_per_entity.items():
                entity_array = []
                for sample_window_idx in nonzero_idx:
                    try:
                        entity_array.append(contribution_values[sample_window_idx])
                    except KeyError:
                        entity_array.append(0)
                contributions_array.append(entity_array)

            contributions_array = np.array(contributions_array)

            if unit == 'relative':
                contribution_shares_array = contributions_array / total_contributions_per_sample_window * 100
                values = contribution_shares_array
                ylabel = f'Share of {contribution_type} (%)'
                legend_threshold = 0 * total_contributions_per_sample_window + 5  # only show in the legend contributors that have a contribution of at least 5% in some sample window
            else:
                values = contributions_array
                ylabel = f'Number of {contribution_type}'
                legend_threshold = 0.05 * total_contributions_per_sample_window
            max_values_per_contributor = values.max(axis=1)
            labels = [f"{entity_name if len(entity_name) <= 15 else entity_name[:15] + '..'}"
                      f"({round(max_values_per_contributor[i], 1)}{'%' if unit == 'relative' else ''})" if any(
                        values[i] > legend_threshold) else f'_{entity_name}' for i, entity_name in
                      enumerate(contributions_per_entity.keys())]
            if top_k > 0:  # only keep the top k contributors (i.e. the contributors that contributed the most commits in total)
                total_value_per_contributor = values.sum(axis=1)
                top_k_idx = total_value_per_contributor.argpartition(-top_k)[-top_k:]
                values = values[top_k_idx]
                labels = [labels[i] for i in top_k_idx]

            if values.shape[1] > 1:  # only plot stack area chart if there is more than one time step
                plot_stack_area_chart(values=values,
                                      execution_id=f'{repo}_{unit}_values_top_{top_k}' if top_k > 0 else f'{repo}_{unit}_values_all',
                                      path=figures_dir, ylabel=ylabel, legend_labels=labels, tick_labels=sample_windows,
                                      legend=legend)
            else:
                # if there is only one time step, plot a doughnut chart
                data_dict = {label: value[0] for label, value in zip(labels, values)}
                plot_doughnut_chart(data_dict, filepath=figures_dir / f'{repo}_doughnut_chart.png')


def plot_comparative_metrics(ledger_repos, metrics, file, figures_dir):
    repos = [repo for repos in ledger_repos.values() for repo in repos]
    metrics_df = pd.read_csv(file, index_col='date')
    metrics_df.index = pd.to_datetime(metrics_df.index)
    colors = sns.color_palette(cc.glasbey, n_colors=len(repos))
    for metric in metrics:
        plt.figure(figsize=(10, 6))
        for i, repo in enumerate(repos):
            repo_data = metrics_df[metrics_df['ledger'] == repo][[metric]]
            plt.plot(repo_data, label=repo, marker='o', markersize=3, color=colors[i])
        plt.xlabel('Date')
        plt.ylabel(metric.replace('_', ' ').title())
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=3, fancybox=True, shadow=True)
        plt.savefig(figures_dir / f"{metric}.png", bbox_inches='tight')
        plt.close("all")


def plot_doughnut_chart(data_dict, title='', filepath='figures/doughnut_chart.png'):
    """
    Plots a doughnut chart with the data provided in the data_dict and saves it in a png file.
    :param data_dict: dictionary with the data to be plotted. The keys are the labels and the values are the values to be
    plotted.
    :param title: optional title for the plot
    :param filepath: the path where the plot will be saved
    """
    fig, ax = plt.subplots()
    plt.title(title)

    # sort the data_dict by values in descending order
    data_dict = dict(sorted(data_dict.items(), key=lambda x: x[1], reverse=True))

    labels = [(f'{label[:15]}...' if len(label) > 15 else label) for label in data_dict.keys()]
    wedges, texts = ax.pie(data_dict.values(), wedgeprops=dict(width=0.5), startangle=0)

    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

    for i, wedge in enumerate(wedges):
        fraction = (wedge.theta2 - wedge.theta1) / 360
        label_threshold = 0.02  # only show labels for the values that exceed the threshold
        if fraction > label_threshold:
            ang = (wedge.theta2 - wedge.theta1) / 2. + wedge.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            ax.annotate(labels[i], xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                        horizontalalignment=horizontalalignment, **kw)
    plt.savefig(filepath, bbox_inches='tight')


def plot(ledger_repos, metrics, commits_per_sample_window, contributor_type, contribution_type):
    contributions_per_entity_data_dir = hlp.get_output_dir(output_type='data', contribution_type=contribution_type,
                                                           contributor_type=contributor_type,
                                                           commits_per_sample_window=commits_per_sample_window,
                                                           data_type='contributions_per_entity')
    metrics_file = hlp.get_output_dir(output_type='data', contribution_type=contribution_type,
                                      contributor_type=contributor_type,
                                      commits_per_sample_window=commits_per_sample_window,
                                      data_type='metrics') / 'all_metrics.csv'
    dynamics_figures_dir = hlp.get_output_dir(output_type='figures', contribution_type=contribution_type,
                                              contributor_type=contributor_type,
                                              commits_per_sample_window=commits_per_sample_window, data_type='dynamics',
                                              mkdir=True)
    metrics_figures_dir = hlp.get_output_dir(output_type='figures', contribution_type=contribution_type,
                                             contributor_type=contributor_type,
                                             commits_per_sample_window=commits_per_sample_window, data_type='metrics',
                                             mkdir=True)

    logging.info("Plotting commit distributions for each repo..")
    plot_contribution_distribution(ledger_repos=ledger_repos, data_dir=contributions_per_entity_data_dir,
                                   figures_dir=dynamics_figures_dir, legend=False, contribution_type=contribution_type)
    logging.info("Plotting metrics..")
    if metrics_file.exists():
        plot_comparative_metrics(ledger_repos=ledger_repos, metrics=metrics, file=metrics_file,
                                 figures_dir=metrics_figures_dir)


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.INFO)
    ledger_repos = hlp.get_ledger_repos()
    metrics = hlp.get_metrics()
    commits_per_sample_window = hlp.get_commits_per_sample_window_list()
    contributor_types = hlp.get_contributor_types()
    contribution_types = hlp.get_contribution_types()
    for contribution_type in contribution_types:
        logging.info(f'Plotting by contribution type: {contribution_type}')
        for contributor_type in contributor_types:
            logging.info(f'Plotting per entity type: {contributor_type}')
            plot(ledger_repos, metrics, commits_per_sample_window, contributor_type, contribution_type)
