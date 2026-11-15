# Idea ticket: member characters that explain each track's findings

Idea in Mahmoud's own words (Arabic, summarised): each team member gets a character made from his own
photo; the character moves its mouth and talks about the findings that member produced, and a visitor
can chat with it ("explain this part to me"). Later, the same characters can appear in a short
presentation video with an old-video-game look instead of plain slides.

Title: Member characters (retro pixel style) that answer questions about each track's findings
What it adds, and for whom (one sentence): judges and visitors can ask a friendly character about one
track and get a short answer that always cites the finding ID, file and row it comes from.
Which judging criterion it improves: Presentation and Creativity (also Validity if every answer cites a finding).
Evidence from the data that it is possible (file and row): T3 already has 12 findings with exact sources
(analysis/T3/*/findings.md, e.g. F-T3-1, workbook 'Reduced Data with ISS Det' rows 35 -> 36); the other
tracks produce the same format.
Files or shared structure it would touch: the dashboard (one new page or panel), each track's findings.md
(read only), a small question set per track (extra-work item 3: 5 answerable + 2 not answerable questions).
Effort in hours, and the risk if it fails:
- Characters: 1 h. Pixelate each member's photo with a fixed filter (no AI image generator, so no
  watermark rule is triggered; if an AI image tool is used instead, the image needs a visible watermark).
  Two frames per character (mouth closed / open) switched while the answer text types out.
- Dialogue box and typing effect with a short blip sound: 1-2 h.
- Answers: 2-3 h. Safe version: answers come from the findings and the per-track question set, with
  "not in our data" for anything else (works offline, no API key). Optional version: an LLM that may only
  quote findings, behind a small server that holds the key; if the key or server fails, fall back to the
  safe version.
- Risk: a wrong or made-up answer in front of judges hurts Validity; mitigated by answering only from
  findings with their IDs. Realistic talking-head video (lip-sync models) is out of scope for the time left.
Consent and rules: every member agrees to the use of his photo; all members are over 18; no NASA logos;
AI use (code, any generated audio or images) listed in the submission.
Latest time it must be decided to fit before the Sunday 14:00 freeze: Sunday 09:00.
