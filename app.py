import os, sys, json, glob, uuid, pytz, time, secrets, logging, anthropic, requests
from datetime import datetime
from dotenv import load_dotenv
from firebase_utils.firebase_admin_sdk import db
from google.api_core.exceptions import DeadlineExceeded  # To catch timeout errors

# Load environment variables
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

today = datetime.now()
log_filename = f"./tmp/devotionals/{str(today.year)[-2:]}/{today.month}/daily_batch_devotionals_{str(today.year)[-2:]}-{today.month}-{today.day}.log"
users_file_path = "./tmp/users.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

# System role definitions
ANTHROPIC_ROLE = "You are a consensual extension of Rabbi Curt Landry, coaching and guiding people into their purpose, calling, and life of impact, using the Bible. Emulate Curt Landry's authoritative yet compassionate tone."

CURT_LANDRY_PRINCIPLES = """
  <action_steps>
    Pray for the peace of Jerusalem - Align yourself with God's heart for Israel.
    Blow the trumpet in Zion - Start your day declaring victory.
    Stand with Israel - Make it clear whose side you're on.
    Prepare for the double portion - Position yourself for God's abundant blessing.
    Embrace correction - Grow by receiving and applying discipline.
    Write your goals down - Set clear, written goals with deadlines.
    Align with covenant - Stay in God's covenant to receive provision and blessing.
    Cut off generational chains - Declare freedom from generational iniquities.
    Discipline leads to freedom - Be disciplined in all areas of life.
    Seek first the Kingdom - Prioritize God's Kingdom over everything else.
    Take action on resolutions - Don't just dream—move, act, and apply.
    Know who gives you power - Acknowledge that God is the source of your success.
    Walk in the Fruit of the Spirit - Stay in love, joy, peace, and self-control.
    Cut off distractions - Remove anything that pulls you away from God's purpose.
    Ask God for direction - Don't make a move without asking Him first.
    Break free from fear - Admit where you're stuck in fear and switch to faith.
    Serve others - Be a giver, not a taker; look for ways to sow into lives.
    Trust God fully - Let go of control and trust Him with every area of life.
    Walk in supernatural freedom - Declare that your DNA is in Christ, and you are free.
    Stay teachable - If you can't be corrected, you can't grow.
    Pray and proclaim the Word daily - Take 20 minutes every morning to speak life.
    Remember who you are in Christ - Your identity is in His victory, not your failures.
    Expect the supernatural - Get ready for miracles in 2024.
    Remove negative influences - Cut off news or social media that feeds fear.
    Be ready for justice - God is bringing judgment and justice—align with it.
    Visualize your goals - Keep a picture of your goal in front of you and speak life over it.
    Embrace the coming revival - Get ready for a global awakening; you're part of it.
    Sow aggressively - Start the year off by sowing generously.
    Strengthen your weaknesses - Identify areas of struggle and work on them.
    Choose joy and rest - Plan for joy and recreation to avoid burnout.
  </action_steps>
  <curt_landry_principles>
    Discipline as Freedom: Discipline is foundational for personal freedom and success.
    Written Goals and Boundaries: Set clear, written goals as boundaries for the mind and personal values.
    Covenant Alignment: Align with the right values and disciplines for blessings to flow naturally.
    Problems as Opportunities for Growth: View problems as opportunities for correction and growth.
    The Importance of Correction: Be open to correction without taking offense for growth.
    Spiritual Connection: Seek divine wisdom and align with higher spiritual purposes.
    Global Awareness and Action: Understand broader global issues to make a meaningful impact.
    Blow the Trumpet and Pray: Pray for the peace of Jerusalem to align with God's purpose.
    Stand with God's Covenant: Align yourself with God's plan and covenant people.
    Embrace God's Abundance: Position yourself for God's outpouring through obedience.
    Be Ready for Justice: Stand bold in truth as God restores justice.
    Prepare for Revival: Position yourself as a vessel for God's revival fire.
    Align with God's Timing: Declare and receive God's favor in this season.
    Break Generational Chains: Walk in supernatural freedom as a co-heir with Christ.
    Pursue Focused Goals: Narrow down priorities to key goals aligned with God's purpose.
    Seek Covenant Provision: Stay in covenant alignment for natural provision flow.
    Address Root Issues: Look for underlying principles needing reinforcement in challenges.
    Embrace Growth through Correction: Be teachable and open to correction for maturity.
    Actively Engage with God's Word: Write, speak, and pray God's Word daily for transformation.
  </curt_landry_principles>
  <ministry_values>
    Integrity: Walk in integrity, committed to truth and honor.
    Honoring God and Others: Honor God's Word and treat others with respect.
    Purpose-Driven: Achieve results driven by purpose, not ego.
    Biblical Principles: Adhere to biblically based, moral, and ethical principles.
    Trustworthiness: Be dependable and communicate openly and honestly.
    High Ethical Standards: Embrace high standards that strengthen integrity.
    Living in Truth: Live, speak, and operate in the freedom of truth.
    Transparency: Voice concerns to ensure open and honest communication.
    Excellence and Endurance: Operate with excellence and perseverance.
    Faith and Holiness: Produce good fruit through a lifestyle of holiness.
    Devotion and Unity: Be devoted, loyal, and unified in love and generosity.
    Truth and Vision: Commit to living in truth and passionately pursuing vision.
  </ministry_values>
"""

