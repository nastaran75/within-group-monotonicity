import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn import preprocessing as p
import numpy as np
import os
from plot_constants import *

plt.rcParams.update(params)
plt.rc('font', family='serif')

if __name__ == "__main__":
    from params_exp_discrimination import *
    from matplotlib.ticker import StrMethodFormatter

    algorithm_labels = {}
    algorithm_colors = {}
    algorithm_markers = {}

    for umb_num_bin in umb_num_bins:
        algorithm_labels["umb_" + str(umb_num_bin)] = r"$f$"
        algorithm_labels["wgm_" + str(umb_num_bin)] = r"$f_{\mathcal{B}^*}$"
        algorithm_labels["wgc_" + str(umb_num_bin)] = r"$f_{\mathcal{B}^{*}_{\epsilon-cal}}$"
        algorithm_labels["pav_" + str(umb_num_bin)] = r"$f_{\mathcal{B}_{pav}}$"
        algorithm_colors["umb_" + str(umb_num_bin)] = "tab:green"
        algorithm_colors["wgm_" + str(umb_num_bin)] = "tab:blue"
        algorithm_colors["wgc_" + str(umb_num_bin)] = "tab:red"
        algorithm_colors["pav_" + str(umb_num_bin)] = "tab:orange"
        algorithm_markers["umb_" + str(umb_num_bin)] = 8
        algorithm_markers["wgm_" + str(umb_num_bin)] = 10
        algorithm_markers["wgc_" + str(umb_num_bin)] = 9
        algorithm_markers["pav_" + str(umb_num_bin)] = 11

    # plotting num bins of wgm vs umb number of bins for different umb bin numbers
    algorithm = "umb"
    results = {}

    metrics = ["discriminated_against", "group_num_in_bin", "pool_discriminated"]

    the_n_cal = n_cals[0]

    for umb_num_bin in umb_num_bins:
        results[umb_num_bin] = {}
        for z, Z_indices in enumerate(Z):
            results[umb_num_bin][z] = {}
            for metric in metrics:
                results[umb_num_bin][z][metric] = {}
                results[umb_num_bin][z][metric]["values"] = []

    for umb_num_bin in umb_num_bins:
        for run in runs:
            for z, Z_indices in enumerate(Z):
                Z_str = "_".join([str(index) for index in Z_indices])  # for one set of groups
                exp_identity_string = "_".join(
                    [Z_str, str(n_train), str(the_n_cal), lbd, str(run)])
                result_path = os.path.join(exp_dir,
                                           exp_identity_string + "_{}_{}_result.pkl".format(algorithm,
                                                                                            umb_num_bin))
                collect_results_quantitative_exp(result_path, umb_num_bin, z, results, metrics)

    for umb_num_bin in umb_num_bins:
        for run in runs:
            for z, Z_indices in enumerate(Z):
                results[umb_num_bin][z]["pool_discriminated"]["values"][run] /= 100
                results[umb_num_bin][z]["group_num_in_bin"]["values"][run] = np.sum(
                    np.where(results[umb_num_bin][z]["discriminated_against"]["values"][run], \
                             results[umb_num_bin][z]["group_num_in_bin"]["values"][run], \
                             np.zeros(results[umb_num_bin][z]["group_num_in_bin"]["values"][run].shape))) / the_n_cal

    for umb_num_bin in umb_num_bins:
        for z, Z_indices in enumerate(Z):
            for metric in ["group_num_in_bin", "pool_discriminated"]:
                assert len(results[umb_num_bin][z][metric]["values"]) == n_runs
                results[umb_num_bin][z][metric]["mean"] = np.mean(
                    results[umb_num_bin][z][metric]["values"])
                results[umb_num_bin][z][metric]["std"] = np.std(
                    results[umb_num_bin][z][metric]["values"], ddof=1)
            # assert (np.array(results[umb_num_bins][algorithm][metric]["values"]) >= 0).all()
    # fig_legend = plt.figure(figsize=(fig_width,0.65))
    for idx, metric in enumerate(["group_num_in_bin", "pool_discriminated"]):
        fig, axs = plt.subplots(1, 1)
        fig.set_size_inches(fig_width / 2, fig_height + 0.5)
        handles = []
        for z, Z_indices in enumerate(Z):

            mean_algorithm = np.array([results[umb_num_bin][z][metric]["mean"] for umb_num_bin
                                       in umb_num_bins])

            std_algorithm = np.array([results[umb_num_bin][z][metric]["std"] / np.sqrt(n_runs) for umb_num_bin
                                      in umb_num_bins])

            line = axs.plot(umb_num_bins, mean_algorithm,
                            linewidth=line_width,
                            label=Z_labels[Z_indices[0]]["feature"],
                            color=Z_labels[Z_indices[0]]["color"],
                            marker=Z_labels[Z_indices[0]]["marker"])

            handles.append(line[0])
            # if metric=="n_bins":
            axs.fill_between(umb_num_bins, mean_algorithm - std_algorithm,
                             mean_algorithm + std_algorithm, alpha=transparency,
                             color=Z_labels[Z_indices[0]]["color"])

            axs.set_xticks(umb_num_bins)

            if metric == "group_num_in_bin":
                axs.set_ylabel(r"$p_d$", fontsize=34)
            if metric == "pool_discriminated":
                axs.set_ylabel(r"$p_{d | \mathcal{D}_{\text{pool}}}$", fontsize=34)
            axs.set_xlabel(xlabels["n_bins"])

            axs.set_ylim(-0.01, 0.28)
            locator = ticker.MultipleLocator(0.05)
            locator.tick_values(0, 0.28)
            axs.yaxis.set_major_locator(locator)

        plt.tight_layout(rect=[0, 0, 1, 1])
        fig.savefig("./plots/exp_{}.pdf".format(metric), format="pdf")
