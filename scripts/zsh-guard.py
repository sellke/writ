#!/usr/bin/env python3
r"""Block four zsh pitfalls in a Bash tool command before it runs.

Dev-only: a Claude Code `PreToolUse` hook for Writ's own sessions, where the
Bash tool runs commands in zsh (retro `.writ/retros/2026-10-30-phase-15.md`
F5). It does not ship (ADR-031): install.sh, update.sh, unlink.sh and
gen-platform-trees.py list it as dev-only.

Rules, each reported with its fix:
  equals-word    an unquoted word that starts with `=` (`echo =====`, the
                 `==` of `[ a == b ]`): zsh expands `=cmd` to a command path
                 and fails with "==== not found". Fix: quote the word.
  option-glob    an unquoted glob after `=` in an option word
                 (`--include=*.py`): zsh globs the whole word and aborts with
                 "no matches found". Fix: quote the word.
  name-modifier  `$name:<letter>` where the letter is a zsh history modifier
                 (`"$dir:t"`, `$f:h`): zsh applies it, or fails on `:s`.
                 Fix: brace the name, `${dir}:t`.
  gnu-timeout    `timeout` as a command: GNU coreutils, absent on macOS
                 ("command not found: timeout"). Fix: drop it and set the
                 Bash tool's timeout parameter.

Quoted and escaped text never matches, nor does a comment, the body of a
heredoc with a quoted delimiter, `[[ ]]`, or `(( ))`. An unquoted heredoc
body is checked for name-modifier only.

Usage:
  python3 scripts/zsh-guard.py [--command TEXT]   check mode
  python3 scripts/zsh-guard.py --hook             PreToolUse hook mode

Check mode reads the hook JSON (`{"tool_input": {"command": "..."}}`) on
stdin unless --command is given, and prints the ADR-029 check shape: line 1
`pass` or `fail`, one `reason: <rule>: ...; <fix>` line per finding, and the
summary `zsh-guard: <verdict> (<n> findings)` last. Exit 0 pass, 1 fail,
2 usage error or an unreadable payload (stdout empty, message on stderr).

Hook mode follows Claude Code's PreToolUse contract instead, which decides
the exit codes: a clean command, or a tool other than Bash, exits 0 with no
output; a finding prints the same check-shaped lines on stderr, which Claude
Code hands to the agent, and exits 2 to block the call; an unreadable
payload exits 1, a non-blocking error, so the guard never blocks on its own
failure.

To wire it, add this to `.claude/settings.json` (or settings.local.json):

  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/zsh-guard.py\" --hook",
              "timeout": 10
            }
          ]
        }
      ]
    }
  }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import List, NamedTuple, Optional, Tuple

# Letters zsh 5.9 consumes after an unbraced `$name:` (measured: every other
# letter is left as literal text).
MODIFIERS = frozenset("acehlqrstuAPQ")
GLOB_CHARS = frozenset("*?[")
NAME_START = re.compile(r"[A-Za-z_]")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\+?=")
HEREDOC_MODIFIER = re.compile(r"(?<!\\)\$([A-Za-z_][A-Za-z0-9_]*|[0-9]):([%s])"
                              % "".join(sorted(MODIFIERS)))
# Words after which the next word is still in command position.
PREFIX_WORDS = frozenset(("!", "{", "if", "then", "else", "elif", "do", "while", "until",
                          "time", "exec", "command", "builtin", "nohup", "env", "sudo",
                          "nice", "noglob"))
OPERATOR_CHARS = frozenset(";&|()")
SPECIAL_PARAMS = frozenset("?*@#$!-")
REDIRECT_CHARS = frozenset("<>")


class UsageError(Exception):
    """Exit-2 conditions in check mode."""


class Finding(NamedTuple):
    offset: int
    rule: str
    text: str
    fix: str


def quoted(text: str) -> str:
    return "'%s'" % text if "'" not in text else '"%s"' % text


class Word:
    """One shell word: its characters with a quoted flag each, and where it began."""

    def __init__(self, start: int) -> None:
        self.start = start
        self.chars: List[Tuple[str, bool]] = []

    def add(self, text: str, is_quoted: bool) -> None:
        self.chars.extend((ch, is_quoted) for ch in text)

    @property
    def text(self) -> str:
        return "".join(ch for ch, _ in self.chars)

    @property
    def bare(self) -> bool:
        return all(not q for _, q in self.chars)


def matching_close(s: str, i: int, open_ch: str, close_ch: str) -> int:
    """Index just past the `close_ch` that closes the `open_ch` at s[i]; quotes skipped."""
    depth, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "'":
            end = s.find("'", i + 1)
            i = n if end < 0 else end + 1
            continue
        if ch == '"':
            i = skip_double(s, i)
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def skip_double(s: str, i: int) -> int:
    """Index just past the double-quoted string that opens at s[i]."""
    i += 1
    while i < len(s) and s[i] != '"':
        i += 2 if s[i] == "\\" else 1
    return min(i + 1, len(s))


class Scanner:
    def __init__(self, source: str, base: int = 0) -> None:
        self.s = source
        self.base = base
        self.findings: List[Finding] = []
        self.word: Optional[Word] = None
        self.cmd_pos = True
        self.redirect_target = False
        self.in_test = False      # inside [[ ]]
        self.noglob = False
        self.heredocs: List[Tuple[str, bool, bool]] = []  # delimiter, quoted, strip tabs

    # -- findings ---------------------------------------------------------------

    def add(self, offset: int, rule: str, text: str, fix: str) -> None:
        self.findings.append(Finding(self.base + offset, rule, text, fix))

    def modifier(self, offset: int, name: str, letter: str) -> None:
        self.add(offset, "name-modifier",
                 "`$%s:%s` reads :%s as a zsh history modifier on $%s" % (name, letter, letter, name),
                 "brace the name: ${%s}:%s" % (name, letter))

    # -- words ------------------------------------------------------------------

    def start_word(self, i: int) -> Word:
        if self.word is None:
            self.word = Word(i)
        return self.word

    def end_word(self) -> None:
        word, self.word = self.word, None
        if word is None or not word.chars:
            return
        text = word.text
        if self.redirect_target:
            self.redirect_target = False
            return
        first_bare = not word.chars[0][1]
        if self.cmd_pos and first_bare and ASSIGNMENT.match(text) and \
                all(not q for _, q in word.chars[:text.index("=") + 1]):
            return  # VAR=value keeps command position
        if not self.in_test and first_bare and text.startswith("=") and len(text) > 1:
            self.add(word.start, "equals-word",
                     "`%s` starts with =, which zsh expands to a command path (\"%s not found\")"
                     % (text, text[1:]),
                     "quote it: %s" % quoted(text))
        if not self.noglob and first_bare and text.startswith("-") and self.option_glob(word):
            self.add(word.start, "option-glob",
                     "`%s` holds an unquoted glob, which zsh expands and aborts on "
                     "(\"no matches found\")" % text,
                     "quote it: %s" % quoted(text))
        if self.cmd_pos and word.bare and text == "timeout":
            self.add(word.start, "gnu-timeout",
                     "`timeout` is GNU coreutils, absent on macOS (\"command not found: timeout\")",
                     "drop it and set the Bash tool's timeout parameter (milliseconds)")
        if self.cmd_pos and word.bare and text == "[[":
            self.in_test, self.cmd_pos = True, False
            return
        if self.in_test and word.bare and text == "]]":
            self.in_test = False
            return
        if self.cmd_pos and word.bare and text == "noglob":
            self.noglob = True
        if not (self.cmd_pos and word.bare and text in PREFIX_WORDS):
            self.cmd_pos = False

    @staticmethod
    def option_glob(word: Word) -> bool:
        after_equals = False
        for ch, is_quoted in word.chars:
            if after_equals and not is_quoted and ch in GLOB_CHARS:
                return True
            if ch == "=" and not is_quoted:
                after_equals = True
        return False

    def new_command(self) -> None:
        self.end_word()
        self.cmd_pos, self.redirect_target, self.noglob = True, False, False

    # -- lexing -----------------------------------------------------------------

    def scan(self) -> List[Finding]:
        s, n, i = self.s, len(self.s), 0
        while i < n:
            ch = s[i]
            if ch in " \t":
                self.end_word()
                i += 1
            elif ch == "\n":
                self.new_command()
                i = self.read_heredocs(i + 1)
            elif ch == "#" and self.word is None:
                end = s.find("\n", i)
                i = n if end < 0 else end
            elif ch == "\\":
                if s[i + 1:i + 2] == "\n":
                    i += 2
                    continue
                self.start_word(i).add(s[i + 1:i + 2], True)
                i += 2
            elif ch == "'":
                end = s.find("'", i + 1)
                end = n if end < 0 else end
                self.start_word(i).add(s[i + 1:end], True)
                i = end + 1
            elif ch == '"':
                i = self.read_double(i)
            elif ch == "`":
                end = s.find("`", i + 1)
                end = n if end < 0 else end
                self.sub_scan(s[i + 1:end], i + 1)
                self.start_word(i).add("`", True)
                i = end + 1
            elif ch == "$":
                i = self.read_dollar(i, in_double=False)
            elif ch == "(" and self.cmd_pos and self.word is None and s[i:i + 2] == "((":
                i = matching_close(s, i, "(", ")")  # (( ... )) arithmetic
                self.cmd_pos = False
            elif ch == "&" and s[i + 1:i + 2] == ">":
                i = self.read_redirect(i)
            elif ch in OPERATOR_CHARS:
                self.new_command()
                if ch == ")":
                    self.cmd_pos = False
                i += 1
            elif ch in REDIRECT_CHARS:
                i = self.read_redirect(i)
            else:
                self.start_word(i).add(ch, False)
                i += 1
        self.end_word()
        return self.findings

    def sub_scan(self, text: str, offset: int) -> None:
        inner = Scanner(text, self.base + offset)
        self.findings.extend(inner.scan())

    def read_double(self, i: int) -> int:
        s, n = self.s, len(self.s)
        word = self.start_word(i)
        i += 1
        while i < n and s[i] != '"':
            ch = s[i]
            if ch == "\\":
                word.add(s[i + 1:i + 2], True)
                i += 2
            elif ch == "$":
                i = self.read_dollar(i, in_double=True)
            elif ch == "`":
                end = s.find("`", i + 1)
                end = n if end < 0 else end
                self.sub_scan(s[i + 1:end], i + 1)
                word.add("`", True)
                i = end + 1
            else:
                word.add(ch, True)
                i += 1
        return i + 1

    def read_dollar(self, i: int, in_double: bool) -> int:
        s, n = self.s, len(self.s)
        word = self.start_word(i)
        nxt = s[i + 1:i + 2]
        if s[i + 1:i + 3] == "((":
            end = matching_close(s, i + 1, "(", ")")
            word.add(s[i:end], True)
            return end
        if nxt == "(":
            end = matching_close(s, i + 1, "(", ")")
            self.sub_scan(s[i + 2:end - 1], i + 2)
            word.add("$()", True)
            return end
        if nxt == "{":
            end = matching_close(s, i + 1, "{", "}")
            word.add(s[i:end], True)
            return end
        if nxt == "'" and not in_double:
            j = i + 2
            while j < n and s[j] != "'":
                j += 2 if s[j] == "\\" else 1
            word.add(s[i + 2:j], True)
            return j + 1
        if nxt and nxt in SPECIAL_PARAMS:
            word.add(s[i:i + 2], True)
            return i + 2
        match = NAME.match(s, i + 1)
        if match is None:
            word.add("$", True)
            return i + 1
        end = match.end()
        letter = s[end + 1:end + 2]
        if s[end:end + 1] == ":" and letter and letter in MODIFIERS:
            self.modifier(i, match.group(0), letter)
        word.add(s[i:end], True)
        return end

    def read_redirect(self, i: int) -> int:
        s = self.s
        if s.startswith("<<<", i):
            self.end_word()
            self.redirect_target = False
            return i + 3
        if s.startswith("<<", i):
            self.end_word()
            j = i + 2
            strip = s[j:j + 1] == "-"
            if strip:
                j += 1
            while s[j:j + 1] in (" ", "\t"):
                j += 1
            delim, is_quoted = [], False
            while j < len(s) and s[j] not in " \t\n;&|<>()":
                ch = s[j]
                if ch in "'\"":
                    is_quoted = True
                    end = s.find(ch, j + 1)
                    end = len(s) if end < 0 else end
                    delim.append(s[j + 1:end])
                    j = end + 1
                elif ch == "\\":
                    is_quoted = True
                    delim.append(s[j + 1:j + 2])
                    j += 2
                else:
                    delim.append(ch)
                    j += 1
            self.heredocs.append(("".join(delim), is_quoted, strip))
            return j
        # `>`, `>>`, `>|`, `<`, `&>`, `>&N`: the next word is a file, not a command.
        word = self.word
        if word is not None and word.bare and word.text.isdigit():
            self.word = None  # a file-descriptor prefix such as the 2 of 2>
        else:
            self.end_word()
        n = len(s)
        j = i + 2 if s[i] == "&" else i + 1
        while j < n and s[j] in ">|":
            j += 1
        if s[j:j + 1] == "&":
            j += 1
            if s[j:j + 1] == "-" or s[j:j + 1].isdigit():
                while j < n and (s[j].isdigit() or s[j] == "-"):
                    j += 1
                return j
        self.redirect_target = True
        return j

    def read_heredocs(self, i: int) -> int:
        s, n = self.s, len(self.s)
        pending, self.heredocs = self.heredocs, []
        for delim, is_quoted, strip in pending:
            while i < n:
                end = s.find("\n", i)
                end = n if end < 0 else end
                start, line = i, s[i:end]
                i = min(end + 1, n)
                if (line.lstrip("\t") if strip else line) == delim:
                    break
                if not is_quoted:
                    for match in HEREDOC_MODIFIER.finditer(line):
                        self.modifier(start + match.start(), match.group(1), match.group(2))
        return i


def scan(command: str) -> List[Finding]:
    return sorted(Scanner(command).scan(), key=lambda f: f.offset)


def render(findings: List[Finding]) -> List[str]:
    verdict = "fail" if findings else "pass"
    lines = [verdict]
    lines.extend("reason: %s: %s; %s" % (f.rule, f.text, f.fix) for f in findings)
    count = len(findings)
    lines.append("zsh-guard: %s (%d finding%s)" % (verdict, count, "" if count == 1 else "s"))
    return lines


def read_payload(raw: str) -> Tuple[str, str]:
    """(tool_name, command) from the PreToolUse JSON; UsageError when unreadable."""
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise UsageError("stdin is not JSON (%s)" % exc)
    if not isinstance(data, dict):
        raise UsageError("stdin JSON is not an object")
    tool = data.get("tool_name", "Bash")
    tool_input = data.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if tool == "Bash" and not isinstance(command, str):
        raise UsageError("stdin JSON has no tool_input.command string")
    return str(tool), command if isinstance(command, str) else ""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # usage errors: stderr, exit 2, stdout empty
        self.print_usage(sys.stderr)
        sys.stderr.write("zsh-guard: error: %s\n" % message)
        raise SystemExit(2)


def main(argv: Optional[List[str]] = None) -> int:
    parser = Parser(prog="zsh-guard.py", description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--command", help="check this command text instead of stdin JSON")
    parser.add_argument("--hook", action="store_true",
                        help="Claude Code PreToolUse mode: exit 2 and stderr on a finding")
    args = parser.parse_args(argv)

    if args.command is not None:
        tool, command = "Bash", args.command
    else:
        try:
            tool, command = read_payload(sys.stdin.read())
        except UsageError as exc:
            sys.stderr.write("zsh-guard: %s\n" % exc)
            return 1 if args.hook else 2

    if tool != "Bash":
        if args.hook:
            return 0
        sys.stderr.write("zsh-guard: tool_name is %s, not Bash\n" % tool)
        return 2

    lines = render(scan(command))
    if args.hook:
        if lines[0] == "pass":
            return 0
        sys.stderr.write("\n".join(lines) + "\n")
        return 2
    sys.stdout.write("\n".join(lines) + "\n")
    return 1 if lines[0] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
