import sys
import numpy as np
import pandas as pd


def compute_delta_cols(df):
    # Modifies df inplace! It adds the delta columns to the end of df
    # Compute diffs for columns per across versions and add them to the df again
    delta_cols = [
        "no_pkgs",
        "no_classes",
        "cost_usd",
        "cost_month",
        "cost_people",
        "no_langs",
        "loc",
        "comments",
        "complexity",
        "no_deps",
        "no_open_issues",
        "mean_h_close",
        "median_h_close",
    ]

    for col in delta_cols:
        # Compute delta to
        delta_sr = np.round(1 / (df[col] / df[col].diff()) * 100, 1)
        delta_sr[delta_sr == -0.0] = 0
        # Move the values one position up to put them in the right row
        df[col + "_diff"] = delta_sr  # np.roll(delta_sr, -1)

    return df


def to_int_str(val):
    if np.isnan(val):
        return ""
    else:
        return str(int(val))


def clean_vals_for_printing(df):
    # round and clean values:
    df.cost_usd = (df.cost_usd / 10 ** 6).round(1)
    df.cost_month = df.cost_month.round(1)
    df.cost_people = df.cost_people.round(0).astype(int)
    df["loc"] = (df["loc"] / 1000).round(1)
    df.comments = (df.comments / 1000).round(1)
    # TODO: replace .0 when printing table
    df.no_deps = df.no_deps.apply(to_int_str)
    df.no_pkgs_diff.fillna("", inplace=True)
    df.no_classes_diff.fillna("", inplace=True)
    df.cost_usd_diff.fillna("", inplace=True)
    df.cost_month_diff.fillna("", inplace=True)
    df.cost_people_diff.fillna("", inplace=True)
    df.no_langs_diff.fillna("", inplace=True)
    df.loc_diff.fillna("", inplace=True)
    df.comments_diff.fillna("", inplace=True)
    df.complexity_diff.fillna("", inplace=True)
    df.no_deps_diff.fillna("", inplace=True)
    df.no_open_issues.fillna("", inplace=True)
    df.mean_h_close.fillna("", inplace=True)
    df.median_h_close.fillna("", inplace=True)
    df.no_open_issues_diff.fillna("", inplace=True)
    df.mean_h_close_diff.fillna("", inplace=True)
    df.median_h_close_diff.fillna("", inplace=True)


def get_arrow(val):
    if val == 0:
        arrow = ""
    elif val < 0:
        arrow = r"\downarrow"
    elif val > 0:
        arrow = r"\uparrow"

    return arrow


# Add mean&median time to close
# Add no open issues
def df_to_latex(df, label=""):
    latex_lines = []
    print_cols = [
        "loc",
        "no_pkgs",
        "no_classes",
        "complexity",
        "no_deps",
        "no_langs",
        "cost_usd",
        "cost_month",
        "cost_people",
        "no_open_issues",
        "mean_h_close",
        "median_h_close",
    ]

    l = r"\begin{tabular}" + r"{ll|llllll|lll|lll}"
    latex_lines.append(l)
    latex_lines.append(r"\toprule")
    l = r"\multicolumn{2}{c|}{} & \multicolumn{6}{c|}{Complexity} & \multicolumn{3}{c|}{Cost} & \multicolumn{3}{c}{Indirect Complexity and Cost}\\"
    latex_lines.append(l)
    l = r"\midrule"
    latex_lines.append(l)
    l = r"Rel. Date & Version & KLOC & \#Pkgs & \#Classes & Compl\textsubscript{cyclo} & \#Deps & \#Langs & USD M & Months & People & \#open iss & $t_{lead\_\mu}$ & $t_{lead\_q2}$ \\"
    latex_lines.append(l)
    latex_lines.append(r"\midrule")
    for _, row in df.sort_values("release_date").iterrows():
        l = []
        l.append(row.release_date.strftime("%b %d %y") + " & ")
        l.append(row.version + " & ")
        for col in print_cols:
            l.append(str(row[col]) + " ")

            val = row[col + "_diff"]

            if col == print_cols[-1]:
                end = r" \\"
            else:
                end = " & "
            if val == "":
                l.append("  " + end)
            else:
                minus_str = ""
                arrow = get_arrow(val)
                if val < 0:
                    minus_str = r"\text{-}"
                    val *= -1
                if str(val).endswith(".0"):
                    field = fr"{{\tiny ${arrow}{minus_str}\text{{{str(int(val))}}}$}}"
                else:
                    field = fr"{{\tiny ${arrow}{minus_str}\text{{{val}}}$}}"
                l.append(field + end)

        latex_lines.append("".join(l))
    latex_lines.append(r"\bottomrule")
    latex_lines.append(r"\end{tabular}")
    latex_lines.append(f"\label{{tab:deps_{label}}}")

    return latex_lines


