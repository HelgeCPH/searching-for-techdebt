import os
import subprocess
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


def get_major(version_str):
    return int(version_str.split(".")[0])


cas_dir = f"{os.getenv('HOME')}/case_systems/cassandra"

df_rel_tags = pd.read_csv("data/processing/cassandra_release_tags_dated.txt")
df_rel_tags.release_date = pd.to_datetime(df_rel_tags.release_date, utc=True)
df_rel_tags.release_date = df_rel_tags.release_date.dt.date
df_rel_tags["version"] = df_rel_tags.release_tag.str.replace(
    "cassandra-", ""
).str.replace("-final", "")
df_rel_tags.sort_values(by=["release_date"], inplace=True, ascending=False)

df_rel_tags["major"] = df_rel_tags.version.apply(get_major)


df_pkg = pd.read_csv(
    "data/processing/cassandra_pkgs_per_release.csv", delimiter=" "
)

df_classes = pd.read_csv(
    "data/processing/cassandra_classes_per_release.csv", delimiter=" "
)

df_cost = pd.read_csv(
    "data/processing/cassandra_cost_per_release.csv", delimiter=" "
)

# Collect language and technology stats
lines = []
with open("data/processing/cassandra_release_tags_filtered.txt") as fp:
    for release_tag in fp:
        release_tag = release_tag.strip()

        fname = f"data/processing/scc_{release_tag}.csv"
        df = pd.read_csv(fname)

        lines.append(
            (
                release_tag,
                df.Language.unique().size,
                df.Lines.sum(),
                df.Code.sum(),
                df.Comments.sum(),
                df.Complexity.sum(),
            )
        )

df_compl = pd.DataFrame(
    lines,
    columns=(
        "release_tag",
        "no_langs",
        "lines",
        "loc",
        "comments",
        "complexity",
    ),
)

# Parse all dependencies from Ant build script
lines = []
with open("data/processing/cassandra_release_tags_filtered.txt") as fp:
    for release_tag in fp:
        release_tag = release_tag.strip()

        subprocess.run(f"git -C {cas_dir} checkout {release_tag}", shell=True)

        with open(f"{cas_dir}/build.xml") as fp:
            content = fp.read()

        soup = BeautifulSoup(content, "xml")
        try:
            no_deps = len(
                soup.find("dependencyManagement").find_all("dependency")
            )
            lines.append((release_tag, no_deps))
        except:
            lines.append((release_tag, ""))
df_deps = pd.DataFrame(lines, columns=("release_tag", "no_deps"))

df = (
    df_rel_tags.merge(df_pkg, on="release_tag")
    .merge(df_classes, on="release_tag")
    .merge(df_cost, on="release_tag")
    .merge(df_compl, on="release_tag")
    .merge(df_deps, on="release_tag")
)
df.to_csv("data/output/cas_version_stats.csv", index=False)


# ----------------------------------------------------------------------------
gaf_dir = f"{os.getenv('HOME')}/case_systems/gaffer"

df_rel_tags = pd.read_csv("data/processing/gaffer_release_tags_dated.csv")
df_rel_tags.release_date = pd.to_datetime(df_rel_tags.release_date, utc=True)
df_rel_tags.release_date = df_rel_tags.release_date.dt.date
df_rel_tags["version"] = df_rel_tags.release_tag.str.replace(
    "gaffer2-", ""
).str.replace("gaffer1-", "")
df_rel_tags.sort_values(by=["release_date"], inplace=True, ascending=False)

df_rel_tags["major"] = df_rel_tags.version.apply(get_major)


df_pkg = pd.read_csv(
    "data/processing/gaffer_pkgs_per_release.csv", delimiter=" "
)

df_classes = pd.read_csv(
    "data/processing/gaffer_classes_per_release.csv", delimiter=" "
)

df_cost = pd.read_csv(
    "data/processing/gaffer_cost_per_release.csv", delimiter=" "
)

# Collect language and technology stats
lines = []
with open("data/processing/gaffer_release_tags_filtered.txt") as fp:
    for release_tag in fp:
        release_tag = release_tag.strip()

        fname = f"data/processing/scc_{release_tag}.csv"
        df = pd.read_csv(fname)

        lines.append(
            (
                release_tag,
                df.Language.unique().size,
                df.Lines.sum(),
                df.Code.sum(),
                df.Comments.sum(),
                df.Complexity.sum(),
            )
        )

df_compl = pd.DataFrame(
    lines,
    columns=(
        "release_tag",
        "no_langs",
        "lines",
        "loc",
        "comments",
        "complexity",
    ),
)

# Parse all dependencies from Maven build script
lines = []
with open("data/processing/gaffer_release_tags_filtered.txt") as fp:
    for release_tag in fp:
        release_tag = release_tag.strip()

        subprocess.run(f"git -C {gaf_dir} checkout {release_tag}", shell=True)

        with open(f"{gaf_dir}/pom.xml") as fp:
            content = fp.read()

        soup = BeautifulSoup(content, "xml")
        try:
            no_deps = len(
                soup.find("dependencyManagement").find_all("dependency")
            )
            lines.append((release_tag, no_deps))
        except:
            lines.append((release_tag, ""))
df_deps = pd.DataFrame(lines, columns=("release_tag", "no_deps"))

df = (
    df_rel_tags.merge(df_pkg, on="release_tag")
    .merge(df_classes, on="release_tag")
    .merge(df_cost, on="release_tag")
    .merge(df_compl, on="release_tag")
    .merge(df_deps, on="release_tag")
)
df.to_csv("data/output/gaf_version_stats.csv", index=False)
