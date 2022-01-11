import os
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
import subprocess
from contribution_complexity.metrics import compute_contrib_compl


def labels_to_list(labels):
    if labels == "[]":
        return []
    else:
        lbls = labels.replace('[Label(name="', "")
        lbls = lbls.replace('")]', "")
        lbls = lbls.replace('"), Label(name="', ",")
        return lbls.split(",")


def remove_priority(labels_lst):
    return [el for el in labels_lst if not el.startswith("p:")]


def extract_priority(labels_lst):
    for el in labels_lst:
        if el.startswith("p:"):
            return el.replace("p:", "")
    return ""


def find_commits_for_issue(path_to_repo, issue_re):

    cmd = f"git -C {path_to_repo} log --extended-regexp --grep='{issue_re}' --pretty=format:'%H'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.splitlines()


def get_complete_issue_df(sys_name):
    procfname = f"data/processing/{sys_name[:3]}_issues.csv"
    if os.path.isfile(procfname):
        date_cols = ["created", "resolved", "updated"]
        df_iss = pd.read_csv(procfname, parse_dates=date_cols)
        # parse commits again in
        df_iss.commit_shas = [
            eval(h.replace("\n", ",")) if type(h) == str else ""
            for h in df_iss.commit_shas
        ]
        df_iss.t_lead = pd.to_timedelta(df_iss.t_lead)
        return df_iss

    # For first time preprocessing
    fname_issues = f"data/input/{sys_name[:3]}_issues.csv"
    if sys_name == "cassandra":
        date_cols = ["created", "resolved", "updated"]
    elif sys_name == "gaffer":
        date_cols = ["created_at", "closed_at", "updated_at"]
    df_iss = pd.read_csv(fname_issues, parse_dates=date_cols)

    if sys_name == "cassandra":
        # Adjust priority values to same format as for Gaffer
        df_iss["priority"] = df_iss.priority.str.lower()
        df_iss.rename(columns={"description": "body"}, inplace=True)
        df_iss.status = df_iss.status.str.lower()
        # Rename resolved to closed as for Gaffer
        df_iss[df_iss.status == "resolved"].status = "closed"
        burl = "https://issues.apache.org/jira/browse/"
        df_iss["url"] = df_iss.key.apply(lambda k: burl + k)

    if sys_name == "gaffer":
        # Rename the columns to allow for unique code in the following
        df_iss.rename(columns={"created_at": "created"}, inplace=True)
        df_iss.rename(columns={"closed_at": "resolved"}, inplace=True)
        df_iss.rename(columns={"updated_at": "updated"}, inplace=True)
        df_iss.rename(columns={"number": "key"}, inplace=True)
        # df_iss.rename(columns={"labels": "issue_type"}, inplace=True)
        df_iss.rename(columns={"state": "status"}, inplace=True)
        # clean the data
        df_iss["labels"] = df_iss.labels.apply(labels_to_list)
        df_iss["issue_type"] = df_iss.labels.apply(remove_priority)
        df_iss["priority"] = df_iss.labels.apply(extract_priority)
        # Does not exist in Github Isssue tracker
        df_iss["resolution"] = df_iss.issue_type.apply(lambda _: "")

    # Compute lead time
    df_iss["t_lead"] = df_iss.resolved - df_iss.created
    df_iss["t_lead_s"] = df_iss.t_lead.dt.total_seconds()

    # df_iss = df_iss.loc[:200]

    # Find related commits
    path_to_repo = f"{os.getenv('HOME')}/case_systems/{sys_name}"
    contribcompls = []
    commit_shas_per_contrib = []
    for issue_key in tqdm(df_iss["key"].values):
        if sys_name == "cassandra":
            issue_re = f"{issue_key}( |$)"
        elif sys_name == "gaffer":
            issue_re = f"(Gh |gh-){issue_key}( |$)"

        commit_shas = find_commits_for_issue(path_to_repo, issue_re)
        commit_shas_per_contrib.append(commit_shas)

        if commit_shas:
            try:
                contribcompl = compute_contrib_compl(path_to_repo, commit_shas)
            except:
                print(
                    f"Skipping {issue_key}",
                    issue_re,
                    commit_shas,
                    type(commit_shas),
                    flush=True,
                )
                contribcompl = None
            contribcompl = contribcompl.value
        else:
            contribcompl = None
        contribcompls.append(contribcompl)

    df_iss["commit_shas"] = commit_shas_per_contrib
    # Compute Contribution Complexities ... This takes multiple hours
    df_iss["contrib_complexity"] = contribcompls

    cols = [
        "key",
        "title",
        "body",
        "created",
        "updated",
        "resolved",
        "status",
        "issue_type",
        "labels",
        "priority",
        "resolution",
        "t_lead",
        "t_lead_s",
        "url",
        "commit_shas",
        "contrib_complexity",
    ]
    np.set_printoptions(threshold=sys.maxsize)
    df_iss[cols].to_csv(procfname, index=False)

    return df_iss[cols]


def main(sys_name):
    get_complete_issue_df(sys_name)


if __name__ == "__main__":
    sys_name = sys.argv[1]
    main(sys_name)