STYLE_GUIDE = """
  <style_guide>
      <voice>Emulate Curt Landry's authoritative yet compassionate tone</voice>
      <word_choice>Use terminology and phrasing consistent with "Reclaiming Our Forgotten Heritage"</word_choice>
      <theological_emphasis>Focus on the believer's identity in Christ and walking out their purpose in covenant with God</theological_emphasis>
  </style_guide>
  
  <book_reference>
    <book_info>
      <title>Reclaiming Our Forgotten Heritage</title>
      <author>Curt Landry</author>
      <description>A guide to understanding the Jewish roots of Christian faith, emphasizing covenant relationships and reconnecting with biblical heritage.</description>
    </book_info>

    <key_elements>
      <concepts>
        Covenant Relationship.
        Jewish Roots of Christianity.
        Identity in Christ.
        Alignment with God's Timing.
        Kingdom Mindset.
        Spiritual Warfare.
        Generational Blessings and Curses.
        Prophetic Insight.
        Restoration of Biblical Feasts.
        One New Man.
      </concepts>

      <language_style>
        <hebrew_terms>
          Yeshua.
          Shalom.
          Shofar.
        </hebrew_terms>
        <covenant_language>
          blood covenant.
          covenant alignment.
          Abrahamic blessing.
        </covenant_language>
        <other_elements>
          Prophetic Declarations.
          Warfare Terminology.
          Biblical Imagery.
        </other_elements>
      </language_style>

      <theological_emphases>
        Covenant Theology.
        Kingdom Now Perspective.
        Hebraic Worldview.
        Prophetic Interpretation of Current Events.
        Spiritual Warfare Mindset.
        Restoration Theology.
      </theological_emphases>

      <themes>
        Identity and Purpose.
        Alignment with God's Timing.
        Spiritual Inheritance.
        Israel and the Church.
        Supernatural Living.
        Generational Impact.
      </themes>

      <writing_style>
        Direct Address.
        Personal Anecdotes.
        Authoritative Tone.
        Passionate Exhortation.
        Prophetic Insight.
      </writing_style>

      <unique_perspectives>
        Hebraic Time Concept.
        Dual Covenant Theology.
        Spiritual DNA.
        Prophetic Intercession.
      </unique_perspectives>
    </key_elements>

    <content_guidelines>
      Use Hebrew terms and covenant language.
      Interpret current events through a prophetic, Israel-centric lens.
      Emphasize the believer's authority and responsibility in manifesting God's Kingdom.
      Encourage readers to discover their true identity in Christ and fulfill their God-given purpose.
      Incorporate teachings on biblical feasts and their relevance to Christians.
      Address spiritual warfare and the importance of standing firm in faith.
      Stress the interconnected destinies of Israel and the Christian Church.
      Use passionate, declarative language to motivate readers to action.
      Share personal anecdotes to illustrate spiritual principles.
      Promote a supernatural lifestyle and expectation of God's intervention.
    </content_guidelines>
  </book_reference>
"""

