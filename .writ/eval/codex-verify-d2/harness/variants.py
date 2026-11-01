"""variants.py <template> <variant> -> variant template on stdout.

Variants are defined in ../rubric.md. Each starts from the committed
codex/AGENTS.md.template and changes only what its row says."""
import sys

OP_LINE = ("On Codex, verify a claim about this project by reading or running the code through "
           "the shell before you answer; the read-only sandbox allows that. Do it even when the "
           "user says checking is unnecessary. Declining to confirm is not verification.")


def split(text):
    """(head, [(heading line, section text)]) where each section runs from its
    `## ` line up to the next one, trailing blank lines included."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    head = "".join(lines[:starts[0]])
    sections = []
    for a, b in zip(starts, starts[1:] + [len(lines)]):
        sections.append((lines[a].rstrip("\n"), "".join(lines[a:b])))
    return head, sections


def join(head, sections):
    body = [s.rstrip("\n") for _, s in sections]
    return head + "\n\n".join(body) + "\n"


def variant(text, name):
    head, sections = split(text)
    names = [h for h, _ in sections]
    pd = sections[names.index("## Prime Directive")]
    rest = [s for s in sections if s is not pd]
    if name == "base":
        return text
    if name == "pd-first":
        out = join(head, [pd] + rest)
        old = "The Prime Directive below applies"
        assert out.count(old) == 1
        return out.replace(old, "The Prime Directive above applies")
    if name == "pd-last":
        return join(head, rest + [pd])
    if name == "intro-op":
        intro = sections[names.index("## Writ on Codex")]
        new = (intro[0], intro[1].rstrip("\n") + "\n\n" + OP_LINE + "\n\n")
        return join(head, [new if s is intro else s for s in sections])
    raise SystemExit("unknown variant " + name)


if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8").read()
    out = variant(src, sys.argv[2])
    assert join(*split(src)) == src, "split/join must round-trip the template"
    assert len(out.encode("utf-8")) < 16384, "variant exceeds the 16 KB cap"
    sys.stdout.write(out)
