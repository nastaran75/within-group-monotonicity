"""
Implementation of the partitioining framework described in Section 3 of the paper.
"""
import argparse
import pickle
import numpy as np
from umb import UMBSelect
from utils import *
from sklearn.metrics import mean_squared_error, accuracy_score, roc_curve, roc_auc_score, log_loss, f1_score


class BinPartition(UMBSelect):
    def __init__(self, n_bins, Z_indices, groups, Z_map, alpha):
        super().__init__(n_bins, Z_indices, groups, Z_map, alpha)

        # Parameters to be learned
        self.dp = None
        self.mid_point = None
        self.optimal_partition = None
        self.recal_n_bins = None
        self.recal_bin_upper_edges = None
        self.recal_num_positives_in_bin = None
        self.recal_num_in_bin = None
        self.recal_bin_values = None
        self.recal_bin_rho = None
        self.recal_group_num_positives_in_bin = None
        self.recal_group_num_in_bin = None
        self.recal_group_rho = None
        self.recal_group_bin_values = None
        self.recal_b = None
        self.recal_theta = None
        self.recal_discriminated_against = None

    def _get_merged_statistics(self, l, r):
        positives = np.sum(self.num_positives_in_bin[l:r + 1])
        total = np.sum(self.num_in_bin[l:r + 1])
        group_positives = np.sum(self.group_num_positives_in_bin[l:r + 1], axis=0)
        group_total = np.sum(self.group_num_in_bin[l:r + 1], axis=0)
        group_rho = np.average(self.group_rho[l:r + 1], axis=0)

        assert (np.sum(group_positives) == positives and np.sum(group_total) == total and np.sum(group_rho) - 1 < 1e-2)

        return positives, total, group_positives, group_total, group_rho

    def recalibrate(self):
        raise Exception("Not Implemented")

    def get_recal_bin_points(self, scores):
        assert self.recal_n_bins is not None and self.optimal_partition is not None
        recal_bin_assignment = np.empty(shape=scores.size)
        bin_assignment = self._bin_points(scores)
        in_bin = np.empty(shape=(self.recal_n_bins, scores.size))

        recal_num_in_bin = np.empty(self.recal_n_bins)
        recal_num_positives_in_bin = np.empty(self.recal_n_bins)
        recal_group_num_positives_in_bin = np.empty(shape=(self.recal_n_bins, self.num_groups))
        recal_group_num_in_bin = np.empty(shape=(self.recal_n_bins, self.num_groups))
        optimal_partition = np.append(self.optimal_partition, self.n_bins)

        for i in range(self.recal_n_bins):
            in_bin[i] = (
                np.logical_and(bin_assignment >= optimal_partition[i], bin_assignment < optimal_partition[i + 1]))
            recal_bin_assignment[in_bin[i].astype(bool)] = i
            recal_num_positives_in_bin[i] = np.sum(
                self.num_positives_in_bin[optimal_partition[i]:optimal_partition[i + 1]])
            recal_num_in_bin[i] = np.sum(self.num_in_bin[optimal_partition[i]:optimal_partition[i + 1]])
            for j in range(self.num_groups):
                recal_group_num_positives_in_bin[i][j] = np.sum(
                    self.group_num_positives_in_bin[optimal_partition[i]:optimal_partition[i + 1], j])
                recal_group_num_in_bin[i][j] = np.sum(
                    self.group_num_in_bin[optimal_partition[i]:optimal_partition[i + 1], j])

        assert (np.sum(in_bin) == scores.size), f"{np.sum(in_bin), scores.size}"
        return recal_bin_assignment.astype(
            int), recal_num_positives_in_bin, recal_num_in_bin, recal_group_num_positives_in_bin, recal_group_num_in_bin

    def find_discriminations(self):
        positive_group_rho = np.greater(self.recal_group_num_in_bin, np.zeros(shape=self.recal_group_num_in_bin.shape))
        self.recal_discriminated_against = np.zeros(shape=self.recal_group_num_in_bin.shape)
        for i in range(self.recal_n_bins):
            for j in range(self.num_groups):
                for k in range(i + 1, self.recal_n_bins):
                    if positive_group_rho[i][j] and positive_group_rho[k][j] and self.recal_bin_values[i] < \
                            self.recal_bin_values[k]:
                        self.recal_discriminated_against[i][j] = np.greater(
                            self.recal_group_num_positives_in_bin[i][j] * self.recal_group_num_in_bin[k][j],
                            self.recal_group_num_positives_in_bin[k][j] * self.recal_group_num_in_bin[i][j])
                        if self.recal_discriminated_against[i][j]:
                            break

    def sanity_check(self):

        for i in range(self.recal_n_bins):
            assert (np.sum(self.recal_group_rho[i] * self.recal_group_bin_values[i]) - self.recal_bin_values[i] < 1e-2)
            assert (self.recal_num_positives_in_bin[i] == np.sum(self.recal_group_num_positives_in_bin[i]))
            assert (self.recal_num_in_bin[i] == np.sum(self.recal_group_num_in_bin[i]))
            assert (np.sum(self.recal_group_rho[i]) - 1.0 < 1e-2)
            assert (self.recal_num_in_bin[i] > 0).all()
            for j in range(self.num_groups):
                if i < self.recal_n_bins - 1:
                    assert (self.recal_bin_values[i] <= self.recal_bin_values[i + 1])

                if self.recal_group_num_in_bin[i][j] == 0:
                    assert self.recal_group_rho[i][j] == 0
                else:
                    assert self.recal_group_rho[i][j] * self.recal_num_in_bin[i] - self.recal_group_num_in_bin[i][
                        j] < 1e-2

                if self.recal_group_num_positives_in_bin[i][j] == 0:
                    assert self.recal_group_bin_values[i][j] == 0
                else:
                    assert self.recal_group_bin_values[i][j] * self.recal_group_num_in_bin[i][j] - \
                           self.recal_group_num_positives_in_bin[i][j] < 1e-2

    def get_recal_threshold(self, m):
        # find threshold bin and theta
        assert (self.recal_num_positives_in_bin is not None and self.epsilon is not None), "Not yet recalibrated"
        recal_b = np.zeros(len(ks))
        recal_theta = np.ones(len(ks))
        for k_idx, k in enumerate(ks):
            recal_sum_scores = 0
            for i in reversed(range(self.recal_n_bins)):
                recal_sum_scores += m * (self.recal_num_positives_in_bin[i] / self.num_examples - self.epsilon)
                if recal_sum_scores >= k:
                    recal_sum_scores -= m * (self.recal_num_positives_in_bin[i] / self.num_examples - self.epsilon)
                    recal_b[k_idx] = i
                    recal_theta[k_idx] = (k - recal_sum_scores) / (
                            m * (self.recal_num_positives_in_bin[i] / self.num_examples
                                 - self.epsilon))
                    break
        return recal_b, recal_theta

    def fit(self, X_est, y_score, y, m):
        super().fit(X_est, y_score, y, m)

    def recal_select(self, scores, k_idx):
        assert (self.recal_b is not None and self.recal_theta is not None), "Not yet recalibrated"
        scores = scores.squeeze()
        size = scores.size

        # assign test data to bins
        test_bins, _, _, _, _ = self.get_recal_bin_points(scores)

        # make decisions
        s = np.zeros(size, dtype=bool)
        for i in range(size):
            if test_bins[i] > self.recal_b[k_idx]:
                s[i] = True
            elif test_bins[i] == self.recal_b[k_idx]:
                s[i] = bool(np.random.binomial(1, self.recal_theta[k_idx]))
            else:
                s[i] = False
        return s

    def recal_global_select(self, scores):
        scores = scores.squeeze()
        size = scores.size
        # assign test data to bins
        test_bins, _, _, _, _ = self.get_recal_bin_points(scores)
        # make decisions
        return self.recal_bin_values[test_bins] > 0.5

    def recal_get_test_roc(self, X, scores, y):
        assert (self.recal_bin_values is not None and self.recal_n_bins is not None), "Not yet recalibrated"
        scores = scores.squeeze()
        # assign test data to bins
        test_bins, _, _, _, _ = self.get_recal_bin_points(scores)
        y_prob = self.recal_bin_values[test_bins]
        fpr, tpr, _ = roc_curve(y, y_prob)
        return fpr, tpr

    def recal_get_group_accuracy(self, X, scores, y):
        scores = scores.squeeze()
        # assign test data to bins
        test_group_assignment = self.group_points(X).astype(bool)
        group_accuracy = np.zeros(self.num_groups)
        test_bins, _, _, _, _ = self.get_recal_bin_points(scores)
        y_prob = self.recal_bin_values[test_bins]
        y_pred = y_prob > 0.5
        for grp in range(self.num_groups):
            group_accuracy[grp] = accuracy_score(y[test_group_assignment[grp]], y_pred[test_group_assignment[grp]])

        return group_accuracy

    def recal_get_calibration_curve(self, scores, y):

        sorted_indexes = np.argsort(scores)
        y = y[sorted_indexes]
        scores = scores[sorted_indexes]
        # split scores into groups of approx equal size
        split_size = 30
        groups = np.array_split(sorted_indexes, split_size)
        scores = scores.squeeze()
        # assign test data to bins
        recal_test_bins, _, _, _, _ = self.get_recal_bin_points(scores)

        prob_pred = np.zeros(split_size)
        prob_true = np.zeros(split_size)
        ECE = np.zeros(split_size)
        for i, group in enumerate(groups):
            prob_true[i] = np.sum(y[group])
            prob_pred[i] = np.sum(self.recal_bin_values[recal_test_bins[group]])
            ECE[i] = np.abs(prob_pred[i] - prob_true[i])
        return prob_true, prob_pred, np.sum(ECE) / scores.shape[0]

    def recal_get_ECE(self, scores, y):
        from sklearn.calibration import calibration_curve
        scores = scores.squeeze()
        test_bins, _, _, _, _ = self.get_recal_bin_points(scores)
        y_pred = self.recal_bin_values[test_bins]
        prob_true, prob_pred = calibration_curve(y, y_pred, n_bins=self.n_bins, strategy='quantile')
        return np.average(np.abs(prob_true - prob_pred))

    def recal_get_sharpness(self, scores, y):
        scores = scores.squeeze()
        # assign test data to bins
        test_bins, _, _, _, _ = self.get_recal_bin_points(scores)
        var = np.zeros(self.recal_n_bins)

        for i in range(self.recal_n_bins):
            in_bin_i = (test_bins == i)
            var[i] = np.var(y[in_bin_i])
        return np.average(var)
