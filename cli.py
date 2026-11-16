import argparse
import asyncio
import os
import sys

from agent import run_job_agent


def read_job_text_from_file(file_path: str) -> str:
    """Reads raw job posting text from an existing local file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: '{file_path}'")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def prompt_multiline_job_text() -> str:
    """Prompts the user to paste multiline job text, ending with 'END' on a new line."""
    print("\nPaste the job posting text below.")
    print("When finished, type 'END' on a new line and press Enter:\n")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def get_job_input(arg_path: str | None = None) -> str:
    """Resolves job posting input either from CLI argument or interactive prompt."""
    if arg_path:
        return read_job_text_from_file(arg_path)

    print("\nSelect input method:")
    print("  [1] Paste job posting text directly into terminal (default)")
    print("  [2] Provide path to a text file")
    choice = input("Enter choice (1/2, default: 1): ").strip()

    if choice == "2":
        path = input("Enter file path: ").strip().strip('"').strip("'")
        return read_job_text_from_file(path)
    else:
        return prompt_multiline_job_text()


async def main():
    parser = argparse.ArgumentParser(description="Job Application Agent Interactive CLI")
    parser.add_argument("--file", "-f", help="Path to job posting text file", default=None)
    parser.add_argument(
        "--resume", "-r", help="Path to resume markdown file (default: resume.md)", default="resume.md"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in automated headless mode without prompting",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("          JOB APPLICATION AGENT — LIVE INTERACTIVE CLI          ")
    print("=" * 70)

    try:
        posting_text = get_job_input(args.file)
        if not posting_text:
            print("\n[ERROR] No job posting text provided. Exiting.")
            return
    except Exception as e:
        print(f"\n[ERROR] Failed to load job posting: {e}")
        return

    interactive = not args.non_interactive
    state = await run_job_agent(
        posting_text=posting_text,
        resume_path=args.resume,
        interactive=interactive,
    )

    print("\n" + "=" * 70)
    print(f"Final Decision: {state.decision}")
    if state.decision == "APPROVED":
        print(f"Application Packet: {state.output_path}")
        if state.cover_letter:
            print("\n" + "-" * 70)
            print("TAILORED COVER LETTER PREVIEW:")
            print("-" * 70)
            print(state.cover_letter)
            print("-" * 70)
    elif state.decision == "ABORTED":
        print("Application was aborted. No files were written.")
    elif state.decision == "FAILED_GENERATION":
        print("Application aborted due to cover letter generation failure.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