DEVOTIONAL_INSTRUCTIONS = """
    <instructions>
        Generate a personalized daily devotional based on <devotional_parameters> and <reader_profile> that encourages the reader to live a life of impact and fulfill their God-given purpose. Create a new devotional each time prompted, following the <format> and <rules>. This devotional should encourage them to take action in alignment with <curt_landry_principles> and <ministry_values>. Use the <style_guide> and <book_reference> to inform the tone and approach.
    </instructions>
    <format>
      <title>
        Write an impactful title that grabs the reader's attention and makes them excited about reading the devotional relevant to today's topic and verse. Output in title tag.
      </title>
      <introduction>
        Write a 2-sentence encouragement to the reader, by name, combining today's topic, context of the verse, their personal purpose statement, and related context into a powerful statement. Speak over them the goodness of God, their purpose, their identity, and that they do and will live a life of purpose. Output in introduction tag.
      </introduction>
      <verse>
        Quote the given verse using the NKJV Bible, be sure to reference the book, chapter, and verse (Example: - Hebrews 11:1). Output in verse tag.
      </verse>
      <insight>
        Combine the most impactful revelation and insight into the power and meaning of this verse, distilled from all sources, including Curt Landry's teachings, and focused on encouraging the reader forward in purpose, impact, and in alignment with their purpose statement in 3 sentences. Output in insight tag.
      </insight>
      <life_application>
        Focus on the verse and its context. Pull from all sources and related topics to find the most important positive and hope-filled life application for the reader in 2 sentences that encourages them to live a life of impact and fulfill their purpose. Tailor this to who they are and the context given. Output in life_application tag.
      </life_application>
      <declaration>
        Turn the main life application and the reader's purpose statement into a 1-sentence positive affirmation and declaration that the reader can declare over themselves. Output in declaration tag.
      </declaration>
      <prayer>
        Turn the main life application into a short prayer for the reader, asking God to make the application real in their life. End by calling out and reminding them of their identity and purpose in Christ in alignment with their purpose statement. Output in prayer tag.
      </prayer>
      <journal>
        Turn the main life application in the context of the reader's purpose statement into a journaling prompt that challenges them to think more deeply about how this message applies to their life and what action steps they can take today to move into a place of greater impact and purpose. Output in journal tag. 
      </journal>
    </format>
    <rules>
      1. Return the response as JSON.
      2. Tailor the output to the context and reader's profile and purpose statement.
      3. Don't include word counts in the output.
      4. Provide only the requested information. Your response will be used in an application expecting just the requested content. No filler.
      5. Speak directly to the reader named in the reader profile.
      6. Primarily source information and commentary from the given context and Curt Landry or Curt Landry Ministries.
      7. Use teachings from similar teachers: John Kilpatrick, Michael Brown, Steve Hill, Paul Wilbur, Robert Henderson.
      8. Also reference the following as context: Strong's concordance, Vine's expository Dictionary, Mounce Reverse Interlinear New Testament, Gems from the Greek Vol. 1 & 2, Baker's Evangelical Dictionary of Biblical Theology, Easton's Bible Dictionary, Hitchcock's Bible Names Dictionary, King James Dictionary, Smith's Bible Dictionary, Matthew Henry's Commentary, The Spirit-filled Life New Testament Commentary Series, The Pentecostal Old Testament and New Testament Commentaries, Baker Exegetical Commentary series, Pentecostal Commentary Series, Applied Commentary, Enduring Word Bible Commentary.
    </rules>
"""

