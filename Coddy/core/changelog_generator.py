import asyncio
import os
from typing import Optional, List, Dict
import re

from utility_functions import execute_command, write_file
from logging_utility import log_info, log_warning, log_error, log_debug

class ChangelogGenerator:
    """
    Generates a Markdown changelog from Git commit history.
    Supports commit categorization, tag ranges, and GitHub linking.
    """

    def __init__(self):
        pass

    async def _get_git_tags(self) -> List[str]:
        """
        Returns a list of Git tags sorted by creation order.
        """
        try:
            retcode, stdout, stderr = await execute_command("git tag --sort=creatordate")
            if retcode != 0:
                await log_warning(f"Failed to retrieve tags: {stderr}")
                return []
            return stdout.strip().splitlines()
        except Exception as e:
            await log_error(f"Error fetching git tags: {e}", exc_info=True)
            return []

    async def _get_git_log(self, since_tag: Optional[str] = None, until_tag: Optional[str] = None, num_commits: Optional[int] = None) -> List[Dict[str, str]]:
        log_format = "%H%n%an%n%ad%n%s%n%b%x00"
        command = ["git", "log", "--no-merges", f"--pretty=format:{log_format}"]

        if since_tag and until_tag:
            command.append(f"{since_tag}..{until_tag}")
        elif since_tag:
            command.append(since_tag)

        if num_commits:
            command.append(f"-n {num_commits}")

        try:
            return_code, stdout, stderr = await execute_command(" ".join(command))

            if return_code != 0:
                await log_error(f"Git log command failed with exit code {return_code}: {stderr}")
                return []

            commits_raw = stdout.strip().split('\x00')
            commits_data = []

            for commit_raw in commits_raw:
                if not commit_raw.strip():
                    continue

                parts = commit_raw.split('\n', 4)
                if len(parts) >= 4:
                    commit_hash = parts[0].strip()
                    if not commit_hash:
                        # Skip commits with missing hash
                        continue
                    author = parts[1].strip()
                    date = parts[2].strip()
                    subject = parts[3].strip()
                    body = parts[4].strip() if len(parts) > 4 else ""

                    commits_data.append({
                        "hash": commit_hash,
                        "author": author,
                        "date": date,
                        "subject": subject,
                        "body": body
                    })
            return commits_data
        except Exception as e:
            await log_error(f"Error fetching Git log: {e}", exc_info=True)
            return []

    async def generate_changelog(self, *, since_tag: Optional[str] = None, until_tag: Optional[str] = None, num_commits: Optional[int] = None, repo_url: Optional[str] = None) -> str:
        await log_info("Generating changelog...")
        commits = await self._get_git_log(since_tag=since_tag, until_tag=until_tag, num_commits=num_commits)

        if not commits:
            await log_warning("No commits found to generate changelog.")
            return "# Changelog\n\n_No changes found._"

        categories = {
            "feat": ("✨ Features", []),
            "fix": ("🐛 Bug Fixes", []),
            "docs": ("📝 Documentation", []),
            "refactor": ("♻️ Refactoring", []),
            "test": ("✅ Tests", []),
            "chore": ("🧹 Chores", []),
            "other": ("🔄 Other", [])
        }

        for commit in commits:
            subject = commit['subject'].strip()
            if not subject:
                subject = commit['hash']  # fallback if subject empty

            # Remove all leading/trailing asterisks, including multiple '**'
            subject = re.sub(r'^\*+|\*+$', '', subject).strip()
            # Collapse multiple spaces
            subject = re.sub(r'\s+', ' ', subject)

            body = commit['body']
            match = re.match(r"^(feat|fix|docs|refactor|test|chore)(\(.+?\))?:\s+(.*)", subject, re.IGNORECASE)

            key = "other"
            message = subject

            if match:
                key = match.group(1).lower()
                message = match.group(3)

            full_hash = commit['hash']
            short_hash = full_hash[:7]
            commit_link = f"[`{short_hash}`]({repo_url}/commit/{full_hash})" if repo_url else f"`{short_hash}`"
            author = commit['author']
            date = commit['date'].split(' ')[0]  # ISO date or first token

            linked_body = re.sub(r"#(\d+)", rf"[#\1]({repo_url}/issues/\1)" if repo_url else r"#\1", body)

            entry = f"- **{message}:** ([`{short_hash}`]({repo_url}/commit/{full_hash}) by {author} on {date})"
            if linked_body:
                indented_body = "\n".join([f"  {line}" for line in linked_body.splitlines()])
                entry += f"\n{indented_body}\n"

            categories.setdefault(key, ("🔄 Other", []))[1].append(entry)

        changelog_lines = ["# Changelog\n"]

        for key, (title, items) in categories.items():
            if items:
                changelog_lines.append(f"## {title}\n")
                changelog_lines.extend(items)
                changelog_lines.append("")

        await log_info(f"Changelog generated with {len(commits)} commits.")
        return "\n".join(changelog_lines)

    async def save_changelog_to_file(self, *, changelog_content: str, file_path: str = "CHANGELOG.md"):
        try:
            await write_file(file_path, changelog_content)
            await log_info(f"Changelog saved to {file_path}")
        except Exception as e:
            await log_error(f"Error saving changelog to file {file_path}: {e}", exc_info=True)

async def main_changelog_test():
    generator = ChangelogGenerator()

    tags = await generator._get_git_tags()
    if len(tags) >= 2:
        since_tag = tags[-2]
        until_tag = tags[-1]
    else:
        since_tag = until_tag = None

    changelog_recent = await generator.generate_changelog(num_commits=5, repo_url="https://github.com/youruser/yourrepo")
    print("\n--- Recent Changelog (Last 5 Commits) ---\n")
    print(changelog_recent)
    await generator.save_changelog_to_file(changelog_content=changelog_recent, file_path="RECENT_CHANGELOG.md")

    changelog_full = await generator.generate_changelog(since_tag=since_tag, until_tag=until_tag, repo_url="https://github.com/youruser/yourrepo")
    print("\n--- Full Changelog ---\n")
    print(changelog_full)
    await generator.save_changelog_to_file(changelog_content=changelog_full, file_path="CHANGELOG.md")

    await log_info("Ensure you have Git installed and some commits in your repository to see output.")

if __name__ == "__main__":
    asyncio.run(main_changelog_test())
