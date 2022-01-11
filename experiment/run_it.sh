#!/usr/bin/env bash


# ----------------------------------------------------------------------------
# Collecting input data.
# The systems from Github and the issues from Jira and Github Issues

mkdir $HOME/case_systems
CAS_DIR=$HOME/case_systems/cassandra
GAF_DIR=$HOME/case_systems/gaffer
git clone git@github.com:apache/cassandra.git $CAS_DIR
git clone git@github.com:gchq/Gaffer.git $GAF_DIR

# Download the issue tracker data to CSV files
python searching_for_td/jira_to_csv.py cassandra CASSANDRA > \
            data/input/cas_issues.csv
python searching_for_td/gh_issues_to_csv.py "gchq/gaffer" > \
            data/input/gaf_issues.csv

# ----------------------------------------------------------------------------


# Collect releases for static analysis
git -C $CAS_DIR tag > data/processing/cassandra_release_tags.txt
# Only keep 'proper' releases, i.e., no betas, RCs, etc
grep -vEe "-rc|-beta|-alpha|-deb|-2$" data/processing/cassandra_release_tags.txt | sort > data/processing/cassandra_release_tags_filtered.txt
# Since for the last two versions there is no date in the Git DB, we remove them
# directly.
echo "release_date,release_tag" > \
    data/processing/cassandra_release_tags_dated.txt
git -C $CAS_DIR for-each-ref \
    --format="%(taggerdate): %(refname)" --sort=-taggerdate refs/tags | \
    ruby -ne 'puts $_.gsub ": refs/tags/", " "' | \
    grep -vEe "-rc|-beta|-alpha|-deb|-2$" | \
    grep -vEe "cassandra-1.2.8|cassandra-1.1.11" | \
    ruby -ne 'puts $_.gsub " cassandra-", ",cassandra-"' \
    >> data/processing/cassandra_release_tags_dated.txt

# Took the missing dates from Github
# https://github.com/apache/cassandra/releases/tag/cassandra-1.1.11
# https://github.com/apache/cassandra/releases/tag/cassandra-1.2.8
echo "Apr 17 2013,cassandra-1.1.11" \
    >> data/processing/cassandra_release_tags_dated.txt
echo "Jul 28 2013,cassandra-1.2.8" \
    >> data/processing/cassandra_release_tags_dated.txt


echo "release_tag no_pkgs" > data/processing/cassandra_pkgs_per_release.csv
echo "release_tag no_classes" > data/processing/cassandra_classes_per_release.csv
echo "release_tag cost_usd cost_month cost_people" > data/processing/cassandra_cost_per_release.csv
while read release_tag; do
  git -C $CAS_DIR checkout ${release_tag}
  # Size and complexity according to SCC
  scc -fcsv $CAS_DIR > data/processing/scc_${release_tag}.csv
  # Since cost in dollar, months people is not included in CSV output get it 
  # directly from CLI output
  scc $CAS_DIR | grep Estimated | ruby -ne 'puts ((((($_.gsub "Estimated Cost to Develop ", "").gsub "Estimated Schedule Effort ", "").gsub " months", "").gsub "Estimated People Required ", "").gsub ",", "").gsub "\$", ""' | xargs echo ${release_tag} >> data/processing/cassandra_cost_per_release.csv
  # Dump all Java packages per release
  grep -hre "^package " --include *.java $CAS_DIR | ruby -ne 'puts $_.strip' | sort | uniq > data/processing/${release_tag}_pkgs.txt
  # Map release tag to number of Java packages in it
  grep -hre "^package " --include *.java $CAS_DIR | ruby -ne 'puts $_.strip' | sort | uniq | wc -l | xargs echo ${release_tag} >> data/processing/cassandra_pkgs_per_release.csv
  # Count number of classes:
  grep -hre "class " --include *.java $CAS_DIR | \
      ruby -ne 'puts $_.strip' | \
      grep -v "^*" | \
      grep -v "^//" | \
      grep -v "\.class" | \
      grep -v ";$" | \
      ruby -ne 'puts $_.split("class ")[1].split(" ")[0]' | \
      ruby -ne 'puts $_.split("<")[0]' | \
      sort | uniq | wc -l | xargs echo ${release_tag} >> data/processing/cassandra_classes_per_release.csv
done < data/processing/cassandra_release_tags_filtered.txt
# in cloc-yaml and in json the complexities seem to be missing, they are all 0

# ----------------------------------------------------------------------------

git -C $GAF_DIR tag > data/processing/gaffer_release_tags.txt
# Only keep 'proper' releases, i.e., no betas, RCs, etc
grep -vEe "-RC" data/processing/gaffer_release_tags.txt | \
    # Filter out bugfix releases
    grep -vEe "([0-9]{1,}[\.]){3}[0-9]{1,}" | \
    sort > data/processing/gaffer_release_tags_filtered.txt