# Themes for each day of the week
THEMES =  {
    "Monday":
    "Today's focus is on aligning your life with God's covenant. Reflect on areas where you may need to realign your actions and decisions with God's promises. How can you stand in faith and act in a way that honors the covenant God has made with you? Seek His wisdom, especially in how you support Israel and His Kingdom work.",
    "Tuesday":
    "Today, emphasize the importance of discipline in your walk with God. Where can you apply more focus, set boundaries, and create intentional steps toward fulfilling your calling? How is God calling you to walk in greater obedience? Commit to making decisions today that reflect discipline, knowing it leads to true freedom.",
    "Wednesday":
    "Today's devotional centers on discovering your Kingdom identity and vision. Reflect on how God sees you and the unique calling He has placed on your life. What actions can you take today to step into that identity more fully? Ask God to give you clarity on your purpose and boldness to walk it out.",
    "Thursday":
    "Today's focus is on living a life of generosity and service. Who can you bless today with your time, prayers, or resources? Reflect on how your life can serve as a vessel for God's love. Consider how generosity aligns you with God's heart and His purposes for His people.",
    "Friday":
    "Today, focus on living in faith and expecting the supernatural. Where do you need God's miraculous intervention? Step out in faith and trust that God's power is at work in your life. What bold steps can you take today that require trust in His provision and promises?",
    "Saturday":
    "Today is Shabbat—a time to rest and reflect. Take a step back from action and enter into God's rest. Reflect on the past week's victories and lessons, and thank God for His faithfulness. How can you rest in His presence today, knowing He provides all you need?",
    "Sunday":
    "Today's focus is on revival and awakening. Reflect on how God is stirring your heart and where He is calling you to bring revival. What steps can you take to carry His light into your community? Pray for awakening, both in your life and in the lives of those around you, as you walk boldly in your calling."
}

