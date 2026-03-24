"""
content_templates.py
────────────────────
Pools of realistic, casual subject lines and body texts used by the
Email Warmup Engine to simulate natural human-to-human email traffic.

Each template is a (subject, body) tuple. The engine picks one at random
for every outbound send.
"""

TEMPLATES: list[tuple[str, str]] = [
    (
        "Checking in",
        (
            "Hey there,\n\n"
            "Just wanted to check in and see how things are going on your end. "
            "Let me know if there's anything I can help with.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Meeting notes from yesterday",
        (
            "Hi,\n\n"
            "Here are the quick takeaways from yesterday's call. I'll send "
            "the full deck by end of week. Let me know if I missed anything.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Quick question",
        (
            "Hey,\n\n"
            "I had a quick question about the timeline we discussed. "
            "Do you have a few minutes to hop on a call this week?\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "Following up",
        (
            "Hi there,\n\n"
            "Just circling back on our last conversation. Wanted to see "
            "if you had a chance to review the proposal.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Thought you'd find this interesting",
        (
            "Hey,\n\n"
            "I came across an article that reminded me of our chat. "
            "I'll forward it separately — think you'll enjoy it.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Happy Monday!",
        (
            "Hi,\n\n"
            "Hope you had a great weekend! Just touching base to see "
            "how the project is coming along. No rush on a reply.\n\n"
            "Warm regards,\nAlex"
        ),
    ),
    (
        "A small update",
        (
            "Hey,\n\n"
            "Quick heads-up — we made a few tweaks on our end that "
            "should streamline things. Happy to walk you through them "
            "whenever you're free.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Coffee sometime?",
        (
            "Hi,\n\n"
            "It's been a while since we caught up. Would love to grab "
            "a virtual coffee if your schedule allows.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Re: Next steps",
        (
            "Hey,\n\n"
            "Following up on next steps from our last sync. I've outlined "
            "a rough plan and would appreciate your thoughts before we "
            "move forward.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Resource I mentioned",
        (
            "Hi,\n\n"
            "Here's the resource I mentioned during our call. Let me know "
            "if you have any questions or need more context.\n\n"
            "Thanks,\nAlex"
        ),
    ),
]
