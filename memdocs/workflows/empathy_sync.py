"""
Empathy-DocInt Sync Workflow

Automated workflow to run Empathy Framework analysis and store results in DocInt.
Can be triggered by:
- Git hooks (pre-commit, post-commit)
- GitHub Actions
- Manual CLI invocation
- Scheduled cron jobs
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from memdocs.empathy_adapter import adapt_empathy_to_memdocs


class EmpathySyncWorkflow:
    """
    Workflow to sync Empathy Framework analysis to DocInt storage.

    Supports:
    - File-level analysis (default)
    - Module-level analysis
    - Batch processing
    - Git integration
    """

    def __init__(
        self,
        empathy_service_url: str = "http://localhost:8000",
        memdocs_root: Path = Path(".memdocs"),
        api_key: str | None = None,
    ):
        """
        Initialize workflow.

        Args:
            empathy_service_url: URL of Empathy Framework API
            memdocs_root: Path to .memdocs directory
            api_key: API key for Empathy service (optional for local)
        """
        self.empathy_service_url = empathy_service_url
        self.memdocs_root = Path(memdocs_root)
        self.api_key = api_key or os.getenv("EMPATHY_API_KEY")

    async def analyze_file(
        self,
        file_path: Path,
        language: str = "python",
        wizard: str = "security",
        tier: str = "pro",
    ) -> dict[str, Any]:
        """
        Analyze a single file with Empathy Framework.

        Args:
            file_path: Path to file to analyze
            language: Programming language
            wizard: Wizard to run (security, performance, etc.)
            tier: Tier level (free, pro)

        Returns:
            DocInt DocumentIndex
        """
        # Check if using local Empathy or API
        if self._is_local_empathy():
            return await self._analyze_local(file_path, language, wizard, tier)
        else:
            return await self._analyze_api(file_path, language, wizard, tier)

    async def analyze_changed_files(
        self,
        since_commit: str | None = None,
        language: str = "python",
        wizard: str = "security",
        tier: str = "pro",
    ) -> list[dict[str, Any]]:
        """
        Analyze all files changed since a commit.

        Args:
            since_commit: Git commit hash to compare against (default: HEAD~1)
            language: Programming language
            wizard: Wizard to run
            tier: Tier level

        Returns:
            List of DocInt DocumentIndex objects
        """
        # Get changed files from git
        changed_files = self._get_changed_files(since_commit)

        if not changed_files:
            print("No files changed.")
            return []

        print(f"Analyzing {len(changed_files)} changed files...")

        # Analyze each file
        results = []
        for file_path in changed_files:
            try:
                result = await self.analyze_file(file_path, language, wizard, tier)
                results.append(result)
                print(f"✓ Analyzed: {file_path}")
            except Exception as e:
                print(f"✗ Error analyzing {file_path}: {e}", file=sys.stderr)

        return results

    async def analyze_module(
        self,
        module_path: Path,
        language: str = "python",
        wizard: str = "security",
        tier: str = "pro",
    ) -> list[dict[str, Any]]:
        """
        Analyze all files in a module/directory.

        Args:
            module_path: Path to module directory
            language: Programming language
            wizard: Wizard to run
            tier: Tier level

        Returns:
            List of DocInt DocumentIndex objects
        """
        # Get all source files in module
        files = self._get_module_files(module_path, language)

        if not files:
            print(f"No {language} files found in {module_path}")
            return []

        print(f"Analyzing {len(files)} files in module {module_path}...")

        # Analyze each file
        results = []
        for file_path in files:
            try:
                result = await self.analyze_file(file_path, language, wizard, tier)
                results.append(result)
                print(f"✓ Analyzed: {file_path}")
            except Exception as e:
                print(f"✗ Error analyzing {file_path}: {e}", file=sys.stderr)

        return results

    def _is_local_empathy(self) -> bool:
        """Check if Empathy Framework is available locally."""
        try:
            # Try to import EmpathyService
            from app.backend.services.empathy_service import EmpathyService

            return True
        except ImportError:
            return False

    async def _analyze_local(
        self, file_path: Path, language: str, wizard: str, tier: str
    ) -> dict[str, Any]:
        """Run Empathy analysis using local EmpathyService."""
        from app.backend.services.empathy_service import EmpathyService

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Run Empathy analysis
        service = EmpathyService()
        analysis_results = await service.run_wizard(wizard, language, code, tier)

        # Get git commit (if available)
        commit = self._get_current_commit()

        # Store in DocInt
        doc_index = adapt_empathy_to_memdocs(
            analysis_results,
            file_path,
            memdocs_root=self.memdocs_root,
            commit=commit,
        )

        return doc_index.model_dump(mode="json")

    async def _analyze_api(
        self, file_path: Path, language: str, wizard: str, tier: str
    ) -> dict[str, Any]:
        """Run Empathy analysis using remote API."""
        import aiohttp

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Call Empathy API
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.empathy_service_url}/api/wizards/{wizard}/analyze",
                json={"code": code, "language": language, "tier": tier},
                headers=headers,
            ) as response:
                if response.status != 200:
                    raise Exception(f"API error: {response.status} - {await response.text()}")

                analysis_results = await response.json()

        # Get git commit
        commit = self._get_current_commit()

        # Store in DocInt
        doc_index = adapt_empathy_to_memdocs(
            analysis_results,
            file_path,
            memdocs_root=self.memdocs_root,
            commit=commit,
        )

        return doc_index.model_dump(mode="json")

    def _get_changed_files(self, since_commit: str | None = None) -> list[Path]:
        """Get list of changed files from git."""
        try:
            # Default to comparing against previous commit
            if not since_commit:
                since_commit = "HEAD~1"

            # Get changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", since_commit, "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Filter to existing files
            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    path = Path(line)
                    if path.exists() and path.is_file():
                        files.append(path)

            return files

        except subprocess.CalledProcessError:
            # Not a git repo or no commits yet
            return []

    def _get_module_files(self, module_path: Path, language: str) -> list[Path]:
        """Get all source files in a module."""
        # Map language to file extensions
        extensions = {
            "python": [".py"],
            "typescript": [".ts", ".tsx"],
            "javascript": [".js", ".jsx"],
            "go": [".go"],
            "rust": [".rs"],
            "java": [".java"],
            "csharp": [".cs"],
            "php": [".php"],
        }

        exts = extensions.get(language, [".py"])

        files = []
        for ext in exts:
            files.extend(module_path.rglob(f"*{ext}"))

        return files

    def _get_current_commit(self) -> str | None:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None


# CLI Interface
async def main():
    """CLI entry point for empathy-sync workflow."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync Empathy Framework analysis to DocInt storage"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Analyze a specific file",
    )
    parser.add_argument(
        "--module",
        type=Path,
        help="Analyze all files in a module/directory",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Analyze files changed since last commit",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Git commit to compare against (for --changed)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="python",
        help="Programming language (default: python)",
    )
    parser.add_argument(
        "--wizard",
        type=str,
        default="security",
        help="Wizard to run (default: security)",
    )
    parser.add_argument(
        "--tier",
        type=str,
        default="pro",
        choices=["free", "pro"],
        help="Tier level (default: pro)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="Empathy service URL",
    )

    args = parser.parse_args()

    # Create workflow
    workflow = EmpathySyncWorkflow(
        empathy_service_url=args.api_url,
        memdocs_root=Path(".memdocs"),
    )

    # Execute based on mode
    if args.file:
        print(f"Analyzing file: {args.file}")
        result = await workflow.analyze_file(args.file, args.language, args.wizard, args.tier)
        print(f"✓ Analysis complete. Stored in .memdocs/")

    elif args.module:
        print(f"Analyzing module: {args.module}")
        results = await workflow.analyze_module(args.module, args.language, args.wizard, args.tier)
        print(f"✓ Analyzed {len(results)} files. Stored in .memdocs/")

    elif args.changed:
        print("Analyzing changed files...")
        results = await workflow.analyze_changed_files(
            args.since, args.language, args.wizard, args.tier
        )
        print(f"✓ Analyzed {len(results)} changed files. Stored in .memdocs/")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
