## What is this?

This repository contains all code and data to reproduce the experiment and results that are described in the paper _"Searching for Technical Debt – An Empirical, Exploratory, and Descriptive Case Study"_, which was presented at the [29th IEEE International Conference on Software Analysis, Evolution and Reengineering (SANER)](https://saner2022.uom.gr/) (Early Research Achievement Track).

The paper can be read [here](https://itu.dk/~ropf/blog/assets/saner2022_pfeiffer.pdf) and the presentation slides can be accessed [here](https://itu.dk/~ropf/presentations/saner2022.html).

## Citing this work:

See [CITATION.bib](https://github.com/HelgeCPH/searching-for-techdebt/blob/master/CITATION.bib).

## How to reproduce the experiment?

### a) Run the experiment locally.

If you want to run this code locally it is expected that you have a Python in at least version 3.9 installed on your computer together with [Poetry](https://python-poetry.org/).
After cloning this repository, change directory into it and run the following:

```bash
$ poetry install
$ poetry shell
(g4R_Bfrx-py3.9) $ ./experiment/run_it.sh
```

Note, the experiment should be able to run on any Linux/Unix. However, we only tested it on MacOS locally.

### b) Run the experiment remotely on DigitalOcean.

If you do not want to run the experiment locally, you can run it on a VM on DigitalOcean instead.
This requires that you have [Vagrant](https://www.vagrantup.com/) and the [Vagrant DigitalOcean Plugin](https://github.com/devopsgroup-io/vagrant-digitalocean) installed on your computer and that you are registered at DigitalOcean with an API token accessible via an environment variable `DIGITAL_OCEAN_TOKEN`.
Before starting the remote VM, remember to replace `<PUT_YOUR_KEY_HERE>` in line `'echo export GITHUB_API_KEY="<PUT_YOUR_KEY_HERE>"' >> ~/.bashrc` of the `Vagrantfile`.

Then the remote machine can be started via `vagrant up`. This will automatically run the experiment code as well. 