import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress

from searching_for_td.preprocess_data import get_complete_issue_df
from searching_for_td.utils import (
    filter_iqr_outliers,
    compute_lin_reg,
    get_commit_urls,
    compute_no_open_issues,
    compute_no_contributors,
)


def compute_lead_t_dev(df, sys_name):
    df_small = filter_iqr_outliers(df, "t_lead_s")

    df_small["t_lead_h"] = df_small.t_lead_s / 60 / 60  # Convert it to hours
    fig, axs = plt.subplots(figsize=(6, 3))

    x_col = "resolved"
    y_col = "t_lead_h"
    df_small.plot.scatter(x=x_col, y=y_col, s=1, ax=axs, rot=0)

    axs.set_ylabel("$t_{lead}$ in hours")
    axs.set_xlabel("Ticket Close Time")

    slope, intercept, xf_dates, yf = compute_lin_reg(df_small, x_col, y_col)
    axs.plot(xf_dates, yf, c="orange")

    fig.savefig(f"data/output/{sys_name[:3]}_lead_t.png", bbox_inches="tight")

    # This code is only to generate the values used in the paper's text
    if sys_name == "cassandra":
        dt_a = "2010-01-01"
    elif sys_name == "gaffer":
        dt_a = "2016-01-01"
    dt_b = "2021-01-01"
    ya = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_a)]))[0] + intercept
    yb = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_b)]))[0] + intercept
    print(
        f"increase in h/year: {slope * (10 ** 9) * 60 * 60 * 24 * 365}",
        f"closing time {dt_a}: {ya}",
        f"closing time {dt_b}: {yb}",
    )

    return fig, slope


def compute_contribcompl_dev(df, sys_name):
    fig, axs = plt.subplots(figsize=(6, 3))

    x_col = "resolved"
    y_col = "contrib_complexity"
    df.plot.scatter(x=x_col, y=y_col, s=1, ax=axs, rot=0)

    axs.set_ylabel("Contribution Complexity")
    axs.set_xlabel("Resolved Date")

    slope, intercept, xf_dates, yf = compute_lin_reg(df, x_col, y_col)
    axs.plot(xf_dates, yf, c="orange")

    axs.set_yticks(list(range(1, 6)))
    axs.set_yticklabels(
        ["low", "moderate", "medium", "elevate", "high"], rotation=45
    )

    # This code is only to generate the values used in the paper's text
    if sys_name == "cassandra":
        dt_a = "2010-01-01"
    elif sys_name == "gaffer":
        dt_a = "2016-01-01"
    dt_b = "2021-01-01"
    ya = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_a)]))[0] + intercept
    yb = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_b)]))[0] + intercept
    print(
        f"increase in cc/year: {slope * (10 ** 9) * 60 * 60 * 24 * 365}",
        f"cc {dt_a}: {ya}",
        f"cc {dt_b}: {yb}",
    )

    fig.tight_layout()
    fig.savefig(
        f"data/output/{sys_name[:3]}_contribcompl.png", bbox_inches="tight"
    )
    return fig, slope


def compute_contribcompl_dev2(df, sys_name):
    fig, axs = plt.subplots(figsize=(6, 3))

    x_col = "month"
    y_col = "avg_contrib_compl"
    df.plot.scatter(x=x_col, y=y_col, s=1, ax=axs, rot=0)

    axs.set_ylabel("Avg. Contribution Complexity per Month")
    axs.set_xlabel("Resolved Date")

    slope, intercept, xf_dates, yf = compute_lin_reg(df, x_col, y_col)
    axs.plot(xf_dates, yf, c="orange")

    axs.set_yticks(list(range(1, 6)))
    axs.set_yticklabels(
        ["low", "moderate", "medium", "elevate", "high"], rotation=90
    )
    print("Increase in ? per ?", slope)
    fig.tight_layout()
    # fig.savefig(
    #     f"data/output/{sys_name[:3]}_contribcompl.png", bbox_inches="tight"
    # )
    return fig, slope