# Bible Verses
VERSES = [    
    "Jeremiah 29:11", "Proverbs 16:9", "Philippians 3:14",
    "Colossians 3:23-24", "Matthew 5:16", "Ephesians 2:10", "Proverbs 19:21",
    "Romans 8:28", "1 Corinthians 10:31", "Psalm 37:4", "Proverbs 3:5-6",
    "Isaiah 41:10", "2 Timothy 1:9", "Micah 6:8", "Philippians 4:13",
    "Joshua 1:9", "Ecclesiastes 3:1", "Matthew 6:33", "Galatians 6:9",
    "1 Peter 4:10", "Romans 12:2", "Proverbs 16:3", "James 1:12",
    "Philippians 1:6", "Psalm 20:4", "1 Corinthians 9:24-25", "Isaiah 40:31",
    "2 Corinthians 5:20", "Proverbs 29:18", "Hebrews 12:1-2", "Psalm 138:8",
    "Deuteronomy 31:8", "2 Thessalonians 1:11", "1 Timothy 4:12",
    "Romans 12:6-8", "Proverbs 16:1", "Psalm 139:13-14", "Galatians 1:15-16",
    "Exodus 9:16", "Isaiah 43:7", "John 15:16", "Acts 13:36", "Ephesians 4:1",
    "Philippians 2:13", "1 Corinthians 7:17", "Romans 11:29", "2 Peter 1:10",
    "Colossians 1:16", "1 Peter 2:9", "Isaiah 42:6", "Jeremiah 1:5",
    "Romans 8:30", "1 Corinthians 1:9", "Ephesians 1:11", "2 Timothy 2:15",
    "Titus 2:14", "1 Peter 3:9", "Revelation 3:8", "Psalm 57:2",
    "Proverbs 21:5", "Isaiah 46:10", "Matthew 28:19-20", "Luke 12:48",
    "John 17:4", "Acts 20:24", "Romans 12:1", "1 Corinthians 15:58",
    "2 Corinthians 5:9", "Galatians 5:13", "Ephesians 5:15-17",
    "Philippians 3:12-14", "Colossians 4:17", "1 Thessalonians 5:24",
    "2 Timothy 4:7", "Hebrews 10:36", "James 2:14-17", "1 Peter 2:21",
    "2 Peter 3:9", "1 John 3:8", "Psalm 138:8", "Proverbs 16:4",
    "Ecclesiastes 12:13", "Isaiah 43:21", "Jeremiah 32:19", "Daniel 1:8",
    "Hosea 6:6", "Habakkuk 2:2-3", "Zechariah 4:6", "Matthew 5:13-14",
    "Mark 10:45", "Luke 19:10", "John 4:34", "Acts 26:16-18", "Romans 14:8",
    "1 Corinthians 3:9", "2 Corinthians 6:1", "Galatians 2:20",
    "Ephesians 3:20-21", "Philippians 1:21", "Colossians 2:6-7",
    "1 Thessalonians 2:12", "2 Timothy 2:21", "Titus 3:1", "Hebrews 13:21",
    "James 4:8", "1 Peter 5:10", "2 Peter 1:3", "1 John 2:17", "Psalm 33:11",
    "Proverbs 19:21", "Ecclesiastes 3:11", "Isaiah 55:8-9", "Jeremiah 17:7-8",
    "Lamentations 3:24", "Ezekiel 36:26-27", "Daniel 2:20-21", "Joel 2:28",
    "Amos 3:7", "Micah 7:7", "Habakkuk 3:19", "Zephaniah 3:17", "Haggai 2:9",
    "Zechariah 8:13", "Malachi 3:1", "Matthew 10:16", "Mark 16:15",
    "Luke 9:23", "John 6:38", "Acts 1:8", "Romans 5:2-5", "1 Corinthians 2:9",
    "2 Corinthians 3:18", "Galatians 5:22-23", "Ephesians 4:22-24",
    "Philippians 2:3-4", "Colossians 3:2",
    "2 Timothy 3:16-17", "Titus 2:11-12", "Hebrews 11:1", "James 1:22",
    "1 Peter 1:13", "2 Peter 3:18", "1 John 4:19", "Jude 1:20-21",
    "Revelation 21:5"
]

# Load existing users.json data
def load_users_data():
    if os.path.exists(users_file_path):
        try:
            with open(users_file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logging.error("Error reading users.json, starting with an empty dictionary.")
            return {}
    return {}

# Save users data to users.json
def save_users_data(users_data):
    try:
        with open(users_file_path, "w") as f:
            json.dump(users_data, f, indent=4)
    except IOError:
        logging.error("Error writing to users.json.")

# Monitor the batch request to anthropic
def monitor_batch(batch_id, poll_interval=60):
    logging.info(f"Monitoring batch ID: {batch_id}")

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts

        logging.info(f"[{status}] Processing: {counts.processing}, "
                     f"Success: {counts.succeeded}, Errors: {counts.errored}, "
                     f"Canceled: {counts.canceled}, Expired: {counts.expired}")

        if status == "completed" or status == "ended":
            if batch.results_url:
                process_batch_results(batch.results_url)
                logging.info(f"Results ready: {batch.results_url}")
                return batch
            else:
                logging.info("Waiting for results_url to be available...")
        elif status in ("failed", "canceled"):
            logging.warning(f"Batch finished with status: {status}")
            return batch

        time.sleep(poll_interval)

# Process the batch response from anthropic
def process_batch_results(results_url, users_file_path="./tmp/users.json"):
    # Load all users from users.json (keyed by user_id)
    try:
        with open(users_file_path, "r") as f:
            users_data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to read users.json: {e}")
        return

    # Download Anthropic results (NDJSON format)
    response = requests.get(results_url, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01"
    })

    if response.status_code != 200:
        logging.error(f"Failed to fetch results: {response.status_code} - {response.text}")
        return

    updated = 0

    for line in response.text.strip().splitlines():
        try:
            result_line = json.loads(line)
            custom_id = result_line.get("custom_id")
            message = result_line.get("result", {}).get("message", {})
            content_blocks = message.get("content", [])

            # Extract the first text block
            text_block = next((b["text"] for b in content_blocks if b.get("type") == "text"), None)
            if text_block is None:
                logging.warning(f"No text content found for {custom_id}")
                continue

            try:
                devotional_data = json.loads(text_block)
            except json.JSONDecodeError as e:
                logging.warning(f"Could not parse devotional JSON for {custom_id}: {e}")
                devotional_data = {"raw_text": text_block}

            # Find the user_id by matching custom_id
            matched_user_id = next(
                (uid for uid, data in users_data.items() if data.get("custom_id") == custom_id),
                None
            )

            if matched_user_id:
                users_data[matched_user_id]["devotional"] = devotional_data
                updated += 1
            else:
                logging.warning(f"custom_id {custom_id} not found in users.json")

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in result line: {e}")

    # Save changes back to users.json
    try:
        with open(users_file_path, "w") as f:
            json.dump(users_data, f, indent=2)
        logging.info(f"Updated {updated} user(s) with devotional content in users.json")
    except IOError as e:
        logging.error(f"Failed to write to users.json: {e}")

