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
    # from params_exp_violations import *
    from params_exp_bins import *
    from matplotlib.ticker import StrMethodFormatter

    algorithm_labels = {}
    algorithm_colors = {}
    algorithm_markers = {}

    for umb_num_bin in umb_num_bins:
        algorithm_labels["umb_" + str(umb_num_bin)] = r"$f$"
        algorithm_labels["wgm_" + str(umb_num_bin)] = r"$\mathcal{B}^*$"
        algorithm_labels["wgc_" + str(umb_num_bin)] = r"$\mathcal{B}^{*}_{cal}$"
        algorithm_labels["pav_" + str(umb_num_bin)] = r"$\mathcal{B}_{pav}$"
        algorithm_colors["umb_" + str(umb_num_bin)] = "tab:green"
        algorithm_colors["wgm_" + str(umb_num_bin)] = "tab:blue"
        algorithm_colors["wgc_" + str(umb_num_bin)] = "tab:red"
        algorithm_colors["pav_" + str(umb_num_bin)] = "tab:orange"
        algorithm_markers["umb_" + str(umb_num_bin)] = 8
        algorithm_markers["wgm_" + str(umb_num_bin)] = 10
        algorithm_markers["wgc_" + str(umb_num_bin)] = 9
        algorithm_markers["pav_" + str(umb_num_bin)] = 11
    for k_idx, k in enumerate(ks):
        for z, Z_indices in enumerate(Z):

            Z_str = "_".join([str(index) for index in Z_indices])  # for one set of groups

            # plotting num bins of wgm vs umb number of bins for different umb bin numbers
            algorithms = []
            results = {}
            algorithms.append("umb")
            algorithms.append("wgm")
            algorithms.append("pav")
            algorithms.append("wgc")

            metrics = ["n_bins", "num_selected", "discriminated_against", "group_num_in_bin"]

            the_n_cal = n_cals[0]

            for umb_num_bin in umb_num_bins:
                results[umb_num_bin] = {}
                for algorithm in algorithms:
                    results[umb_num_bin][algorithm] = {}
                    for metric in metrics:
                        results[umb_num_bin][algorithm][metric] = {}
                        results[umb_num_bin][algorithm][metric]["values"] = []

            for umb_num_bin in umb_num_bins:
                for run in runs:
                    for algorithm in algorithms:
                        exp_identity_string = "_".join(
                            [Z_str, str(n_train), str(the_n_cal), lbd, str(run)])
                        result_path = os.path.join(exp_dir,
                                                   exp_identity_string + "_{}_{}_result.pkl".format(algorithm,
                                                                                                    umb_num_bin))
                        collect_results_quantitative_exp(result_path, umb_num_bin, algorithm, results, metrics, k_idx)

            for umb_num_bin in umb_num_bins:
                for run in runs:
                    n_bins_wgm = results[umb_num_bin]["wgm"]["n_bins"]["values"][run]
                    n_bins_pav = results[umb_num_bin]["pav"]["n_bins"]["values"][run]
                    n_bins_wgc = results[umb_num_bin]["wgc"]["n_bins"]["values"][run]
                    assert (n_bins_wgm >= n_bins_pav), f"{n_bins_wgm, n_bins_pav, n_bins_wgc}"
            for umb_num_bin in umb_num_bins:
                for algorithm in algorithms:
                    for metric in ["n_bins", "num_selected"]:
                        assert len(results[umb_num_bin][algorithm][metric]["values"]) == n_runs
                        results[umb_num_bin][algorithm][metric]["mean"] = np.mean(
                            results[umb_num_bin][algorithm][metric]["values"])
                        results[umb_num_bin][algorithm][metric]["std"] = np.std(
                            results[umb_num_bin][algorithm][metric]["values"], ddof=1)
                    # assert (np.array(results[umb_num_bins][algorithm][metric]["values"]) >= 0).all()
            # fig_legend = plt.figure(figsize=(fig_width,0.8))
            for idx, metric in enumerate(["n_bins", "num_selected"]):
                fig, axs = plt.subplots(1, 1)
                fig.set_size_inches(fig_width / 2, fig_height + 0.5)
                handles = []
                for algorithm in algorithms:
                    if metric == "n_bins" and algorithm == "umb":
                        continue
                    if metric == "group_num_in_bin" and (algorithm == "wgm" or algorithm == "pav"):
                        continue

                    # if (metric=="num_selected" or metric=="log_loss" or metric=="accuracy") and algorithm=="wgc":
                    #     print("here")
                    #     continue

                    mean_algorithm = np.array([results[umb_num_bin][algorithm][metric]["mean"] for umb_num_bin
                                               in umb_num_bins])
                    std_algorithm = np.array(
                        [results[umb_num_bin][algorithm][metric]["std"] / np.sqrt(n_runs) for umb_num_bin
                         in umb_num_bins])

                    line = axs.plot(umb_num_bins, mean_algorithm,
                                    linewidth=line_width,
                                    label=algorithm_labels["{}_{}".format(algorithm, str(umb_num_bins[0]))],
                                    color=algorithm_colors["{}_{}".format(algorithm, str(umb_num_bins[0]))],
                                    marker=algorithm_markers["{}_{}".format(algorithm, str(umb_num_bins[
                                                                                               0]))])  # , color=group_colors[i], marker=group_markers[i])
                    handles.append(line[0])
                    # if metric=="n_bins":
                    axs.fill_between(umb_num_bins, mean_algorithm - std_algorithm,
                                     mean_algorithm + std_algorithm, alpha=transparency,
                                     color=algorithm_colors[
                                         "{}_{}".format(algorithm, str(umb_num_bins[0]))])

                    axs.set_xticks(umb_num_bins)

                    axs.set_ylabel(metric_labels[metric])
                    axs.set_xlabel(xlabels["n_bins"])
                    # axs.set_ylim(-0.01, 0.28)
                    # if Z_indices[0] in [6,15]:
                    #     if metric=="n_bins":
                    #         axs.set_ylim(2.4, 18)
                    #         locator = ticker.MultipleLocator(4)
                    #         locator.tick_values(4, 15)
                    #     if metric=="num_selected":
                    #         axs.set_ylim(5.51, 7.7)
                    #         locator = ticker.MultipleLocator(0.5)
                    #         locator.tick_values(6, 7.5)
                    #     axs.yaxis.set_major_locator(locator)

                plt.tight_layout(rect=[0, 0, 1, 1])
                fig.savefig("./plots/exp_bins_{}_{}_{}.pdf".format(Z_indices[0], str(k), metric), format="pdf")
