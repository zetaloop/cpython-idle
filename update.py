RESET = "\033[0m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
GRAY = "\033[90m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
print(f"{GREEN}====== CPython IDLE Update Script ======{RESET}")

import re  # noqa:E402
import subprocess  # noqa:E402

from git import Repo  # noqa:E402  # type:ignore

repo = Repo(".")
print(
    f"{YELLOW}Adding{RESET} remote upstream {MAGENTA}{UNDERLINE}https://github.com/python/cpython.git{RESET}"
)
if any(r.name == "upstream" for r in repo.remotes):
    repo.delete_remote("upstream")
repo.create_remote("upstream", "https://github.com/python/cpython.git")
print(f"{YELLOW}Fetching{RESET} upstream{GRAY}")
subprocess.run(["git", "fetch", "upstream", "--tags"], check=True)

print(f"{YELLOW}Analysing{RESET} tags")
tag_re = re.compile(r"^v3\.(\d+)\.(\d+)$")
latest = {}
for t in repo.tags:
    m = tag_re.match(t.name)
    if not m:
        continue
    minor, patch = int(m.group(1)), int(m.group(2))
    if minor < 5:  # Python>=3.5
        continue
    if minor not in latest or patch > latest[minor][0]:
        latest[minor] = (patch, t.name)
print(
    "  "
    + ", ".join(
        f"{CYAN}{UNDERLINE}v3.{m}.{latest[m][0]}{RESET}" for m in sorted(latest)
    )
)

print(f"{YELLOW}Updating{RESET} refs")
refs = []
for minor in sorted(latest):
    sha = repo.git.rev_parse(f"{latest[minor][1]}^{{commit}}")
    repo.git.update_ref(f"refs/heads/3.{minor}", sha)
    refs.append(f"refs/heads/3.{minor}")
    print(
        f"  {MAGENTA}{UNDERLINE}refs/heads/3.{minor}{RESET}"
        f" -> {CYAN}{UNDERLINE}{latest[minor][1]}{RESET}"
        f" {GRAY}{ITALIC}({sha}){RESET}"
    )
assert refs

print(f"{YELLOW}Deleting{RESET} tags{GRAY}")
subprocess.run(["git", "tag", "-d"] + [t.name for t in repo.tags], check=True)

print(f"{YELLOW}Removing{RESET} remote upstream")
repo.delete_remote("upstream")

cmd = ["uvx", "git-filter-repo", "--force", "--refs"]
for r in refs:
    cmd.append(r)
cmd += [
    "--path",
    "Lib/idlelib",
    "--path",
    "Lib/turtledemo",
    "--path-rename",
    "Lib/idlelib:idlelib",
    "--path-rename",
    "Lib/turtledemo:turtledemo",
]
print(
    f"{YELLOW}Filtering{RESET} history for {GREEN}{UNDERLINE}Lib/idlelib{RESET} and {GREEN}{UNDERLINE}Lib/turtledemo{RESET}{GRAY}"
)
subprocess.run(cmd, check=True)
print(f"{YELLOW}Cleaning{RESET} reflog{GRAY}")
subprocess.run(["git", "reflog", "expire", "--expire=now", "--all"], check=True)
print(f"{YELLOW}Cleaning{RESET} objects{GRAY}")
subprocess.run(["git", "gc", "--prune=now"], check=True)
print(f"{YELLOW}Pushing{RESET} to origin{GRAY}")
subprocess.run(["git", "push", "--force", "origin"] + refs, check=True)
print(f"{GREEN}Complete!{RESET}")
