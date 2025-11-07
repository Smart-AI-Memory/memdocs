"""
Basic MemDocs Usage Example

This example shows how to use MemDocs to:
1. Initialize memory for a project
2. Review files and generate documentation
3. Search project memory
4. Get context for AI assistants
"""

from memdocs import MemDocs


def example_initialize():
    """Initialize MemDocs in a project"""
    print("=" * 80)
    print("Example 1: Initialize MemDocs")
    print("=" * 80)

    # Initialize MemDocs for current directory
    mem = MemDocs(repo_path=".")

    # Or specify a different project
    mem = MemDocs(repo_path="/path/to/your/project")

    print(f"✓ MemDocs initialized for: {mem.repo_path}")
    print(f"✓ Memory directory: {mem.memory_dir}")
    print()


def example_review_file():
    """Review a single file and generate memory"""
    print("=" * 80)
    print("Example 2: Review a File")
    print("=" * 80)

    mem = MemDocs(".")

    # Review a Python file
    result = mem.review_file("src/payments/charge.py")

    print(f"✓ File reviewed: {result['file']}")
    print(f"✓ Summary: {result['summary'][:100]}...")
    print(f"✓ Symbols extracted: {len(result['symbols'])}")
    print(f"✓ Confidence: {result['confidence']:.0%}")
    print()


def example_review_module():
    """Review an entire module"""
    print("=" * 80)
    print("Example 3: Review a Module")
    print("=" * 80)

    mem = MemDocs(".")

    # Review entire payments module
    result = mem.review_module("src/payments/")

    print(f"✓ Module reviewed: {result['module']}")
    print(f"✓ Files processed: {len(result['files'])}")
    print(f"✓ Total symbols: {result['total_symbols']}")
    print(f"✓ Public APIs: {len(result['public_apis'])}")
    print()


def example_search():
    """Search project memory"""
    print("=" * 80)
    print("Example 4: Search Memory")
    print("=" * 80)

    mem = MemDocs(".")

    # Search for authentication-related code
    results = mem.search("authentication")

    print(f"✓ Found {len(results)} results for 'authentication':")
    for i, result in enumerate(results[:3], 1):
        print(f"  {i}. {result['file']}")
        print(f"     {result['snippet'][:80]}...")
    print()


def example_get_context():
    """Get context for AI assistant"""
    print("=" * 80)
    print("Example 5: Get Context for AI")
    print("=" * 80)

    mem = MemDocs(".")

    # Get context for a specific file
    context = mem.get_context_for_file("src/auth/login.py")

    print("✓ Context generated for AI:")
    print(f"  - File: {context['file']}")
    print(f"  - Summary: {context['summary'][:100]}...")
    print(f"  - Dependencies: {', '.join(context['dependencies'][:3])}")
    print(f"  - Related files: {len(context['related_files'])}")
    print()

    # Use with Claude
    print("✓ Example: Pass context to Claude")
    print("""
    from anthropic import Anthropic

    client = Anthropic(api_key="your-api-key")

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        system=f"Project context:\\n{context['full_context']}",
        messages=[
            {"role": "user", "content": "Explain the login flow"}
        ]
    )
    """)
    print()


def example_stats():
    """Get memory statistics"""
    print("=" * 80)
    print("Example 6: Memory Statistics")
    print("=" * 80)

    mem = MemDocs(".")

    stats = mem.get_stats()

    print("✓ Project Memory Stats:")
    print(f"  - Total files documented: {stats['total_files']}")
    print(f"  - Total symbols: {stats['total_symbols']}")
    print(f"  - Memory size: {stats['memory_size_mb']:.2f} MB")
    print(f"  - Last updated: {stats['last_updated']}")
    print(f"  - Coverage: {stats['coverage_percentage']:.1f}%")
    print()


def example_empathy_integration():
    """Integrate with Empathy Framework"""
    print("=" * 80)
    print("Example 7: Empathy Framework Integration")
    print("=" * 80)

    mem = MemDocs(".")

    # Sync with Empathy
    mem.sync_to_empathy()

    print("✓ Synced with Empathy Framework")
    print("✓ Empathy agents can now use project memory for:")
    print("  - Level 4 Anticipatory predictions")
    print("  - Trust-building behaviors")
    print("  - Proactive assistance")
    print()

    # Example: Use with Empathy agent
    print("✓ Example: Create Empathy agent with memory")
    print("""
    from empathy import EmpathyAgent

    agent = EmpathyAgent(
        memory=mem,
        level=4,
        anticipation_window_days=90
    )

    # Agent can anticipate issues based on project history
    predictions = await agent.predict_issues()
    """)
    print()


def main():
    """Run all examples"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "MemDocs Usage Examples" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        example_initialize()
        example_review_file()
        example_review_module()
        example_search()
        example_get_context()
        example_stats()
        example_empathy_integration()

        print("=" * 80)
        print("✓ All examples completed successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Install MemDocs: pip install memdocs")
        print("  2. Initialize in your project: memdocs init")
        print("  3. Start reviewing files: memdocs review --path src/")
        print("  4. Read the docs: https://docs.deepstudyai.com/memdocs")
        print()

    except Exception as e:
        print(f"✗ Error: {e}")
        print("Note: These examples require MemDocs to be installed and configured.")
        print("Install with: pip install memdocs")


if __name__ == "__main__":
    main()
