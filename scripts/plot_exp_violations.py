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
    from params_exp_violations import *
    from matplotlib.ticker import StrMethodFormatter

    if not os.path.exists('./plots'):
        os.mkdir('./plots')

    for umb_num_bin in umb_num_bins:
        algorithm_labels["umb_" + str(umb_num_bin)] = "UMB"
        algorithm_labels["wgm_" + str(umb_num_bin)] = "WGM"
        algorithm_labels["wgc_" + str(umb_num_bin)] = "WGC"
        algorithm_labels["pav_" + str(umb_num_bin)] = "PAV"
        algorithm_colors["umb_" + str(umb_num_bin)] = "tab:green"
        algorithm_colors["wgm_" + str(umb_num_bin)] = "tab:blue"
        algorithm_colors["wgc_" + str(umb_num_bin)] = "tab:red"
        algorithm_colors["pav_" + str(umb_num_bin)] = "tab:orange"
        algorithm_markers["umb_" + str(umb_num_bin)] = 8
        algorithm_markers["wgm_" + str(umb_num_bin)] = 10
        algorithm_markers["wgc_" + str(umb_num_bin)] = 9
        algorithm_markers["pav_" + str(umb_num_bin)] = 11

    the_run = 0
    the_n_cal = n_cals[0]  # for one calibration set
    the_umb_num_bin = umb_num_bins[0]

    algorithms = []
    algorithms.append("umb_" + str(the_umb_num_bin))
    algorithms.append("wgm_" + str(the_umb_num_bin))
    algorithms.append("pav_" + str(the_umb_num_bin))
    algorithms.append("wgc_" + str(the_umb_num_bin))

    for z, Z_indices in enumerate(Z):
        Z_str = "_".join([str(index) for index in Z_indices])  # for one set of groups
        num_groups = Z_labels[Z_indices[0]]["num_groups"]

        fig, axs = plt.subplots(len(algorithms), 1)
        fig.set_size_inches(fig_width, (fig_height) * len(algorithms))

        # plot group bin values for one run, one calibration set, for each algorithms across bin values

        results = {}
        num_bins = {}

        metrics = ["group_bin_values", "bin_values", "bin_rho", "discriminated_against"]

        handles = []
        for row, algorithm in enumerate(algorithms):
            exp_identity_string = "_".join([Z_str, str(n_train), str(the_n_cal), lbd, str(the_run)])
            result_path = os.path.join(exp_dir, exp_identity_string + "_{}_result.pkl".format(algorithm))

            with open(result_path, 'rb') as f:
                result = pickle.load(f)
            num_bins = len(result["bin_values"])
            alpha = 0
            if algorithm.startswith("wgc"):
                alpha = result["alpha"]

            discrimination_prob = np.sum(np.where(result["discriminated_against"], result["group_num_in_bin"],
                                                  np.zeros(result["group_num_in_bin"].shape)))

            for bin in range(num_bins):
                results[bin] = {}
                # results[bin][algorithm] = {}
                for metric in metrics:
                    results[bin][metric] = {}
                    results[bin][metric]["values"] = []

            for bin in range(num_bins):
                for metric in metrics:
                    results[bin][metric]["values"] = result[metric][bin]

            mean_algorithm = np.array([results[bin]["group_bin_values"]["values"] for bin
                                       in range(num_bins)])

            bin_value_algorithm = np.array([results[bin]["bin_values"]["values"] for bin
                                            in range(num_bins)])

            disc_algorithm = np.array([results[bin]["discriminated_against"]["values"] for bin
                                       in range(num_bins)])
            rho_algorithm = np.array([results[bin]["bin_rho"]["values"] for bin
                                      in range(num_bins)])

            import matplotlib.colors as mcolors

            for i in range(num_groups):
                if algorithm.startswith("wgc"):
                    axs[row].text(0.05, 0.85, s=r"$\epsilon = $" + r" {}".format(alpha), fontsize=font_size,
                                  transform=axs[row].transAxes)

                # axs[row].text(0.05,0.85,s=r"{}".format(discrimination_prob),fontsize=font_size,transform=axs[row].transAxes)

                mean = mean_algorithm[:, i]
                # std = std_algorithm[:,i]
                # alpha = alpha_algorithm[:,i]
                disc = disc_algorithm[:, i]
                # rgba_colors = np.zeros(shape=(alpha.shape[0],4))
                # rgba_colors[:,:3] = mcolors.to_rgb(group_colors[i])
                # rgba_colors[:,3] = [1 if dis else 0.7 for dis in disc]

                legend_bars = axs[row].bar(np.arange(num_bins) - ((i - 1) * 0.2), mean, align='edge',
                                           linewidth=disc, width=0.1, color=group_colors[i],
                                           label=Z_labels[Z_indices[0]][i])
                handles.append(legend_bars)

                bars = axs[row].bar(np.arange(num_bins) - ((i - 1) * 0.2), mean, align='edge',
                                    linewidth=disc, width=0.1, edgecolor='black', color=group_colors[i])

                if row == 0:
                    # legend = axs[row].legend(handles = handles, loc='lower center', bbox_to_anchor=(0.5, 0.97),ncol=2, title = Z_labels[Z_indices[0]]["feature"])
                    # plt.setp(legend.get_title(), fontsize=params['legend.fontsize'])
                    if Z_indices[0] in [6, 15]:
                        n_cols = 2
                    else:
                        n_cols = 4
                    legend = axs[row].legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.97),
                                             ncol=n_cols)

                hatch = ['//' if dis else '' for dis in disc]
                for bar, h in zip(bars, hatch):
                    bar.set_hatch(h)

                axs[row].set_xticks(range(num_bins))
                axs[row].set_xticklabels([str(round(float(label), 2)) for label in bin_value_algorithm])

                axs[row].set_yticks([])
                # axs[alg][z].set_ylim((0,1))

            axs[row].set_ylim([0.0001, 0.99])
            locator = ticker.MultipleLocator(0.25)
            locator.tick_values(0.25, 0.77)
            # axs.yaxis.set_major_locator(locator)

            axs[row].yaxis.set_major_locator(locator)
            if algorithm.startswith("umb"):
                axs[row].set_ylabel(r'$\Pr(Y=1|f(X),Z)$')
                axs[row].set_xlabel(r'$\Pr(Y=1|f(X))$')
            if algorithm.startswith("wgm"):
                axs[row].set_ylabel(r'$\Pr(Y=1|f_{\mathcal{B}^*}(X),Z)$')
                axs[row].set_xlabel(r'$\Pr(Y=1|f_{\mathcal{B}^*}(X))$')
            if algorithm.startswith("wgc"):
                axs[row].set_ylabel(r'$\Pr(Y=1|f_{\mathcal{B}^{*}_{cal}}(X),Z)$')
                axs[row].set_xlabel(r'$\Pr(Y=1|f_{\mathcal{B}^{*}_{cal}}(X))$')

            if algorithm.startswith("pav"):
                axs[row].set_ylabel(r'$\Pr(Y=1|f_{\mathcal{B}_{pav}}(X),Z)$')
                axs[row].set_xlabel(r'$\Pr(Y=1|f_{\mathcal{B}_{pav}}(X))$')

        plt.tight_layout(rect=[0, 0, 1, 1])
        fig.savefig("./plots/exp_violations_{}_{}.pdf".format(Z_indices[0], '_'.join(algorithms)), format="pdf")