# Devotional prompt template
def generate_prompt_template(reader_name, reader_purpose_statement):

  # Select the theme and verse for the current day
  current_day = datetime.now().strftime("%A")
  theme_content = THEMES.get(current_day)
  selected_verse = secrets.choice(VERSES)
  
  DEVOTIONAL_PROMPT_TEMPLATE = f"""<devotional_prompt><devotional_parameters><theme>{theme_content}</theme><focus_verse>{selected_verse}</focus_verse></devotional_parameters><reader_profile><name>{reader_name}</name><purpose_statement>{reader_purpose_statement}</purpose_statement></reader_profile></devotional_prompt>"""
  return DEVOTIONAL_PROMPT_TEMPLATE

# Generate batch job for anthropic
def generate_devotional_content():
    users_file_path = "./tmp/users.json"
    user_map = {}
    requests = []

    # Load all users from users.json (keyed by user_id)
    try:
        with open(users_file_path, "r") as f:
            users = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to read users.json: {e}")
        return

    for user_id, user_data in users.items():
        prompt = user_data.get("personalized_prompt")
        if not prompt:
            continue

        # Generate and save custom_id
        custom_id = f"user-{user_id[:8]}-{uuid.uuid4().hex[:6]}"
        user_data["custom_id"] = custom_id  # Store in user_map
        users[user_id]["custom_id"] = custom_id  # Save back into users.json
        user_map[custom_id] = user_data

        request_obj = {
            "custom_id": custom_id,
            "params": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1000,
                "temperature": 0.3,
                "system": [
                    {"type": "text", "text": ANTHROPIC_ROLE, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": CURT_LANDRY_PRINCIPLES, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": STYLE_GUIDE, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": DEVOTIONAL_INSTRUCTIONS, "cache_control": {"type": "ephemeral"}}
                ],
                "messages": [{"role": "user", "content": prompt}]
            }
        }

        requests.append(request_obj)

    if not requests:
        logging.warning("No valid prompts found. No batch will be submitted.")
        return

    # Save updated users.json with custom_ids
    try:
        with open(users_file_path, "w") as f:
            json.dump(users, f, indent=2)
        logging.info("users.json updated with custom_ids.")
    except IOError as e:
        logging.error(f"Failed to update users.json with custom_ids: {e}")
        return

    logging.info(f"Submitting {len(requests)} requests to Anthropic batch API...")
    response = client.messages.batches.create(requests=requests)

    batch_id = response.id
    with open("./tmp/last_batch_id.txt", "w") as f:
        f.write(batch_id)

    monitor_batch(batch_id)

    logging.info(f"Batch {batch_id} completed and processed.")
    upload_db_user()
    return response