def create_t_lead_tab(df, sys_name):
    # pd.set_option('display.max_colwidth', None)
    df_small = filter_iqr_outliers(df, "t_lead_s")
    cols = [
        "key",
        "priority",
        "title",
        "issue_type",
        "t_lead",
        "contrib_complexity",
        "url",
        "commit_shas",
    ]
    df_tab = df_small.sort_values("t_lead", ascending=False)[cols].head(20)
    df_tab["commit_shas"] = df_tab["commit_shas"].apply(
        (lambda x: "<br>".join(get_commit_urls(sys_name, x)))
    )
    df_tab["description"] = ["_descr_" for i in range(df_tab.shape[0])]
    df_tab["is_td"] = ["_yes/no_" for i in range(df_tab.shape[0])]

    with open(f"data/processing/{sys_name[:3]}_t_lead_longest.md", "w") as fp:
        fp.write(df_tab.to_markdown(index=False))


def create_contribcompl_tab(df, sys_name):
    cols = [
        "key",
        "priority",
        "title",
        "issue_type",
        "t_lead",
        "contrib_complexity",
        "url",
        "commit_shas",
    ]
    df_5 = df[df.contrib_complexity == 5]
    sample_length = 20 - df_5.shape[0]
    df_4 = df[df.contrib_complexity == 4].sample(sample_length)
    df_tab = pd.concat([df_5, df_4])[cols]

    df_tab["commit_shas"] = df_tab["commit_shas"].apply(
        (lambda x: "<br>".join(get_commit_urls(sys_name, x)))
    )
    df_tab["description"] = ["_descr_" for i in range(df_tab.shape[0])]
    df_tab["is_td"] = ["_yes/no_" for i in range(df_tab.shape[0])]

    with open(
        f"data/processing/{sys_name[:3]}_contribcompl_highest.md", "w"
    ) as fp:
        fp.write(df_tab.to_markdown(index=False))


def create_no_open_issues_dev(df, sys_name):
    compute_no_open_issues(df)

    fig, axs = plt.subplots(figsize=(6, 3))

    x_col = "created"
    y_col = "no_open_iss"
    df.plot.scatter(x=x_col, y=y_col, s=1, ax=axs, rot=0)

    axs.set_ylabel("Number of Open Issues")
    axs.set_xlabel("Ticket Creation Time")

    slope, intercept, xf_dates, yf = compute_lin_reg(df, x_col, y_col)
    axs.plot(xf_dates, yf, c="orange")
    fig.savefig(
        f"data/output/{sys_name[:3]}_no_open_issues.png", bbox_inches="tight"
    )

    # This code is only to generate the values used in the paper's text
    if sys_name == "cassandra":
        dt_a = "2010-01-01"
    elif sys_name == "gaffer":
        dt_a = "2016-01-01"
    dt_b = "2021-01-01"
    ya = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_a)]))[0] + intercept
    yb = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_b)]))[0] + intercept
    print(
        f"increase in open_iss/year: {slope * (10 ** 9) * 60 * 60 * 24 * 365}",
        f"no open issues {dt_a}: {ya}",
        f"no open issues {dt_b}: {yb}",
    )

    return fig, slope, intercept


