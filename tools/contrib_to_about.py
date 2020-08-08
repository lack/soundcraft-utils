#!/bin/env python3

import re
import os

author_format = re.compile(
    r"^- \[(?P<name>[^]]+)]\(mailto:(?P<email>[^)]+)\)(?P<description>.*)"
)
link_format = re.compile(r"\[(?P<name>[^]]+)]\((?P<url>[^)]+)\)")


def parseMarkdown(line):
    author_match = author_format.match(line)
    if author_match is not None:
        author = author_match.groupdict()
        return f"{author['name']} <{author['email']}>{author['description']}"
    link_match = link_format.search(line)
    if link_match is not None:
        link = link_match.groupdict()
        return f"{link['name']} {link['url']}"
    return line.lstrip("- ")


contributors = {}
section = None
with open("CONTRIBUTORS.md") as contrib:
    for line in contrib:
        line = line.rstrip("\n")
        if line.startswith("- "):
            contributors[section].append(parseMarkdown(line))
        elif line.startswith("--") or len(line) == 0:
            next
        else:
            section = line
            contributors[section] = []

print(f"authors={contributors['Contributors']}")
print(f"artists={contributors['Artwork']}")

gui = "soundcraft/gui.py"
edited = f"{gui}.edited"
print(f"Editing {gui}")
with open(gui) as src, open(edited, "w") as dst:
    mode = ""
    for line in src:
        if "authors=[" in line:
            mode = "authors"
        elif "artists=[" in line:
            mode = "artists"
        if mode == "authors":
            if "]," in line:
                dst.write(f"authors={contributors['Contributors']},\n")
                mode = ""
        elif mode == "artists":
            if "]," in line:
                dst.write(f"artists={contributors['Artwork']},\n")
                mode = ""
        else:
            dst.write(line)

os.rename(edited, gui)
os.system(f"black {gui}")