# Since most dates are not stored in Git DB, we get them directly from Github
echo "release_date,release_tag" > \
    data/processing/gaffer_release_tags_dated.csv
cat data/processing/gaffer_release_tags_filtered.txt | \
    python searching_for_td/collect_release_dates_from_gh.py "gchq/Gaffer" >> \
    data/processing/gaffer_release_tags_dated.csv

echo "release_tag no_pkgs" > data/processing/gaffer_pkgs_per_release.csv
echo "release_tag no_classes" > data/processing/gaffer_classes_per_release.csv
echo "release_tag cost_usd cost_month cost_people" > data/processing/gaffer_cost_per_release.csv
while read release_tag; do
  git -C $GAF_DIR checkout ${release_tag}
  # Size and complexity according to SCC
  scc -fcsv $GAF_DIR > data/processing/scc_${release_tag}.csv
  # Since cost in dollar, months people is not included in CSV output get it 
  # directly from CLI output
  scc $GAF_DIR | grep Estimated | ruby -ne 'puts ((((($_.gsub "Estimated Cost to Develop ", "").gsub "Estimated Schedule Effort ", "").gsub " months", "").gsub "Estimated People Required ", "").gsub ",", "").gsub "\$", ""' | xargs echo ${release_tag} >> data/processing/gaffer_cost_per_release.csv
  # Dump all Java packages per release
  grep -hre "^package " --include *.java $GAF_DIR | ruby -ne 'puts $_.strip' | sort | uniq > data/processing/${release_tag}_pkgs.txt
  # Map release tag to number of Java packages in it
  grep -hre "^package " --include *.java $GAF_DIR | ruby -ne 'puts $_.strip' | sort | uniq | wc -l | xargs echo ${release_tag} >> data/processing/gaffer_pkgs_per_release.csv
  # Count number of classes:
  grep -hre "class " --include *.java $GAF_DIR | \
      ruby -ne 'puts $_.strip' | \
      grep -v "^*" | \
      grep -v "^//" | \
      grep -v "\.class" | \
      grep -v ";$" | \
      ruby -ne 'puts $_.split("class ")[1].split(" ")[0]' | \
      ruby -ne 'puts $_.split("<")[0]' | \
      sort | uniq | wc -l | xargs echo ${release_tag} >> data/processing/gaffer_classes_per_release.csv
done < data/processing/gaffer_release_tags_filtered.txt


# ----------------------------------------------------------------------------

# Consumes the files from data/processing/ and creates two files in
# data/output/cas_version_stats.csv
# data/output/gaf_version_stats.csv
python searching_for_td/collect_version_stats.py

# After iterating through history jump back to top of history
git -C $CAS_DIR checkout trunk
git -C $GAF_DIR/ checkout develop 

python searching_for_td/convert_version_stats_to_tables.py cassandra
python searching_for_td/convert_version_stats_to_tables.py gaffer

# Creates two datasets in 
# data/processing/cas_issues.csv
# data/processing/gaf_issues.csv  ... takes 35:43 on my computer
python searching_for_td/preprocess_data.py gaffer
python searching_for_td/preprocess_data.py cassandra


# The initial version that was created like in the following and then manually edited
# git -C $HOME/case_systems/cassandra/ shortlog -se | awk -F'\t' '{print $2,$3,$2,$3}' | sort > /tmp/.mailmap
cp data/manual/.mailmap $HOME/case_systems/cassandra/
cp data/manual/.mailmap_gaffer $HOME/case_systems/gaffer/.mailmap
python searching_for_td/analyze.py gaffer
# increase in h/year: 16.462737477414255 closing time 2016-01-01: 290.1358175359169 closing time 2021-01-01: 372.5397117036863
# increase in cc/year: -0.03917252572502099 cc 2016-01-01: 2.05538752226045 cc 2021-01-01: 1.8593102496587697
# increase in open_iss/year: 13.208079999075174 no open issues 2016-01-01: 44.52528985749848 no open issues 2021-01-01: 110.63806289396518
# increase in contr/year: -0.32496607413594697 no contributors 2016-01-01: 8.395133822392653 no contributors 2021-01-01: 6.7685228156902575

python searching_for_td/analyze.py cassandra
# increase in h/year: 33.990350147770414 closing time 2010-01-01: 285.88273198761976 closing time 2021-01-01: 660.0559563540351
# increase in cc/year: 0.008483450053622194 cc 2010-01-01: 1.3824317665819659 cc 2021-01-01: 1.4758194441585522
# increase in open_iss/year: 216.919944495605 no open issues 2010-01-01: -139.22368093626756 no open issues 2021-01-01: 2248.6786121687765
# increase in contr/year: 6.876676487996704 no contributors 2010-01-01: 2.784153190648283 no contributors 2021-01-01: 78.48411518728051

# # Manual preprocessing of Cassandra's contributors
# git -C $CAS_DIR shortlog -se | awk -F'\t' '{print $2,$3,$2,$3}' | sort > data/processing/.mailmap
# echo 

