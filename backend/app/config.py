CALL_STAGES = [
    {
        "id": 1,
        "name": "Opening",
        "purpose": "Introduce yourself and establish who you are speaking with.",
        "prompt": "Hi, this is [Your Name] from [Company]. Am I speaking with [Prospect Name]?",
        "guidance": "Keep the introduction brief and professional."
    },
    {
        "id": 2,
        "name": "Purpose",
        "purpose": "Explain why you are calling.",
        "prompt": "I'm calling because we help businesses with [specific outcome].",
        "guidance": "State a relevant business outcome without giving a long pitch."
    },
    {
        "id": 3,
        "name": "Permission",
        "purpose": "Ask whether the prospect can spare a moment.",
        "prompt": "Is now a bad time for a quick question?",
        "guidance": "Respect their time and accept their response."
    },
    {
        "id": 4,
        "name": "Their business",
        "purpose": "Understand the prospect's business and responsibilities.",
        "prompt": "Could you tell me a little about how your team currently handles this?",
        "guidance": "Ask an open question and listen before offering solutions."
    },
    {
        "id": 5,
        "name": "Their need",
        "purpose": "Identify the prospect's problem in their own words.",
        "prompt": "What is the biggest challenge you face with your current process?",
        "guidance": "Capture the prospect's exact words. Do not replace them with your interpretation."
    },
    {
        "id": 6,
        "name": "Objection",
        "purpose": "Understand and respond to concerns.",
        "prompt": "I understand. Could you tell me a little more about that concern?",
        "guidance": "Acknowledge the concern and clarify before responding. Do not pressure the prospect."
    },
    {
        "id": 7,
        "name": "Next step",
        "purpose": "Agree on a clear and appropriate follow-up.",
        "prompt": "Would a short follow-up conversation or a relevant resource be useful?",
        "guidance": "Record the agreed action, owner, and timing when provided."
    },
    {
        "id": 8,
        "name": "Close",
        "purpose": "End professionally and record the outcome.",
        "prompt": "Thank you for your time. I appreciate the conversation.",
        "guidance": "Confirm the outcome and next step, if any, before ending the call."
    }
]

CALL_OUTCOMES = [
    "Interested",
    "Agreed to receive report",
    "Follow-up required",
    "Next step agreed",
    "Not interested",
    "Do not call",
    "Wrong person",
    "Call again",
    "Moved company",
    "No outcome logged"
]