def save_latex_table(fname, latex_lines):
    with open(fname, "w") as fp:
        fp.write("\n".join(latex_lines))


def create_no_open_col(df, df_iss):
    # Jira and Github call creation and resolved time columns differently.
    # Rename the columns to allow for unique code in the following
    if ("created_at" in df_iss.columns) and ("closed_at" in df_iss.columns):
        df_iss.rename(columns={"created_at": "created"}, inplace=True)
        df_iss.rename(columns={"closed_at": "resolved"}, inplace=True)

    rows = []
    for _, release_date in df.release_date.sort_values().items():
        # Make sure the release date is in UTC too, for Cassandra it is not
        # inferred from the data
        release_date = pd.to_datetime(release_date, utc=True)
        open_issues_at_date = df_iss[
            (df_iss.created < release_date)
            & ((df_iss.resolved > release_date) | (df_iss.resolved.isnull()))
        ]
        no_open_issues_at_date = open_issues_at_date.shape[0]
        rows.append(no_open_issues_at_date)

    df["no_open_issues"] = rows
    return df


def create_closing_t_col(df, df_iss):
    # Jira and Github call creation and resolved time columns differently.
    # Rename the columns to allow for unique code in the following
    if ("created_at" in df_iss.columns) and ("closed_at" in df_iss.columns):
        df_iss.rename(columns={"created_at": "created"}, inplace=True)
        df_iss.rename(columns={"closed_at": "resolved"}, inplace=True)

    rows = []
    rows2 = []
    for _, release_date in df.release_date.sort_values().items():
        release_date = pd.to_datetime(release_date, utc=True)
        closed_issues_at_date = df_iss[
            (df_iss.created < release_date) & (df_iss.resolved <= release_date)
        ]
        closing_ts = (
            closed_issues_at_date.resolved - closed_issues_at_date.created
        )

        rows.append(int(closing_ts.mean().round("h") / pd.Timedelta("1 hour")))
        rows2.append(
            int(closing_ts.median().round("h") / pd.Timedelta("1 hour"))
        )
    df["mean_h_close"] = rows
    df["median_h_close"] = rows2
    return df


def read_data(sys_name, present_type):
    if sys_name == "cassandra":
        fname_issues = "data/input/cas_issues.csv"
        fname = "data/output/cas_version_stats.csv"
        date_cols = ["created", "resolved", "updated"]
    elif sys_name == "gaffer":
        fname_issues = "data/input/gaf_issues.csv"
        fname = "data/output/gaf_version_stats.csv"
        date_cols = ["created_at", "closed_at", "updated_at"]
    else:
        print()
        sys.exit(1)
    df_iss = pd.read_csv(fname_issues, parse_dates=date_cols)
    df = pd.read_csv(fname, parse_dates=["release_date"])

    is_minor = df.version.str.endswith(".0") | (
        df.version.str.split(".").apply(len) == 2
    )
    if sys_name == "cassandra":
        df = df[(is_minor)]
        # for the paper remove versions 0.3.0 and 0.4.0 since the have the
        # same release date as 0.5.0 due to import from other vcs
        df = df[~(df.version == "0.3.0") & ~(df.version == "0.4.0")]
    elif sys_name == "gaffer":
        # Filter out a prerelease Gaffer version
        is_not_gaffer1 = ~(df.release_tag.str.startswith("gaffer1-"))
        df = df[(is_minor) & (is_not_gaffer1)]

    # Discard timestamps, keep only the date.
    df.release_date = df.release_date.dt.date
    # Sort by increasing date
    df.sort_values("release_date", inplace=True)

    return df, df_iss


def create_stats(sys_name, present_type):
    df, df_iss = read_data(sys_name, present_type)

    create_no_open_col(df, df_iss)
    create_closing_t_col(df, df_iss)

    compute_delta_cols(df)  # Inplace adding delta values
    clean_vals_for_printing(df)

    df_latex_str = df_to_latex(df, sys_name[:3])
    fname = f"data/output/{sys_name[:3]}_version_stats_tab.tex"
    save_latex_table(fname, df_latex_str)

    df.to_csv(f"data/output/{sys_name[:3]}_version_stats_tab.csv", index=False)
    return df


def main():
    sys_name = sys.argv[1]
    try:
        present_type = sys.argv[2]
    except IndexError:
        present_type = "paper"

    create_stats(sys_name, present_type)


if __name__ == "__main__":
    main()
