#!/usr/bin/env python3
"""
Build Pipeline for Joydev Barua (25BTRCL298) Operating Systems Laboratory Record.
1. Writes all 62 experiment scripts across Chapters 1-21 to os_lab/chXX/.
2. Executes every single script genuinely via Python 3.14 / Git Bash and asserts exit code 0.
3. Renders high-DPI VS Code Dark+ source code PNGs and dark terminal output PNGs via Pillow.
4. Generates Joydev_Barua_25BTRCL298_OS_Lab_Record.tex and compiles twice with TinyTeX pdflatex.
5. Copies the verified PDF to the user's Desktop.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(r"C:\Users\barua\.gemini\antigravity\scratch\os-lab-report-joydev")
OS_LAB_DIR = BASE_DIR / "os_lab"
IMG_DIR = BASE_DIR / "images"
TEX_PATH = BASE_DIR / "Joydev_Barua_25BTRCL298_OS_Lab_Record.tex"
PDF_PATH = BASE_DIR / "Joydev_Barua_25BTRCL298_OS_Lab_Record.pdf"
DESKTOP_PDF = Path(r"C:\Users\barua\OneDrive\Pictures\Desktop\Joydev_Barua_25BTRCL298_OS_Lab_Record.pdf")

PYTHON_EXE = r"C:\Users\barua\AppData\Local\Python\bin\python.exe"
BASH_EXE = r"C:\Program Files\Git\bin\bash.exe"
PDFLATEX_EXE = r"C:\Users\barua\AppData\Roaming\TinyTeX\bin\windows\pdflatex.exe"

FONT_REG_PATH = r"C:\Windows\Fonts\consola.ttf"
FONT_BOLD_PATH = r"C:\Windows\Fonts\consolab.ttf"

sys.path.insert(0, str(BASE_DIR))
from experiments_part1 import CHAPTERS_PART1
from experiments_part2 import CHAPTERS_PART2, SYNTHESIS_CHAPTER

ALL_CHAPTERS = CHAPTERS_PART1 + CHAPTERS_PART2


# ---------------------------------------------------------------------------
# LaTeX Escaping & Sanitization
# ---------------------------------------------------------------------------

def tex_clean(text: str) -> str:
    """Clean prose/titles for pdflatex without disturbing intentional LaTeX commands/math."""
    s = text
    s = s.replace("\u2013", "--").replace("\u2014", "---")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", "``").replace("\u201d", "''")
    s = s.replace("\u2192", r"$\to$").replace("\u2264", r"$\le$").replace("\u2265", r"$\ge$")
    s = s.replace("\u00d7", r"$\times$")
    s = re.sub(r"(?<!\\)%", r"\\%", s)
    s = re.sub(r"(?<!\\)&", r"\\&", s)
    s = re.sub(r"(?<!\\)#", r"\\#", s)
    return s


def tex_literal(text: str) -> str:
    """Escape a plain literal (such as a filename or command) for use inside \\texttt{...}."""
    s = text.replace("\\", r"\textbackslash{}")
    for ch in ["_", "%", "&", "#", "$", "{", "}"]:
        s = s.replace(ch, "\\" + ch)
    return s


# ---------------------------------------------------------------------------
# Syntax Highlighting (VS Code Dark+ Palette)
# ---------------------------------------------------------------------------

COL_BG = (30, 30, 30)
COL_TITLEBAR = (37, 37, 38)
COL_BORDER = (62, 62, 66)
COL_GUTTER_SEP = (55, 55, 60)
COL_LINENO = (125, 133, 144)
COL_DEFAULT = (212, 212, 212)
COL_COMMENT = (106, 153, 85)
COL_STRING = (206, 145, 120)
COL_KEYWORD = (86, 156, 214)
COL_CONTROL = (197, 134, 192)
COL_BUILTIN = (220, 220, 170)
COL_NUMBER = (181, 206, 168)
COL_VAR = (156, 220, 254)

PY_KEYWORDS = {
    "def", "class", "lambda", "global", "nonlocal", "True", "False", "None",
    "and", "or", "not", "in", "is", "as", "pass", "del", "assert", "async", "await",
}
PY_CONTROL = {
    "if", "elif", "else", "for", "while", "return", "import", "from", "with",
    "try", "except", "finally", "raise", "break", "continue", "yield",
}
PY_BUILTINS = {
    "print", "len", "range", "int", "float", "str", "list", "dict", "set", "tuple",
    "sorted", "min", "max", "sum", "enumerate", "open", "input", "divmod", "map",
    "abs", "any", "all", "isinstance", "zip", "reversed", "next", "round", "format",
    "bool", "bytes", "bytearray", "hex", "ord", "chr", "super", "type", "repr",
}
BASH_KEYWORDS = {
    "if", "then", "else", "elif", "fi", "while", "do", "done", "for", "in",
    "case", "esac", "function", "echo", "read", "exit", "local", "export",
}

PY_TOKEN_RE = re.compile(
    r'(?P<comment>#[^\n]*)'
    r'|(?P<tstring>"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')'
    r'|(?P<string>[rRbBfFuU]{0,2}"(?:\\.|[^"\\])*"|[rRbBfFuU]{0,2}\'(?:\\.|[^\'\\])*\')'
    r'|(?P<number>\b0[xX][0-9a-fA-F_]+\b|\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b)'
    r'|(?P<ident>\b[A-Za-z_][A-Za-z0-9_]*\b)'
)

BASH_TOKEN_RE = re.compile(
    r'(?P<comment>#[^\n]*)'
    r'|(?P<string>"(?:\\.|[^"\\])*"|\'[^\']*\')'
    r'|(?P<var>\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\$[0-9@*?#])'
    r'|(?P<number>\b\d+\b)'
    r'|(?P<ident>\b[A-Za-z_][A-Za-z0-9_]*\b)'
)


def tokenize_line(line: str, lang: str):
    """Return list of (text, rgb_color) spans for a single source line."""
    spans = []
    pos = 0
    pattern = BASH_TOKEN_RE if lang == "bash" else PY_TOKEN_RE
    prev_ident = ""
    for m in pattern.finditer(line):
        if m.start() > pos:
            spans.append((line[pos:m.start()], COL_DEFAULT))
        kind = m.lastgroup
        tok = m.group()
        if kind == "comment":
            col = COL_COMMENT
        elif kind in ("string", "tstring"):
            col = COL_STRING
        elif kind == "number":
            col = COL_NUMBER
        elif kind == "var":
            col = COL_VAR
        elif kind == "ident":
            if lang == "bash":
                col = COL_CONTROL if tok in BASH_KEYWORDS else COL_DEFAULT
            else:
                if prev_ident in ("def", "class"):
                    col = COL_BUILTIN
                elif tok in PY_CONTROL:
                    col = COL_CONTROL
                elif tok in PY_KEYWORDS:
                    col = COL_KEYWORD
                elif tok in PY_BUILTINS:
                    col = COL_BUILTIN
                else:
                    col = COL_DEFAULT
            prev_ident = tok
        else:
            col = COL_DEFAULT
        spans.append((tok, col))
        pos = m.end()
    if pos < len(line):
        spans.append((line[pos:], COL_DEFAULT))
    return spans


def wrap_line(line: str, max_cols: int):
    if len(line) <= max_cols:
        return [line]
    chunks = []
    cur = line
    while len(cur) > max_cols:
        cut = cur.rfind(" ", 0, max_cols)
        if cut < max_cols // 2:
            cut = max_cols
        chunks.append(cur[:cut].rstrip())
        cur = "    " + cur[cut:].lstrip()
    if cur:
        chunks.append(cur)
    return chunks


def render_code_png(code: str, filename: str, lang: str, out_path: Path):
    font_reg = ImageFont.truetype(FONT_REG_PATH, 20)
    font_title = ImageFont.truetype(FONT_BOLD_PATH, 18)

    raw_lines = code.strip("\n").splitlines()
    # Build display lines with (lineno_str, text)
    display_lines = []
    max_cols = 114
    for idx, line in enumerate(raw_lines, start=1):
        wrapped = wrap_line(line, max_cols)
        for sub_i, seg in enumerate(wrapped):
            display_lines.append((str(idx) if sub_i == 0 else "", seg))

    char_w = font_reg.getbbox("M")[2] - font_reg.getbbox("M")[0]
    line_h = 27
    title_h = 40
    pad_top = 15
    pad_bot = 17
    gutter_w = 66
    pad_right = 28
    max_line_chars = max([len(seg) for _, seg in display_lines] + [64])
    width = max(1160, gutter_w + 22 + int(max_line_chars * char_w) + pad_right)
    width = min(width, 1560)
    height = title_h + pad_top + len(display_lines) * line_h + pad_bot

    img = Image.new("RGB", (width, height), COL_BG)
    draw = ImageDraw.Draw(img)

    # Border & titlebar
    draw.rectangle([0, 0, width - 1, title_h], fill=COL_TITLEBAR)
    draw.line([(0, title_h), (width, title_h)], fill=COL_BORDER, width=1)
    # Traffic-light dots
    for i, dot_col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = 22 + i * 22
        cy = title_h // 2
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=dot_col)

    title_text = f"{filename}  --  joydev@Joydev_Barua"
    tb = draw.textbbox((0, 0), title_text, font=font_title)
    tw = tb[2] - tb[0]
    draw.text(((width - tw) // 2, 10), title_text, fill=(204, 204, 204), font=font_title)

    # Gutter separator
    draw.line([(gutter_w, title_h), (gutter_w, height)], fill=COL_GUTTER_SEP, width=1)

    # Code lines
    y = title_h + pad_top
    for lineno, text in display_lines:
        if lineno:
            lb = draw.textbbox((0, 0), lineno, font=font_reg)
            lw = lb[2] - lb[0]
            draw.text((gutter_w - lw - 14, y), lineno, fill=COL_LINENO, font=font_reg)
        x = gutter_w + 18
        for span_text, col in tokenize_line(text, lang):
            draw.text((x, y), span_text, fill=col, font=font_reg)
            x += draw.textlength(span_text, font=font_reg)
        y += line_h

    # Outer border
    draw.rectangle([0, 0, width - 1, height - 1], outline=COL_BORDER, width=2)
    img.save(out_path, "PNG", optimize=True)


def render_terminal_png(ch_num: int, cmd_display: str, stdout_text: str, out_path: Path):
    font_reg = ImageFont.truetype(FONT_REG_PATH, 20)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, 20)
    font_title = ImageFont.truetype(FONT_BOLD_PATH, 18)

    term_bg = (12, 12, 12)
    term_bar = (28, 28, 30)
    term_border = (62, 62, 66)
    col_user = (63, 185, 80)     # Bold terminal green
    col_path = (88, 166, 255)    # Bold terminal blue
    col_cmd = (245, 248, 250)
    col_out = (224, 230, 237)

    ch_dir_str = f"~/os_lab/ch{ch_num:02d}"
    prompt_user = "joydev@Joydev_Barua"

    max_cols = 114
    out_lines = []
    for raw in stdout_text.rstrip("\n").splitlines():
        out_lines.extend(wrap_line(raw, max_cols))

    char_w = font_reg.getbbox("M")[2] - font_reg.getbbox("M")[0]
    line_h = 27
    title_h = 38
    pad_x = 22
    pad_top = 15
    pad_bot = 17

    prompt_len = len(prompt_user) + 1 + len(ch_dir_str) + 2 + len(cmd_display)
    max_chars = max([len(l) for l in out_lines] + [prompt_len, 66])
    width = max(1160, pad_x * 2 + int(max_chars * char_w) + 24)
    width = min(width, 1560)
    total_rows = 1 + len(out_lines) + 1  # cmd prompt + output + trailing prompt
    height = title_h + pad_top + total_rows * line_h + pad_bot

    img = Image.new("RGB", (width, height), term_bg)
    draw = ImageDraw.Draw(img)

    # Top title bar
    draw.rectangle([0, 0, width - 1, title_h], fill=term_bar)
    draw.line([(0, title_h), (width, title_h)], fill=term_border, width=1)
    for i, dot_col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = 22 + i * 22
        cy = title_h // 2
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=dot_col)
    bar_text = f"Terminal  --  {prompt_user}:{ch_dir_str}"
    tb = draw.textbbox((0, 0), bar_text, font=font_title)
    draw.text(((width - (tb[2] - tb[0])) // 2, 9), bar_text, fill=(195, 195, 195), font=font_title)

    def draw_prompt(y_pos, cmd_text="", cursor=False):
        x = pad_x
        draw.text((x, y_pos), prompt_user, fill=col_user, font=font_bold)
        x += draw.textlength(prompt_user, font=font_bold)
        draw.text((x, y_pos), ":", fill=col_out, font=font_reg)
        x += draw.textlength(":", font=font_reg)
        draw.text((x, y_pos), ch_dir_str, fill=col_path, font=font_bold)
        x += draw.textlength(ch_dir_str, font=font_bold)
        draw.text((x, y_pos), "$ ", fill=col_out, font=font_reg)
        x += draw.textlength("$ ", font=font_reg)
        if cmd_text:
            draw.text((x, y_pos), cmd_text, fill=col_cmd, font=font_reg)
            x += draw.textlength(cmd_text, font=font_reg)
        if cursor:
            draw.rectangle([x + 2, y_pos + 3, x + 13, y_pos + 23], fill=(215, 220, 225))

    y = title_h + pad_top
    draw_prompt(y, cmd_display, cursor=False)
    y += line_h
    for line in out_lines:
        draw.text((pad_x, y), line, fill=col_out, font=font_reg)
        y += line_h
    draw_prompt(y, "", cursor=True)

    draw.rectangle([0, 0, width - 1, height - 1], outline=term_border, width=2)
    img.save(out_path, "PNG", optimize=True)


# ---------------------------------------------------------------------------
# Experiment Execution Pipeline
# ---------------------------------------------------------------------------

def execute_all_experiments():
    if OS_LAB_DIR.exists():
        shutil.rmtree(OS_LAB_DIR)
    OS_LAB_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    results = {}  # sub -> (code_png_rel, out_png_rel, stdout)
    total_exps = sum(len(ch["experiments"]) for ch in ALL_CHAPTERS)
    done = 0

    for ch in ALL_CHAPTERS:
        ch_num = ch["num"]
        ch_dir = OS_LAB_DIR / f"ch{ch_num:02d}"
        ch_dir.mkdir(parents=True, exist_ok=True)

        # Write all scripts and setup files for this chapter first so dir scans see realistic files
        for exp in ch["experiments"]:
            script_path = ch_dir / exp["filename"]
            # Always write with LF so Git Bash never sees CRLF
            script_path.write_bytes(exp["code"].replace("\r\n", "\n").encode("utf-8"))
            for fname, fcontent in exp.get("setup_files", {}).items():
                (ch_dir / fname).write_bytes(fcontent.replace("\r\n", "\n").encode("utf-8"))

        # Execute each experiment genuinely
        for exp in ch["experiments"]:
            done += 1
            sub = exp["sub"]
            slug = sub.replace(".", "_")
            script_path = ch_dir / exp["filename"]
            lang = exp["lang"]
            args = exp.get("args", [])
            stdin_data = exp.get("stdin", None)

            if lang == "bash":
                cmd = [BASH_EXE, exp["filename"]] + args
            else:
                cmd = [PYTHON_EXE, str(script_path)] + args

            proc = subprocess.run(
                cmd,
                cwd=str(ch_dir),
                input=stdin_data,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=30,
            )

            if proc.returncode != 0:
                print(f"\n[ERROR] Experiment {sub} ({exp['filename']}) failed with exit code {proc.returncode}!")
                print("STDOUT:\n", proc.stdout)
                print("STDERR:\n", proc.stderr)
                sys.exit(1)

            captured = proc.stdout
            if proc.stderr.strip():
                captured = captured.rstrip("\n") + "\n" + proc.stderr

            code_png = IMG_DIR / f"code_{slug}.png"
            out_png = IMG_DIR / f"out_{slug}.png"
            render_code_png(exp["code"], exp["filename"], lang, code_png)
            render_terminal_png(ch_num, exp["cmd_display"], captured, out_png)

            results[sub] = (f"images/code_{slug}.png", f"images/out_{slug}.png", captured)
            print(f"[{done:02d}/{total_exps}] Verified Exp {sub:<4} ({exp['filename']:<26}) -> OK ({len(captured.splitlines()):2d} lines)")

    return results


# ---------------------------------------------------------------------------
# LaTeX Generation & Compilation
# ---------------------------------------------------------------------------

def generate_tex(results):
    lines = []
    lines.append(r"""\documentclass[11pt,a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[a4paper,top=0.95in,bottom=0.95in,left=0.9in,right=0.9in,headheight=18pt,headsep=18pt]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{xcolor}
\usepackage[hidelinks]{hyperref}

\definecolor{jainnavy}{RGB}{22, 48, 92}
\definecolor{slategray}{RGB}{74, 85, 104}
\definecolor{rulegray}{RGB}{180, 188, 200}

% Native LaTeX running header & footer (zero external header package dependencies)
\makeatletter
\def\ps@labpage{%
  \def\@oddhead{%
    \vbox{%
      \hbox to \textwidth{\small\textit{\textcolor{slategray}{Operating Systems Laboratory (25PCCS201)}}\hfill\textit{\textcolor{slategray}{Joydev Barua (25BTRCL298)}}}%
      \vspace{3pt}%
      \textcolor{rulegray}{\hrule height 0.5pt}%
    }%
  }%
  \def\@oddfoot{\hfill\small\thepage\hfill}%
  \let\@evenhead\@oddhead
  \let\@evenfoot\@oddfoot
}
\def\ps@plain{%
  \def\@oddhead{}%
  \def\@oddfoot{\hfill\small\thepage\hfill}%
  \let\@evenhead\@oddhead
  \let\@evenfoot\@oddfoot
}
\makeatother

\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\setcounter{tocdepth}{2}
\sloppy

\newcommand{\labexp}[2]{%
  \phantomsection%
  \addcontentsline{toc}{section}{#1\texorpdfstring{\quad}{ }#2}%
  {\raggedright\Large\bfseries\textcolor{jainnavy}{Experiment #1: #2}\par}%
  \vspace{4pt}%
}
\newcommand{\labsub}[1]{%
  \vspace{5pt}{\raggedright\normalsize\bfseries\textcolor{jainnavy}{#1}\par}\vspace{2pt}%
}

\begin{document}

% ==================== COVER PAGE ====================
\thispagestyle{empty}
\begin{center}
  \vspace*{0.4cm}
  {\LARGE\bfseries\textcolor{jainnavy}{JAIN (DEEMED-TO-BE UNIVERSITY)}}\\[0.25cm]
  {\large\textbf{Faculty of Engineering \& Technology}}\\[0.1cm]
  {\normalsize Department of Computer Science \& Engineering, Bengaluru}\\[1.1cm]

  \textcolor{jainnavy}{\rule{\textwidth}{1.8pt}}\\[0.45cm]
  {\Huge\bfseries\textcolor{jainnavy}{OPERATING SYSTEMS LABORATORY}}\\[0.35cm]
  {\Large\bfseries LABORATORY RECORD (CHAPTERS 1--21)}\\[0.3cm]
  {\normalsize\texttt{Course Code: 25PCCS201 \quad|\quad Semester: III}}\\[0.35cm]
  \textcolor{jainnavy}{\rule{\textwidth}{1.8pt}}\\[1.3cm]

  {\large\textbf{STUDENT \& ENVIRONMENT METADATA}}\\[0.35cm]
  \begin{tabular}{@{}ll@{}}
    \toprule
    \textbf{Attribute} & \textbf{Details} \\
    \midrule
    \textbf{Student Name} & \textbf{JOYDEV BARUA} \\
    \textbf{University Seat Number (USN)} & \textbf{25BTRCL298} \\
    \textbf{Program / Branch} & B.Tech (Computer Science \& Engineering) \\
    \textbf{Course Title \& Code} & Operating Systems Laboratory (\texttt{25PCCS201}) \\
    \textbf{Academic Year} & 2026--2027 \\
    \textbf{Execution Platform} & Windows 11 x86\_64 (Python 3.14 / GNU Bash) \\
    \textbf{Host Machine} & HP OMEN Laptop (\texttt{joydev@Joydev\_Barua}) \\
    \textbf{Verified Experiments} & 62 Native Implementations across 21 Chapters \\
    \bottomrule
  \end{tabular}

  \vfill
  \textcolor{rulegray}{\rule{0.75\textwidth}{0.6pt}}\\[0.35cm]
  {\small\textit{Submitted in partial fulfillment of the practical laboratory requirements for}}\\[0.1cm]
  {\small\textbf{Operating Systems Laboratory (25PCCS201)}}\\
  {\small Department of Computer Science \& Engineering, School of Computer Science \& IT}\\[0.2cm]
  {\small\textit{All source listings and execution outputs in this record were genuinely executed and verified on \texttt{joydev@Joydev\_Barua}.}}
  \vspace*{0.4cm}
\end{center}
\clearpage

% ==================== TABLE OF CONTENTS ====================
\pagenumbering{roman}
\pagestyle{labpage}
\tableofcontents
\clearpage

\pagenumbering{arabic}
\pagestyle{labpage}
""")

    fig_counter = 0
    for ch in ALL_CHAPTERS:
        ch_num = ch["num"]
        ch_title = tex_clean(ch["title"])
        ch_syn = tex_clean(ch["synopsis"])

        lines.append(f"\n\\chapter{{{ch_title}}}")
        lines.append(f"\\noindent\\textit{{{ch_syn}}}\\par\\vspace{{6pt}}")
        lines.append(r"\noindent\textcolor{rulegray}{\rule{\textwidth}{0.5pt}}\vspace{6pt}")

        for exp_idx, exp in enumerate(ch["experiments"]):
            sub = exp["sub"]
            title_c = tex_clean(exp["title"])
            aim_c = tex_clean(exp["aim"])
            theory_c = tex_clean(exp["theory"])
            obs_c = tex_clean(exp["observation"])
            fname_lit = tex_literal(exp["filename"])
            code_png, out_png, _ = results[sub]

            if exp_idx > 0:
                lines.append(r"\clearpage")

            lines.append(f"\\labexp{{{sub}}}{{{title_c}}}")

            lines.append(f"\\textbf{{Aim:}} {aim_c}\\par")
            lines.append(f"\\textbf{{Theoretical Principle:}} {theory_c}\\par")

            fig_counter += 1
            lines.append(f"\\labsub{{1. Source Code Implementation (\\texttt{{{fname_lit}}})}}")
            lines.append(r"\noindent\begin{minipage}{\textwidth}\centering")
            lines.append(f"  \\includegraphics[width=0.96\\textwidth,height=0.45\\textheight,keepaspectratio]{{{code_png}}}\\\\[4pt]")
            lines.append(f"  {{\\small\\textit{{Figure {ch_num}.{exp_idx * 2 + 1}: Source Code Listing --- \\texttt{{{fname_lit}}} on \\texttt{{joydev@Joydev\\_Barua}}}}}}")
            lines.append(r"\end{minipage}\par\vspace{6pt}")

            lines.append(r"\labsub{2. Execution Verification Output}")
            lines.append(r"\noindent\begin{minipage}{\textwidth}\centering")
            lines.append(f"  \\includegraphics[width=0.96\\textwidth,height=0.37\\textheight,keepaspectratio]{{{out_png}}}\\\\[4pt]")
            lines.append(f"  {{\\small\\textit{{Figure {ch_num}.{exp_idx * 2 + 2}: Live Terminal Execution Output on \\texttt{{joydev@Joydev\\_Barua}}}}}}")
            lines.append(r"\end{minipage}\par\vspace{6pt}")

            lines.append(f"\\textbf{{Observation \\& Inference:}} {obs_c}\\par")

    # ==================== CHAPTER 22: SYNTHESIS ====================
    syn_title = tex_clean(SYNTHESIS_CHAPTER["title"])
    syn_intro = tex_clean(SYNTHESIS_CHAPTER["intro"])
    lines.append(f"\n\\chapter{{{syn_title}}}")
    lines.append(f"{syn_intro}\\par\\vspace{{8pt}}")

    for heading, body in SYNTHESIS_CHAPTER["invariants"]:
        lines.append(f"\\subsection*{{{tex_clean(heading)}}}")
        lines.append(f"{tex_clean(body)}\\par")

    lines.append(r"\vspace{10pt}\subsection*{Laboratory Verification Summary (Chapters 1--21)}")
    lines.append(r"""\begin{center}
\small
\begin{tabular}{@{}clcc@{}}
\toprule
\textbf{Ch.} & \textbf{Chapter Title} & \textbf{Experiments} & \textbf{Status} \\
\midrule""")
    total_count = 0
    for ch in ALL_CHAPTERS:
        cnt = len(ch["experiments"])
        total_count += cnt
        lines.append(f"{ch['num']} & {tex_clean(ch['title'])} & {cnt} & Verified (Pass) \\\\")
    lines.append(r"\midrule")
    lines.append(f"\\textbf{{Total}} & \\textbf{{Complete Operating Systems Laboratory Curriculum}} & \\textbf{{{total_count}}} & \\textbf{{100\\% Verified}} \\\\")
    lines.append(r"""\bottomrule
\end{tabular}
\end{center}
\vspace{12pt}
\begin{center}
\textcolor{rulegray}{\rule{0.6\textwidth}{0.6pt}}\\[4pt]
{\small\textit{End of Operating Systems Laboratory Record --- Joydev Barua (25BTRCL298)}}
\end{center}
\end{document}
""")

    TEX_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nGenerated LaTeX source: {TEX_PATH}")


def compile_pdf():
    for run_idx in (1, 2):
        print(f"\nRunning pdflatex pass {run_idx}/2 ...")
        proc = subprocess.run(
            [PDFLATEX_EXE, "-interaction=nonstopmode", "-halt-on-error", TEX_PATH.name],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if proc.returncode != 0:
            print(f"[ERROR] pdflatex pass {run_idx} failed (exit {proc.returncode})!")
            tail = "\n".join(proc.stdout.splitlines()[-60:])
            print(tail)
            sys.exit(1)
        # Check for page count in log
        m = re.search(r"Output written on .*?\((\d+) pages", proc.stdout)
        pages = m.group(1) if m else "?"
        print(f"pdflatex pass {run_idx} succeeded! ({pages} pages)")

    if not PDF_PATH.exists() or PDF_PATH.stat().st_size < 50_000:
        print("[ERROR] Compiled PDF is missing or unexpectedly small!")
        sys.exit(1)

    shutil.copy2(PDF_PATH, DESKTOP_PDF)
    print(f"\nCopied final PDF to Desktop: {DESKTOP_PDF}")
    print(f"PDF Size: {PDF_PATH.stat().st_size / (1024 * 1024):.2f} MB")


def verify_no_stale_identity():
    bad_terms = ["vedesh", "25btrcl281", "omen-16", "sid_vedesh"]
    tex_lower = TEX_PATH.read_text(encoding="utf-8").lower()
    for term in bad_terms:
        if term in tex_lower:
            print(f"[ERROR] Found forbidden stale string '{term}' in generated .tex!")
            sys.exit(1)
    for f in OS_LAB_DIR.rglob("*"):
        if f.is_file():
            txt = f.read_text(encoding="utf-8", errors="ignore").lower()
            for term in bad_terms:
                if term in txt:
                    print(f"[ERROR] Found forbidden stale string '{term}' in {f}!")
                    sys.exit(1)
    print("Identity Hygiene Check: PASSED (0 occurrences of stale student identifiers).")


if __name__ == "__main__":
    print("=== Joydev Barua (25BTRCL298) OS Lab Record Builder ===")
    results = execute_all_experiments()
    generate_tex(results)
    verify_no_stale_identity()
    compile_pdf()
    print("\nALL STEPS COMPLETED SUCCESSFULLY!")
