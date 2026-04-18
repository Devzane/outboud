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
        "Long time no see",
        (
            "Hey,\n\n"
            "It's been a minute since we last caught up. Hope everything "
            "is going well on your end. Let's reconnect soon!\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Checking in on your end",
        (
            "Hi there,\n\n"
            "Just wanted to drop a quick note to see how the week is treating you. "
            "Hope the new projects are off to a good start.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Hope you're having a good week",
        (
            "Hey,\n\n"
            "Just a quick hello! No need to reply to this, just wanted to "
            "wish you a productive rest of the week.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Touching base",
        (
            "Hi,\n\n"
            "Wanted to quickly touch base and make sure we're still aligned "
            "for the upcoming quarter. Let me know your thoughts.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Reconnecting",
        (
            "Hey there,\n\n"
            "I saw your recent update and it reminded me that we need to catch up. "
            "Let's grab some time next week if you're free.\n\n"
            "Warmly,\nAlex"
        ),
    ),
    (
        "Thinking of the team",
        (
            "Hi,\n\n"
            "Just wanted to send a quick shoutout to you and the team. "
            "Hope you're all crushing it this month.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Almost Friday",
        (
            "Hey,\n\n"
            "Hope you're surviving the week! Just crossing a few things off "
            "my list and wanted to say hi.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Quick hello",
        (
            "Hi there,\n\n"
            "Wanted to drop a quick line. It's been pretty busy over here, "
            "but I wanted to make sure we stayed in touch.\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "Catch up soon?",
        (
            "Hey,\n\n"
            "Let me know when things slow down a bit for you. "
            "I'd love to hear how the new initiatives are panning out.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Any updates?",
        (
            "Hi,\n\n"
            "Curious to hear how the team is doing with the recent changes. "
            "Drop me a line whenever you have a spare moment.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Draft review",
        (
            "Hey,\n\n"
            "I'm looking over the latest draft now. It looks solid, but I'll "
            "send over a few minor tweaks by tomorrow morning.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Quick update on my end",
        (
            "Hi there,\n\n"
            "Just a quick heads-up: things are moving smoothly on our side. "
            "We should be ready to launch right on schedule.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Status report",
        (
            "Hey,\n\n"
            "Quick update on the timeline. We're slightly ahead of schedule, "
            "so I'll have the deliverables to you early next week.\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "Pending items",
        (
            "Hi,\n\n"
            "I still have a few pending items on my plate from our last chat. "
            "I'll have them wrapped up by EOD Friday.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Feedback on the document",
        (
            "Hey,\n\n"
            "I left a few comments in the shared doc. Nothing major, just "
            "some formatting suggestions. Let me know what you think.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Almost done",
        (
            "Hi there,\n\n"
            "Just wrapping up the final touches on this end. I'll shoot "
            "everything over to you once it's completely polished.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Moving the deadline",
        (
            "Hey,\n\n"
            "Do you mind if we push this back a day? I want to make sure "
            "we get it exactly right before sending it off.\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "Quick pivot",
        (
            "Hi,\n\n"
            "We decided to go in a slightly different direction based on the "
            "latest data. I'll send over the updated brief shortly.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "New requirements",
        (
            "Hey,\n\n"
            "Got some new info from the client today. I don't think it changes "
            "much, but I wanted to keep you in the loop.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Checking the specs",
        (
            "Hi there,\n\n"
            "Can you verify the numbers on page 3 when you get a chance? "
            "Just want to make sure my math is checking out.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Interesting read",
        (
            "Hey,\n\n"
            "Saw this article today and immediately thought of our conversation "
            "last week. Definitely worth a quick read.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Podcast recommendation",
        (
            "Hi,\n\n"
            "I listened to a great podcast episode on my commute today. "
            "I think it's right up your alley. I'll send you the link!\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Helpful tool",
        (
            "Hey,\n\n"
            "I started using this new software for project management and "
            "it's been a game changer. We should look into it for the team.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Industry news",
        (
            "Hi there,\n\n"
            "Did you see the big announcement this morning? Crazy stuff. "
            "Would love to hear your take on it when you have a minute.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Book suggestion",
        (
            "Hey,\n\n"
            "I just finished a fantastic book over the weekend. "
            "Reminded me of your current project. Highly recommend it!\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Useful link",
        (
            "Hi,\n\n"
            "Found this forum thread super helpful while troubleshooting earlier. "
            "Bookmarking it for later, thought you might want it too.\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "That article we talked about",
        (
            "Hey,\n\n"
            "Finally found the link to that case study I mentioned. "
            "Take a look when you have some downtime.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Weekend reading",
        (
            "Hi there,\n\n"
            "Sending over some light reading for your weekend! "
            "No need to look at this until Monday, though.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "New feature drop",
        (
            "Hey,\n\n"
            "Looks like they finally updated the app with the features we "
            "were asking for. Might be worth taking it for a spin again.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Something to look into",
        (
            "Hi,\n\n"
            "I stumbled across a framework that might be useful for our "
            "next big push. Let's discuss it at our next sync.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Rescheduling our sync",
        (
            "Hey,\n\n"
            "Something urgent just came up. Can we move our sync to Thursday "
            "afternoon instead? Let me know if that works.\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "Agenda for tomorrow",
        (
            "Hi,\n\n"
            "Here's a quick outline of what I want to cover tomorrow. "
            "Feel free to add anything else you'd like to discuss.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Are we still on?",
        (
            "Hey,\n\n"
            "Just confirming our meeting for later today. "
            "I'm looking forward to catching up!\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Can't make it today",
        (
            "Hi there,\n\n"
            "I'm running incredibly behind schedule today and won't be able "
            "to make our call. Can we reschedule for early next week?\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Availability next week",
        (
            "Hey,\n\n"
            "Let me know what days work best for you next week. "
            "My Tuesday and Wednesday afternoons are pretty wide open.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Quick huddle?",
        (
            "Hi,\n\n"
            "Do you have 5 minutes to chat this afternoon? "
            "Just want to bounce a quick idea off you.\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "Calendar invite sent",
        (
            "Hey,\n\n"
            "Just sent over the calendar invite. Let me know if you didn't "
            "receive it or if the time doesn't work for you.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Postponing the call",
        (
            "Hi,\n\n"
            "Let's push this discussion to next month when we have more data. "
            "No sense in rushing it right now.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Follow up from Tuesday",
        (
            "Hey,\n\n"
            "Great chatting with you on Tuesday. I'm working on the action "
            "items now and will keep you posted on my progress.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Notes from our chat",
        (
            "Hi there,\n\n"
            "Summarizing what we discussed earlier. I think we're on a great "
            "track. Let me know if I missed any key points.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
    (
        "Quick favor",
        (
            "Hey,\n\n"
            "Could you do me a quick favor and look over the attached sheet? "
            "Just want a second pair of eyes on it.\n\n"
            "Thanks a million,\nAlex"
        ),
    ),
    (
        "Opinion needed",
        (
            "Hi,\n\n"
            "What do you think about the new UI mockups? "
            "I'm torn between the two options and value your input.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Intro request",
        (
            "Hey,\n\n"
            "Could you possibly introduce me to the new vendor? "
            "I'd love to ask them a few questions about their onboarding process.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Out of office next week",
        (
            "Hi there,\n\n"
            "Giving you a quick heads up that I'll be OOO next week. "
            "If anything urgent pops up, please reach out to the wider team.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Holiday plans",
        (
            "Hey,\n\n"
            "Hope you have a fantastic holiday break planned! "
            "Unplug, relax, and we'll catch up when you're back.\n\n"
            "Warmly,\nAlex"
        ),
    ),
    (
        "Question about the process",
        (
            "Hi,\n\n"
            "I'm not entirely sure how the new approval process works. "
            "Do you mind walking me through it when you have a second?\n\n"
            "Thanks,\nAlex"
        ),
    ),
    (
        "Can you clarify?",
        (
            "Hey,\n\n"
            "I didn't quite understand the last point in your email. "
            "Could you clarify what you meant by the bandwidth limitations?\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Thanks again",
        (
            "Hi,\n\n"
            "Just wanted to say thanks again for your help yesterday. "
            "Really appreciate you taking the time to explain things.\n\n"
            "Cheers,\nAlex"
        ),
    ),
    (
        "Congratulations!",
        (
            "Hey,\n\n"
            "Saw the good news on LinkedIn today! Huge congratulations. "
            "Very well deserved.\n\n"
            "Best,\nAlex"
        ),
    ),
    (
        "Happy Friday",
        (
            "Hi there,\n\n"
            "We made it to Friday! Have a great weekend and take some time "
            "to recharge. Catch you next week.\n\n"
            "Talk soon,\nAlex"
        ),
    ),
]