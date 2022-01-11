import os
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress
from searching_for_td.convert_version_stats_to_tables import read_data


def _create_iqr_cutoffs(df, column):
    qntl_25 = df[column].quantile(0.25)
    qntl_75 = df[column].quantile(0.75)
    iqr = qntl_75 - qntl_25
    cut_off = iqr * 1.5
    cut_off_low = qntl_25 - cut_off
    cut_off_up = qntl_75 + cut_off

    return cut_off_low, cut_off_up


def filter_iqr_outliers(df, column):
    # Remove all issues for which `column` is not within 1.5*iqr
    cut_off_low, cut_off_up = _create_iqr_cutoffs(df, column)
    outlier_filter_q = (df[column] > cut_off_low) & (df[column] < cut_off_up)
    return df[outlier_filter_q]


def compute_lin_reg(df, x_col, y_col):
    y = df[y_col]
    x = pd.to_numeric(df[x_col])
    slope, intercept, _, _, _ = linregress(x, y)

    xf = np.linspace(x.min(), x.max(), 2)
    yf = slope * xf + intercept
    xf_dates = pd.to_datetime(xf)

    return slope, intercept, xf_dates, yf


def plot_data_w_lin_reg(df, x_col, y_col, out_file, connect=False, rot=None):
    fig, axs = plt.subplots()

    if connect:
        df.plot(
            x=x_col,
            y=y_col,
            ax=axs,
            linestyle=":",
            marker="o",
            rot=rot,
            legend=False,
        )
    else:
        df.plot.scatter(x=x_col, y=y_col, s=1, ax=axs, rot=rot)

    df.plot.scatter(
        x=x_col, y=y_col, s=1, ax=axs, linestyle=":", marker="o", rot=rot
    )
    axs.set_ylabel(y_col.replace("_", " ").title())
    axs.set_xlabel(x_col.replace("_", " ").title())

    slope, intercept, xf_dates, yf = compute_lin_reg(df, x_col, y_col)
    axs.plot(xf_dates, yf, c="orange")

    fig.savefig(out_file, bbox_inches="tight")
    fig.tight_layout()
    return fig, slope


def get_commit_urls(sys_name, commit_shas):
    if sys_name == "cassandra":
        commit_url = "https://github.com/apache/cassandra/commit/"
    elif sys_name == "gaffer":
        commit_url = "https://github.com/gchq/Gaffer/commit/"

    commit_urls = [commit_url + commit for commit in commit_shas]
    return commit_urls


def compute_no_open_issues(df):
    no_open_issues = []
    for dt in df.created.values:
        dt = pd.to_datetime(dt, utc=True)
        # Select those that were created before this issue but that are not
        # closed yet
        q = (df.created < dt) & ((df.resolved > dt) | (df.resolved.isnull()))
        no_open = df[q].shape[0]
        no_open_issues.append(no_open)
    df["no_open_iss"] = no_open_issues

    return df


def compute_no_contributors(sys_name):
    df_tab, _ = read_data(sys_name, "paper")

    version_ranges = list(
        zip(
            list(df_tab.release_tag.values), list(df_tab.release_tag.values)[1:]
        )
    )

    path = f"{os.getenv('HOME')}/case_systems/{sys_name}"
    cmd = f"git -C {path} rev-list --max-parents=0 HEAD"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    version_ranges.insert(
        0, (result.stdout.strip(), df_tab.release_tag.values[0])
    )

    contributors = []
    for start, end in version_ranges:
        cmd = f"git -C {path} shortlog -sn {start}^0..{end}^0 | wc -l"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        contributors.append(int(result.stdout.strip()))

    df_tab["no_contributors"] = contributors
    df_tab.release_date = pd.to_datetime(df_tab.release_date)
    return df_tab