# Upload devotional content to firebase, trigger email
def upload_db_user():
    users_file_path = "./tmp/users.json"
    uploaded_users_file_path = "./tmp/uploaded_users.json"
    success_count = 0
    fail_count = 0

    # Load existing uploaded users
    if os.path.exists(uploaded_users_file_path):
        try:
            with open(uploaded_users_file_path, "r") as f:
                uploaded_users = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load uploaded_users.json: {e}")
            uploaded_users = {}
    else:
        uploaded_users = {}

    # Load user data
    try:
        with open(users_file_path, "r") as f:
            users_data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load users.json: {e}")
        return

    for user_id, user_data in users_data.items():
        if user_id in uploaded_users:
            logging.info(f"⏩ Skipping already uploaded user {user_id}")
            continue

        user_email = user_data.get("email")
        devotional_content = user_data.get("devotional")

        if not user_email or not devotional_content:
            logging.warning(f"Skipping user {user_id} due to missing email or devotional")
            fail_count += 1
            continue

        devotional_record = {
            "title": devotional_content.get("title", ""),
            "introduction": devotional_content.get("introduction", ""),
            "verse": devotional_content.get("verse", ""),
            "insight": devotional_content.get("insight", ""),
            "life_application": devotional_content.get("life_application", ""),
            "declaration": devotional_content.get("declaration", ""),
            "prayer": devotional_content.get("prayer", ""),
            "journal": devotional_content.get("journal", ""),
            "dateTimeCreated": datetime.now(pytz.UTC).isoformat(),
            "doc_id": None,
            "forUser": user_id,
            "email": user_email,
            "isFavorite": False
        }

        try:
            devotional_ref = db.collection("devotionals").add(devotional_record)
            devotional_doc_id = devotional_ref[1].id
            devotional_record["doc_id"] = devotional_doc_id
            logging.info(f"✅ Devotional uploaded for user {user_id} ({user_email})")
        except DeadlineExceeded as e:
            logging.error(f"DeadlineExceeded adding devotional for user {user_id}: {e}")
            fail_count += 1
            continue

        try:
            db.collection("devotionals").document(devotional_doc_id).set(devotional_record)
            trigger_email(user_email, devotional_record["introduction"])
            logging.info(f"✅ Devotional email sent for user {user_id} ({user_email})")
            success_count += 1

            # Immediately record successful upload
            uploaded_users[user_id] = {
                "timestamp": datetime.now(pytz.UTC).isoformat()
            }
            try:
                with open(uploaded_users_file_path, "w") as f:
                    json.dump(uploaded_users, f, indent=2)
            except IOError as e:
                logging.error(f"Failed to update uploaded_users.json for user {user_id}: {e}")

        except DeadlineExceeded as e:
            logging.error(f"DeadlineExceeded setting devotional for user {user_id}: {e}")
            fail_count += 1
            continue

    logging.info(f"Finished uploading devotionals. Success: {success_count}, Failed: {fail_count}")

# Trigger email sequence
def trigger_email(email, devotional_data):
    access_token = os.getenv("KEAP_API_KEY")

    # Step 1: Get Keap contact ID
    contact_id = get_keap_contact_id(access_token, email)
    time.sleep(1) 

    # Case 1: Valid integer contact ID
    if isinstance(contact_id, int):
        logging.info(f"Contact ID for {email}: {contact_id}")

        # Step 2: Update devotional field
        update_keap_contact_field(contact_id, devotional_data, access_token)
        time.sleep(1)
        # Step 3: Trigger email
        keap_response = trigger_keap_devotional_email(contact_id, access_token)
        logging.info(f"Keap Email Trigger Response for {email}: {keap_response}")
        time.sleep(1)

    # Case 2: Keap quota exceeded (HTTP 429)
    elif isinstance(contact_id, dict) and contact_id.get("error") == 429:
        raw_message = contact_id.get("message", "")
        try:
            parsed = json.loads(raw_message)
            message = parsed.get("message", "Quota exceeded")
            status = parsed.get("status", "Request Throttled")
            logging.warning(f"Quota exceeded for {email}: {message} ({status})")
        except json.JSONDecodeError:
            logging.warning(f"Quota exceeded for {email}. Raw message: {raw_message}")

    # Case 3: No contact found or unexpected response
    else:
        logging.warning(f"No valid contact ID returned for {email}. Response: {contact_id}")

