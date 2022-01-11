import os
import csv
import sys
from github import Github
from github.GithubException import UnknownObjectException


def run():
    csv_writer = csv.writer(sys.stdout)
    g = Github(login_or_token=os.getenv("GITHUB_API_KEY"))
    repo = g.get_repo(sys.argv[1])
    tags = repo.get_tags()

    for line in sys.stdin:
        try:
            release_tag = line.strip()
            release = repo.get_release(release_tag)
            csv_writer.writerow((release.raw_data["published_at"], release_tag))
        except UnknownObjectException:
            # Get the date directly from the corresponding commit as some
            # releases seem to be just lightweight tags
            for tag in tags:
                if tag.name == release_tag:
                    c = tag.commit
                    published_at = c.commit.committer.raw_data["date"]
                    csv_writer.writerow((published_at, release_tag))


if __name__ == "__main__":
    run()