def create_no_contributors_dev(sys_name):
    df = compute_no_contributors(sys_name)

    fig, axs = plt.subplots(figsize=(6, 3))

    x_col = "release_date"
    y_col = "no_contributors"
    # df.plot.scatter(x=x_col, y=y_col, s=1, ax=axs, rot=45)

    df.plot(
        x=x_col,
        y=y_col,
        ax=axs,
        linestyle=":",
        marker="o",
        rot=45,
        legend=False,
    )

    axs.set_ylabel("Number of Contributors")
    axs.set_xlabel("Release Date")

    slope, intercept, xf_dates, yf = compute_lin_reg(df, x_col, y_col)
    axs.plot(xf_dates, yf, c="orange")
    fig.savefig(
        f"data/output/{sys_name[:3]}_no_contributors.png", bbox_inches="tight"
    )

    # This code is only to generate the values used in the paper's text
    if sys_name == "cassandra":
        dt_a = "2010-01-01"
    elif sys_name == "gaffer":
        dt_a = "2016-01-01"
    dt_b = "2021-01-01"
    ya = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_a)]))[0] + intercept
    yb = slope * pd.to_numeric(pd.Series([pd.to_datetime(dt_b)]))[0] + intercept
    print(
        f"increase in contr/year: {slope * (10 ** 9) * 60 * 60 * 24 * 365}",
        f"no contributors {dt_a}: {ya}",
        f"no contributors {dt_b}: {yb}",
    )

    return fig, slope, intercept


def main(sys_name):
    df = get_complete_issue_df(sys_name)
    q = (~df.resolved.isnull()) & (df.commit_shas.astype(bool))
    print(df[q].t_lead.describe())
    compute_lead_t_dev(df[q], sys_name)
    compute_contribcompl_dev(df[q], sys_name)

    # df["month"] = df.resolved.dt.strftime("%Y-%m")
    # rows = []
    # for idx, grp in df[q].groupby("month"):  # .groups
    #     rows.append((idx, grp.contrib_complexity.mean()))
    # avg_df = pd.DataFrame(rows, columns=["month", "avg_contrib_compl"])
    # avg_df.month = avg_df.month.apply(lambda x: x + "-15")
    # avg_df.month = pd.to_datetime(avg_df.month)

    # df["quarter"] = df.resolved.dt.strftime(
    #     "%Y-"
    # ) + df.resolved.dt.quarter.astype(str)
    # rows = []
    # for idx, grp in df[q].groupby("quarter"):  # .groups
    #     rows.append((idx, grp.contrib_complexity.mean()))
    # avg_df = pd.DataFrame(rows, columns=["quarter", "avg_contrib_compl"])
    # d = {"1.0": "2", "2.0": "5", "3.0": "8", "4.0": "11"}
    # avg_df.quarter = avg_df.quarter.apply(
    #     lambda x: x.split("-")[0] + "-" + d[x.split("-")[1]] + "-15"
    # )
    # avg_df.quarter = pd.to_datetime(avg_df.quarter)

    # Look at only those that are resolved with contribution
    q = (~df.resolved.isnull()) & (df.commit_shas.astype(bool))
    create_t_lead_tab(df[q], sys_name)

    q = (~df.resolved.isnull()) & (~df.contrib_complexity.isnull())
    create_contribcompl_tab(df[q], sys_name)

    create_no_open_issues_dev(df, sys_name)
    create_no_contributors_dev(sys_name)

    # dfc = get_complete_issue_df("cassandra")
    # _, sca, ica = create_no_open_issues_dev(dfc, "cassandra")
    # _, scb, icb = create_no_contributors_dev("cassandra")

    # for y in range(12, 21):
    #     dta = f"20{y}-01-01"
    #     i = sca * pd.to_numeric(pd.Series([pd.to_datetime(dta)]))[0] + ica
    #     c = scb * pd.to_numeric(pd.Series([pd.to_datetime(dta)]))[0] + icb

    #     print(i, c, i/c)

    # dfg = get_complete_issue_df("gaffer")
    # _, scc, icc = create_no_open_issues_dev(dfg, "gaffer")
    # _, scd, icd = create_no_contributors_dev("gaffer")

    # for y in range(16, 21):
    #     dta = f"20{y}-01-01"
    #     i = scc * pd.to_numeric(pd.Series([pd.to_datetime(dta)]))[0] + icc
    #     c = scd * pd.to_numeric(pd.Series([pd.to_datetime(dta)]))[0] + icd

    #     print(i, c, i/c)


if __name__ == "__main__":
    sys_name = sys.argv[1]
    main(sys_name)