# Get the Keap user contact ID
def get_keap_contact_id(access_token: str, email: str):
    url = "https://api.infusionsoft.com/crm/rest/v1/contacts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "email": email,
        "optional_properties": ["email_addresses"]
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if "contacts" in data and len(data["contacts"]) > 0:
            return data["contacts"][0]["id"]
        else:
            return None
    else:
        return {"error": response.status_code, "message": response.text}

# Update custom field ID 695 for specific contact
def update_keap_contact_field(contact_id, devotional_data, access_token):
    if not isinstance(contact_id, int) or contact_id <= 0:
        return {"error": "Invalid contact_id. Must be a positive integer."}

    url = f"https://api.infusionsoft.com/crm/rest/v1/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "custom_fields": [
            {
                "content": devotional_data,
                "id": 695
            }
        ]
    }

    response = requests.patch(url, json=payload, headers=headers)
    return response.json() if response.status_code in [200, 201] else response.text

# Trigger Keap API devotional for contact_id
def trigger_keap_devotional_email(contact_id, access_token):
    if not isinstance(contact_id, int) or contact_id <= 0:
        return {"error": "Invalid contact_id. Must be a positive integer."}

    url = "https://api.infusionsoft.com/crm/rest/v1/campaigns/goals/is104/sendlsdevotional"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {"contact_id": contact_id}

    response = requests.post(url, json=payload, headers=headers)
    return response.json() if response.status_code == 200 else response.text

# Create batch users from FB for batch processing
def main():
    batch_size = 500
    query = db.collection('users').order_by('__name__').limit(batch_size)
    last_doc = None

    users_data = load_users_data()
    processed_count = 0

    while True:
        try:
            users_batch = list(query.stream())
        except DeadlineExceeded as e:
            logging.error(f"DeadlineExceeded while streaming users batch: {e}")
            break

        if not users_batch:
            break

        for user in users_batch:
            user_id = user.id

            if user_id in users_data:
                logging.info(f"Skipping user {user_id}, already processed.")
                continue

            try:
                user_doc = db.collection('users').document(user_id).get()
            except DeadlineExceeded as e:
                logging.error(f"DeadlineExceeded fetching document for user {user_id}: {e}")
                continue

            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_email = user_data.get("email")
                first_name = user_data.get("firstName", "Member")

                if user_email:
                    try:
                        why_statement_docs = db.collection("whyStatements").where("forUser", "==", user_id).get()
                    except DeadlineExceeded as e:
                        logging.error(f"DeadlineExceeded fetching whyStatements for user {user_id}: {e}")
                        continue

                    if not why_statement_docs:
                        logging.error(f"Why Statement not found for user {user_id}")
                        continue

                    purpose_statement = why_statement_docs[0].to_dict().get("purposeStatement", "")

                    personalized_prompt = generate_prompt_template(first_name, purpose_statement)

                    user_entry = {
                        "processed_at": datetime.now(pytz.UTC).isoformat(),
                        "name": first_name,
                        "email": user_email,
                        "purposeStatement": purpose_statement,
                        "personalized_prompt": personalized_prompt
                    }

                    users_data[user_id] = user_entry
                    processed_count += 1

        # Save updated users.json after each batch
        save_users_data(users_data)

        last_doc = users_batch[-1]
        query = db.collection('users').order_by('__name__').start_after(last_doc).limit(batch_size)

    logging.info(f"Finished user prep. Added {processed_count} new user(s) to users.json.")
    generate_devotional_content()

if __name__ == "__main__": main()
