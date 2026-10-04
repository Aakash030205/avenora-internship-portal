from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, quote_plus
import sqlite3, os, secrets, uuid

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('AVENORA_DB_PATH', str(BASE_DIR / 'database.db'))).resolve()

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.environ.get('AVENORA_SECRET_KEY') or None,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('AVENORA_HTTPS', '0') == '1',
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
)

if not app.config['SECRET_KEY']:
    # Local development convenience only.
    # Set AVENORA_SECRET_KEY for stable sessions/deployment.
    app.config['SECRET_KEY'] = secrets.token_hex(32)

ADMIN_EMAIL = os.environ.get(
    'AVENORA_ADMIN_EMAIL',
    'admin@avenora.in'
).strip().lower()

ADMIN_PASSWORD = os.environ.get('AVENORA_ADMIN_PASSWORD')

PAYMENT_INSTRUCTIONS = os.environ.get(
    'AVENORA_PAYMENT_INSTRUCTIONS',
    'Pay only to the official UPI ID shown on this page. '
    'Never share your UPI PIN, OTP, or banking password.'
)


TRACKS = [
    {
        'slug': 'web-development',
        'title': 'Web Development',
        'icon': '🌐',
        'level': 'Beginner to Intermediate',
        'summary': 'Build responsive websites and full-stack web applications.',
        'weeks': 8,
        'lessons': [
            (
                'html-foundations',
                'HTML Foundations',
                'Structure accessible pages with headings, links, lists and images.',
                'Learn semantic HTML, document structure, links, images and accessible markup.',
                'DOCTYPE, headings, lists, links, images',
                'Build a personal profile page with semantic HTML.',
                'https://developer.mozilla.org/en-US/docs/Learn/HTML'
            ),
            (
                'css-responsive',
                'CSS & Responsive Design',
                'Create polished layouts that adapt to different screens.',
                'Use selectors, the box model, Flexbox, Grid and media queries.',
                'Selectors, box model, Flexbox, Grid, media queries',
                'Create a responsive landing page with cards and navigation.',
                'https://developer.mozilla.org/en-US/docs/Learn/CSS'
            ),
            (
                'javascript-basics',
                'JavaScript Essentials',
                'Add logic and interactivity to your web pages.',
                'Practice variables, functions, arrays, events and DOM manipulation.',
                'Variables, functions, arrays, DOM, events',
                'Build an interactive task list or form validator.',
                'https://developer.mozilla.org/en-US/docs/Learn/JavaScript'
            ),
            (
                'web-final-project',
                'Final Website Project',
                'Plan, test and submit a complete responsive website.',
                'Combine HTML, CSS and JavaScript into a tested project with a README.',
                'Planning, accessibility, testing, GitHub, deployment',
                'Submit a repository URL and optional live demo.',
                'https://docs.github.com/en/pages'
            ),
            (
                'web-accessibility',
                'Accessibility & Semantic HTML',
                'Make pages more usable for different people and devices.',
                'Use semantic landmarks, descriptive links, labels, alt text and keyboard-friendly controls to improve accessibility.',
                'Semantic landmarks, labels, alt text, keyboard navigation',
                'Audit your profile page and fix five accessibility issues.',
                'https://developer.mozilla.org/en-US/docs/Learn/Accessibility'
            ),
            (
                'web-forms',
                'Forms & Validation',
                'Collect and validate user input in a browser.',
                'Build forms with associated labels and use native constraints plus JavaScript feedback for invalid input.',
                'Labels, required fields, constraints, validation messages',
                'Create a registration form with name, email and password checks.',
                'https://developer.mozilla.org/en-US/docs/Learn/Forms'
            ),
            (
                'web-fetch-api',
                'DOM, Events & Fetch',
                'Connect page interactions to asynchronous data.',
                'Use DOM events and the Fetch API to request data, handle failures and update the page without a full reload.',
                'DOM events, promises, async/await, fetch, errors',
                'Build a small page that loads sample JSON and displays a loading/error state.',
                'https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API'
            ),
            (
                'web-deployment-git',
                'Git, GitHub & Deployment',
                'Prepare a website for sharing and maintenance.',
                'Track changes with Git, write a useful README and publish a static site with a clear project structure.',
                'Commits, branches, README, GitHub Pages, deployment checks',
                'Publish a responsive site and document its URL and test steps.',
                'https://docs.github.com/en/pages'
            )
        ]
    },

    {
        'slug': 'python-programming',
        'title': 'Python Programming',
        'icon': '🐍',
        'level': 'Beginner to Intermediate',
        'summary': 'Learn Python fundamentals, automation and problem solving.',
        'weeks': 8,
        'lessons': [
            (
                'python-foundations',
                'Python Foundations',
                'Learn variables, data types, operators and input/output.',
                'Python is a general-purpose language. Start with values, variables, types and readable statements.',
                'Variables, strings, numbers, booleans, input/output',
                'Write a program that collects a name and calculates a simple total.',
                'https://docs.python.org/3/tutorial/introduction.html'
            ),
            (
                'python-control',
                'Conditions, Loops & Collections',
                'Control program flow and work with lists and dictionaries.',
                'Use if/elif/else, for/while loops, lists, tuples, sets and dictionaries.',
                'Conditions, loops, lists, dictionaries, comprehensions',
                'Create a command-line marks calculator for several subjects.',
                'https://docs.python.org/3/tutorial/controlflow.html'
            ),
            (
                'python-functions',
                'Functions, Files & Errors',
                'Organize reusable code and handle common errors.',
                'Create functions, read/write files safely and handle exceptions.',
                'Functions, modules, file handling, exceptions',
                'Build a text-based expense tracker that saves entries to a file.',
                'https://docs.python.org/3/tutorial/errors.html'
            ),
            (
                'python-project',
                'Python Final Project',
                'Deliver a tested Python application.',
                'Plan a small application, validate inputs, separate logic into functions and document it.',
                'Project structure, testing, validation, README',
                'Submit a CLI utility or automation script with documentation.',
                'https://docs.python.org/3/library/unittest.html'
            ),
            (
                'python-modules',
                'Modules & Packages',
                'Reuse standard-library modules and organize Python code.',
                'Import modules intentionally, use virtual environments for dependencies and separate reusable logic from script entry points.',
                'import, standard library, packages, virtual environments',
                'Create a command-line utility using at least two standard-library modules.',
                'https://docs.python.org/3/tutorial/modules.html'
            ),
            (
                'python-oop',
                'Object-Oriented Python',
                'Model related data and behavior with classes.',
                'Classes combine data and methods. Use objects when they make a program easier to understand and maintain.',
                'Classes, objects, __init__, methods, composition',
                'Model a library book and borrowing status with a small class.',
                'https://docs.python.org/3/tutorial/classes.html'
            ),
            (
                'python-testing',
                'Testing & Debugging',
                'Find defects and verify expected behavior.',
                'Use clear assertions, small reproducible test cases, tracebacks and the unittest framework to improve reliability.',
                'Assertions, tracebacks, unittest, edge cases, debugging',
                'Write unit tests for a marks calculator, including invalid inputs.',
                'https://docs.python.org/3/library/unittest.html'
            ),
            (
                'python-automation',
                'Python Automation Project',
                'Automate a repeatable file or data task.',
                'A good automation script validates inputs, handles exceptions, logs useful information and avoids destructive defaults.',
                'Pathlib, CSV/JSON, logging, exceptions, CLI arguments',
                'Build a script that summarizes a CSV file and reports malformed rows.',
                'https://docs.python.org/3/library/csv.html'
            )
        ]
    },

    {
        'slug': 'ai-data-science',
        'title': 'AI & Data Science',
        'icon': '🤖',
        'level': 'Beginner',
        'summary': 'Explore data cleaning, analysis, visualization and ML concepts.',
        'weeks': 8,
        'lessons': [
            (
                'data-fundamentals',
                'Data Science Foundations',
                'Understand datasets, data types and analytical questions.',
                'Define a useful question, inspect columns and distinguish numerical and categorical data.',
                'Rows/columns, data types, missing values, questions',
                'Create a small dataset and write five questions it can answer.',
                'https://pandas.pydata.org/docs/getting_started/intro_tutorials/'
            ),
            (
                'data-cleaning',
                'Data Cleaning with Python',
                'Prepare consistent data for analysis.',
                'Explore missing values, duplicates, inconsistent labels and validation checks.',
                'Pandas DataFrame, nulls, duplicates, types',
                'Clean a sample CSV and document each change.',
                'https://pandas.pydata.org/docs/user_guide/missing_data.html'
            ),
            (
                'data-visualization',
                'Analysis & Visualization',
                'Communicate findings with clear charts and summaries.',
                'Choose charts that match the question and avoid misleading scales or labels.',
                'Bar/line charts, distributions, labels, interpretation',
                'Create three charts and summarize two insights from each.',
                'https://matplotlib.org/stable/tutorials/'
            ),
            (
                'ai-final-project',
                'Introductory ML Project',
                'Build and evaluate a small supervised-learning experiment.',
                'Split data into training and test sets, compare a baseline and explain limitations.',
                'Features, labels, train/test split, metrics, bias',
                'Submit a documented notebook or script with a clear evaluation.',
                'https://scikit-learn.org/stable/getting_started.html'
            ),
            (
                'data-statistics',
                'Descriptive Statistics',
                'Summarize data before making conclusions.',
                'Use mean, median, spread and distributions to understand data; inspect outliers and sample size before interpreting results.',
                'Mean, median, variance, distribution, outliers',
                'Summarize a small dataset and explain which statistics are most informative.',
                'https://pandas.pydata.org/docs/getting_started/intro_tutorials/06_calculate_statistics.html'
            ),
            (
                'data-feature-engineering',
                'Feature Preparation',
                'Prepare useful model input features.',
                'Encode categories and scale numeric values when appropriate. Fit transformations on training data to avoid leakage.',
                'Categorical encoding, scaling, leakage, feature selection',
                'Describe preprocessing steps for a dataset and identify possible leakage.',
                'https://scikit-learn.org/stable/modules/preprocessing.html'
            ),
            (
                'ml-model-evaluation',
                'Model Evaluation',
                'Measure a model using suitable metrics.',
                'Choose evaluation metrics based on the task and class balance; compare against a simple baseline and inspect errors.',
                'Train/test split, accuracy, precision, recall, baseline',
                'Compare two hypothetical classifiers and justify the better metric for the task.',
                'https://scikit-learn.org/stable/modules/model_evaluation.html'
            ),
            (
                'data-ethics',
                'Responsible AI & Data Ethics',
                'Recognize privacy, fairness and reproducibility concerns.',
                'Document data sources, protect personal information, check group-level performance and communicate uncertainty and limitations.',
                'Privacy, bias, consent, reproducibility, limitations',
                'Write a short model card describing intended use, risks and limitations.',
                'https://www.nist.gov/itl/ai-risk-management-framework'
            )
        ]
    },

    {
        'slug': 'embedded-iot',
        'title': 'Embedded Systems & IoT',
        'icon': '🔌',
        'level': 'Beginner',
        'summary': 'Learn microcontrollers, sensors, embedded C concepts and IoT design.',
        'weeks': 8,
        'lessons': [
            (
                'embedded-basics',
                'Embedded Systems Foundations',
                'Understand microcontrollers, inputs, outputs and constraints.',
                'An embedded system combines hardware and software for a defined task. Review GPIO, memory and timing.',
                'MCU, GPIO, firmware, power, timing',
                'Draw a block diagram for a temperature-monitoring device.',
                'https://docs.arduino.cc/learn/'
            ),
            (
                'embedded-c',
                'Embedded C Concepts',
                'Practice variables, conditions, functions and bitwise ideas.',
                'Use small functions and clear state handling; hardware registers differ by platform.',
                'Types, functions, bitwise operations, state machines',
                'Write pseudocode for a button-controlled LED state machine.',
                'https://en.cppreference.com/w/c/language'
            ),
            (
                'sensors-connectivity',
                'Sensors & Connectivity',
                'Plan sensor readings and communication safely.',
                'Consider sensor ranges, sampling intervals, calibration and protocols such as UART, I2C, SPI and MQTT.',
                'Sensors, calibration, UART, I2C, SPI, MQTT',
                'Design a sensor data flow and identify likely failure cases.',
                'https://mqtt.org/'
            ),
            (
                'iot-project',
                'IoT Mini Project',
                'Document an IoT prototype and test plan.',
                'Describe components, data flow, safety limits, error handling and test cases before implementation.',
                'Architecture, telemetry, reliability, test plan',
                'Submit a prototype report, code repository or simulator evidence.',
                'https://docs.espressif.com/projects/esp-idf/en/stable/esp32/'
            ),
            (
                'gpio-interfacing',
                'GPIO & Digital Interfacing',
                'Plan digital input and output connections.',
                'Check voltage levels, pin limits, pull-up or pull-down needs and common ground before connecting a microcontroller circuit.',
                'Digital input, output, pull-up, logic levels, current limits',
                'Simulate a push-button controlling an LED and document its truth table.',
                'https://docs.arduino.cc/learn/microcontrollers/digital-pins/'
            ),
            (
                'analog-sensors',
                'Analog Sensors & ADC',
                'Convert sensor signals into useful readings.',
                'An ADC samples an analog voltage into a digital value; resolution, reference voltage and calibration affect interpretation.',
                'ADC, resolution, reference voltage, sampling, calibration',
                'Design a simulated temperature or light sensor reading and explain the conversion steps.',
                'https://docs.arduino.cc/learn/microcontrollers/analog-input/'
            ),
            (
                'iot-power-safety',
                'Power, Protection & Reliability',
                'Design safer and more reliable prototypes.',
                'Match supply voltage and current to components, use suitable protection and plan safe behavior on sensor or network failure.',
                'Supply ratings, current budget, protection, watchdog, fail-safe',
                'Create a component power budget and a fault-response table for an IoT node.',
                'https://docs.espressif.com/projects/esp-idf/en/stable/esp32/'
            ),
            (
                'iot-cloud-telemetry',
                'IoT Telemetry & Dashboard',
                'Plan the flow from device readings to a dashboard.',
                'Telemetry systems need message formats, timestamps, authentication, reconnect behavior and clear handling of stale data.',
                'MQTT topics, JSON payloads, timestamps, authentication, dashboards',
                'Design a sample JSON telemetry payload and sketch a dashboard for it.',
                'https://mqtt.org/'
            )
        ]
    },

    {
        'slug': 'software-testing',
        'title': 'Software Testing',
        'icon': '🧪',
        'level': 'Beginner to Intermediate',
        'summary': 'Practice test design, API checks, bug reports and quality assurance.',
        'weeks': 8,
        'lessons': [
            (
                'testing-foundations',
                'Testing Foundations',
                'Understand testing levels and why software defects occur.',
                'Testing compares actual behavior against expected behavior and reduces risk; it cannot prove absence of defects.',
                'SDLC/STLC, smoke, regression, integration, UAT',
                'Write test scenarios for a login page.',
                'https://www.istqb.org/'
            ),
            (
                'test-cases',
                'Test Cases & Defect Reports',
                'Write reproducible tests and clear bug reports.',
                'Include preconditions, steps, test data, expected/actual results and severity.',
                'Positive/negative tests, boundary values, severity, priority',
                'Create ten test cases for a registration form and two bug reports.',
                'https://www.guru99.com/test-case.html'
            ),
            (
                'api-testing',
                'API & Data Validation',
                'Check HTTP APIs and verify returned data.',
                'Inspect status codes, response bodies, headers, authentication and data consistency.',
                'HTTP methods, status codes, JSON, Postman, SQL checks',
                'Design API tests for a simple student records endpoint.',
                'https://learning.postman.com/docs/introduction/overview/'
            ),
            (
                'testing-project',
                'QA Final Project',
                'Deliver a compact quality assurance portfolio.',
                'Prepare a test plan, evidence, defects and a final summary with clear coverage limits.',
                'Test plan, execution evidence, traceability, summary',
                'Submit test cases, sample API results and a concise QA report.',
                'https://playwright.dev/docs/intro'
            ),
            (
                'testing-boundaries',
                'Boundary & Equivalence Testing',
                'Select test values that reveal common defects.',
                'Partition inputs into equivalent groups and test boundaries where behavior commonly changes.',
                'Equivalence partitioning, boundary values, invalid inputs, test data',
                'Design boundary tests for an age field accepting values from 18 to 60.',
                'https://www.istqb.org/'
            ),
            (
                'testing-regression',
                'Regression & Integration Testing',
                'Choose test coverage after a change.',
                'Regression checks existing behavior after modifications; integration tests focus on interactions between components.',
                'Regression, integration, smoke tests, risk, coverage',
                'Create a regression checklist for a login flow after a password reset change.',
                'https://playwright.dev/docs/intro'
            ),
            (
                'testing-performance-security',
                'Performance & Security Basics',
                'Recognize common non-functional risks.',
                'Check response time under representative load and test security controls within authorized environments and defined scope.',
                'Latency, throughput, load, authentication, authorization',
                'Write a safe high-level test plan for login performance and access control.',
                'https://owasp.org/www-project-web-security-testing-guide/'
            ),
            (
                'testing-automation',
                'Test Automation Fundamentals',
                'Identify stable candidates for automated tests.',
                'Automate repeatable, deterministic checks first; keep test data controlled and avoid brittle selectors or tests dependent on timing.',
                'Assertions, fixtures, selectors, flakiness, CI',
                'Outline an automated smoke test for a registration form.',
                'https://playwright.dev/docs/writing-tests'
            )
        ]
    },

    {
        'slug': 'electrical-automation',
        'title': 'Electrical & Industrial Automation',
        'icon': '⚡',
        'level': 'Beginner',
        'summary': 'Explore electrical fundamentals, control systems, PLC and automation safety.',
        'weeks': 8,
        'lessons': [
            (
                'electrical-foundations',
                'Electrical Fundamentals',
                'Review voltage, current, resistance and power.',
                'Use Ohm’s law and basic power relationships. Follow lab rules and never work on energized equipment without authorization.',
                'Voltage, current, resistance, power, safety',
                'Solve five basic circuit calculations and note safety precautions.',
                'https://www.allaboutcircuits.com/textbook/'
            ),
            (
                'control-systems',
                'Control Systems Basics',
                'Understand sensors, actuators and feedback loops.',
                'A control system measures a process and changes an output to meet a desired target.',
                'Open/closed loop, sensor, actuator, setpoint, feedback',
                'Draw a block diagram for tank-level control.',
                'https://www.nise.org/'
            ),
            (
                'plc-logic',
                'PLC & Ladder Logic',
                'Read simple PLC logic and interlocks conceptually.',
                'PLC programs use inputs, logic and outputs. Practice in a simulator or de-energized training setup.',
                'PLC scan, contacts, coils, timers, interlocks',
                'Create a simulated start/stop motor-control ladder diagram.',
                'https://www.plcopen.org/'
            ),
            (
                'automation-project',
                'Automation Mini Project',
                'Document an automation design and verification plan.',
                'State requirements, I/O list, sequence, alarms, fail-safe behavior and test procedure.',
                'I/O list, sequence chart, alarms, verification',
                'Submit a simulated automation project report and test checklist.',
                'https://www.rockwellautomation.com/en-us/support/documentation.html'
            ),
            (
                'electrical-circuits',
                'Series & Parallel Circuits',
                'Analyze basic circuit arrangements.',
                'Use equivalent resistance and circuit laws to predict current and voltage; verify calculations in a simulator before lab work.',
                'Series circuits, parallel circuits, Kirchhoff laws, equivalent resistance',
                'Solve and simulate a low-voltage series/parallel circuit worksheet.',
                'https://www.allaboutcircuits.com/textbook/direct-current/'
            ),
            (
                'motors-drives',
                'Motors, Starters & Drives',
                'Understand motor-control components and purpose.',
                'Contactors, overload protection and variable-frequency drives serve different roles; selection and wiring must follow manufacturer documentation.',
                'Motor starter, contactor, overload relay, VFD, interlock',
                'Draw a conceptual motor-control block diagram and label protection devices.',
                'https://www.rockwellautomation.com/en-us/support/documentation.html'
            ),
            (
                'plc-timers-counters',
                'PLC Timers, Counters & Sequencing',
                'Build a timed sequence in a PLC simulator.',
                'Timers and counters support sequence logic; always define reset behavior, interlocks and safe states.',
                'TON/TOF, counters, reset, sequence, interlocks',
                'Create a simulated conveyor sequence with a timer and emergency-stop interlock.',
                'https://www.plcopen.org/'
            ),
            (
                'automation-hmi-safety',
                'HMI, Alarms & Industrial Safety',
                'Design operator feedback and safe fault handling.',
                'HMI screens should show clear status and alarms. Risk assessment, lockout procedures and qualified supervision are essential in real installations.',
                'HMI, alarms, acknowledgement, lockout/tagout, fail-safe',
                'Design a sample HMI screen and alarm-response checklist for a tank system.',
                'https://www.osha.gov/control-hazardous-energy'
            )
        ]
    }
]


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = db()

    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        created_at TEXT NOT NULL,
        account_status TEXT NOT NULL DEFAULT 'active',
        lifecycle_action TEXT,
        lifecycle_at TEXT
    );

    CREATE TABLE IF NOT EXISTS tracks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        icon TEXT NOT NULL,
        summary TEXT NOT NULL,
        level TEXT NOT NULL,
        access_type TEXT NOT NULL DEFAULT 'free'
            CHECK(access_type IN ('free','paid')),
        price REAL NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS enrollments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        track_id INTEGER NOT NULL,
        payment_status TEXT NOT NULL DEFAULT 'not_required',
        payment_reference TEXT,
        enrolled_at TEXT NOT NULL,
        UNIQUE(user_id,track_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(track_id) REFERENCES tracks(id)
    );

    CREATE TABLE IF NOT EXISTS progress(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        lesson_id TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        completed_at TEXT,
        UNIQUE(user_id,lesson_id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS submissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        track_slug TEXT NOT NULL DEFAULT 'web-development',
        github_url TEXT NOT NULL,
        live_url TEXT,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        marks INTEGER,
        feedback TEXT,
        submitted_at TEXT NOT NULL,
        reviewed_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS quiz_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        lesson_id TEXT NOT NULL,
        score INTEGER NOT NULL,
        passed INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS csrf_nonces(
        nonce TEXT PRIMARY KEY,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS portal_settings(
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT NOT NULL DEFAULT ''
    );
    ''')

    # Safe migrations
    migrations = [
        (
            'users',
            'account_status',
            "ALTER TABLE users ADD COLUMN account_status TEXT NOT NULL DEFAULT 'active'"
        ),
        (
            'users',
            'lifecycle_action',
            'ALTER TABLE users ADD COLUMN lifecycle_action TEXT'
        ),
        (
            'users',
            'lifecycle_at',
            'ALTER TABLE users ADD COLUMN lifecycle_at TEXT'
        ),
        (
            'submissions',
            'track_slug',
            "ALTER TABLE submissions ADD COLUMN track_slug TEXT NOT NULL DEFAULT 'web-development'"
        )
    ]

    for table, col, sql in migrations:
        cols = {
            r['name']
            for r in conn.execute(f'PRAGMA table_info({table})')
        }

        if col not in cols:
            conn.execute(sql)

    enrollment_sql = conn.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type='table' AND name='enrollments'"
    ).fetchone()

    if enrollment_sql and 'user_id INTEGER UNIQUE' in (
        enrollment_sql['sql'] or ''
    ):
        conn.execute('ALTER TABLE enrollments RENAME TO enrollments_legacy')

        conn.execute("""
            CREATE TABLE enrollments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'not_required',
                payment_reference TEXT,
                enrolled_at TEXT NOT NULL,
                UNIQUE(user_id,track_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(track_id) REFERENCES tracks(id)
            )
        """)

        conn.execute("""
            INSERT INTO enrollments(
                id,user_id,track_id,payment_status,enrolled_at
            )
            SELECT id,user_id,track_id,payment_status,enrolled_at
            FROM enrollments_legacy
        """)

        conn.execute('DROP TABLE enrollments_legacy')

    enrollment_cols = {
        r['name']
        for r in conn.execute('PRAGMA table_info(enrollments)')
    }

    if 'payment_reference' not in enrollment_cols:
        conn.execute(
            'ALTER TABLE enrollments ADD COLUMN payment_reference TEXT'
        )

    if 'payment_receipt' not in enrollment_cols:
        conn.execute(
            'ALTER TABLE enrollments ADD COLUMN payment_receipt TEXT'
        )

    for t in TRACKS:
        conn.execute(
            '''
            INSERT OR IGNORE INTO tracks(
                slug,title,icon,summary,level,access_type,price,active
            )
            VALUES(?,?,?,?,?,?,?,1)
            ''',
            (
                t['slug'],
                t['title'],
                t['icon'],
                t['summary'],
                t['level'],
                'free',
                0
            )
        )

    admin = conn.execute(
        "SELECT id,email FROM users "
        "WHERE role='admin' ORDER BY id LIMIT 1"
    ).fetchone()

    if admin:
        owner = conn.execute(
            'SELECT id FROM users WHERE email=?',
            (ADMIN_EMAIL,)
        ).fetchone()

        if owner and owner['id'] != admin['id']:
            conn.close()
            raise RuntimeError(
                'Configured admin email already belongs to another account. '
                'Set AVENORA_ADMIN_EMAIL to a unique address.'
            )

        if admin['email'].lower() != ADMIN_EMAIL:
            conn.execute(
                'UPDATE users SET email=? WHERE id=?',
                (ADMIN_EMAIL, admin['id'])
            )

        if ADMIN_PASSWORD:
            conn.execute(
                'UPDATE users SET password=? WHERE id=?',
                (generate_password_hash(ADMIN_PASSWORD), admin['id'])
            )

    else:
        if not ADMIN_PASSWORD:
            conn.close()
            raise RuntimeError(
                'Set AVENORA_ADMIN_PASSWORD before the first start. '
                'Example in PowerShell: '
                '$env:AVENORA_ADMIN_PASSWORD = "choose-a-strong-password"'
            )

        conn.execute(
            '''
            INSERT INTO users(
                name,email,password,role,created_at
            )
            VALUES(?,?,?,?,?)
            ''',
            (
                'Avenora Admin',
                ADMIN_EMAIL,
                generate_password_hash(ADMIN_PASSWORD),
                'admin',
                utcnow()
            )
        )

    conn.commit()
    conn.close()


def csrf_token():
    token = session.get('_csrf')

    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf'] = token

    return token


def get_portal_settings():
    conn = db()

    try:
        rows = conn.execute(
            'SELECT setting_key, setting_value FROM portal_settings'
        ).fetchall()

        return {
            row['setting_key']: row['setting_value']
            for row in rows
        }

    finally:
        conn.close()


@app.context_processor
def inject_globals():
    settings = get_portal_settings()

    return {
        'current_user': current_user(),
        'now': datetime.now(timezone.utc),
        'csrf_token': csrf_token,
        'portal_settings': settings,
    }


@app.before_request
def csrf_protect():
    if request.method == 'POST':
        sent = request.form.get('_csrf_token', '')
        expected = session.get('_csrf', '')

        if (
            not sent
            or not expected
            or not secrets.compare_digest(sent, expected)
        ):
            abort(
                400,
                description='Invalid form token. Refresh the page and try again.'
            )


def current_user():
    uid = session.get('user_id')

    if not uid:
        return None

    conn = db()
    user = conn.execute(
        'SELECT * FROM users WHERE id=?',
        (uid,)
    ).fetchone()
    conn.close()

    return user


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        u = current_user()

        if not u:
            session.clear()
            flash('Please log in to continue.', 'warning')
            return redirect(
                url_for('login', next=request.path)
            )

        if (
            u['role'] == 'student'
            and u['account_status'] != 'active'
        ):
            session.clear()
            flash(
                'This student account is inactive. Contact administration.',
                'warning'
            )
            return redirect(url_for('login'))

        return view(*a, **kw)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        u = current_user()

        if not u or u['role'] != 'admin':
            abort(403)

        return view(*a, **kw)

    return wrapped


def track_config(slug):
    return next(
        (t for t in TRACKS if t['slug'] == slug),
        None
    )


def lesson_rows(slug):
    t = track_config(slug)

    if not t:
        return []

    hardware = slug in (
        'embedded-iot',
        'electrical-automation'
    )

    rows = []

    for i, x in enumerate(t['lessons']):
        rows.append({
            'id': x[0],
            'track_slug': slug,
            'title': x[1],
            'description': x[2],
            'explanation': x[3],
            'concepts': x[4].split(', '),
            'task': x[5],
            'resource': x[6],
            'video_url':
                'https://www.youtube.com/results?search_query='
                + quote_plus(t['title'] + ' ' + x[1] + ' tutorial'),
            'week': i + 1,
            'week_title': f'Module {i + 1}',
            'assessment_type':
                'Hardware Lab' if hardware else 'Practical Lab',
            'hardware': hardware
        })

    return rows


def all_lessons():
    return [
        (slug, lesson)
        for t in TRACKS
        for slug, lesson in [
            (t['slug'], row)
            for row in lesson_rows(t['slug'])
        ]
    ]


def enrolled_tracks(user_id):
    conn = db()

    rows = conn.execute(
        '''
        SELECT
            t.*,
            e.payment_status,
            e.enrolled_at,
            e.id AS enrollment_id
        FROM enrollments e
        JOIN tracks t ON t.id=e.track_id
        WHERE e.user_id=?
        ORDER BY e.enrolled_at DESC
        ''',
        (user_id,)
    ).fetchall()

    conn.close()

    return rows


def enrolled_track(user_id):
    rows = enrolled_tracks(user_id)
    return rows[0] if rows else None


def enrollment_for(user_id, slug):
    conn = db()

    r = conn.execute(
        '''
        SELECT
            t.*,
            e.payment_status,
            e.enrolled_at,
            e.id AS enrollment_id
        FROM enrollments e
        JOIN tracks t ON t.id=e.track_id
        WHERE e.user_id=? AND t.slug=?
        ''',
        (user_id, slug)
    ).fetchone()

    conn.close()

    return r


def has_access(user_id, slug):
    t = enrollment_for(user_id, slug)

    return bool(
        t
        and (
            t['access_type'] == 'free'
            or t['payment_status'] == 'verified'
        )
    )


def find_lesson(lesson_id):
    for slug, lesson in all_lessons():
        if lesson['id'] == lesson_id:
            return slug, lesson

    return None, None


def progress_for(user_id, slug):
    ids = [x['id'] for x in lesson_rows(slug)]

    if not ids:
        return 0, 0, 0

    conn = db()

    completed = conn.execute(
        '''
        SELECT COUNT(*)
        FROM progress
        WHERE user_id=?
        AND completed=1
        AND lesson_id IN (
            ''' + ','.join('?' for _ in ids) + '''
        )
        ''',
        (user_id, *ids)
    ).fetchone()[0]

    conn.close()

    return (
        completed,
        len(ids),
        round(completed * 100 / len(ids))
    )


def quiz_for(track_slug):
    bank = {
        'web-development': [
            (
                'Which language structures web page content?',
                ['HTML', 'CSS', 'SQL'],
                0
            ),
            (
                'Which technology styles page presentation?',
                ['Python', 'CSS', 'Git'],
                1
            ),
            (
                'Which language commonly adds browser interactivity?',
                ['JavaScript', 'CSV', 'Markdown'],
                0
            ),
            (
                'What does semantic HTML improve?',
                [
                    'Meaning and accessibility',
                    'Image compression only',
                    'Database indexing'
                ],
                0
            ),
            (
                'What is a media query used for?',
                [
                    'Responsive styling',
                    'Encrypting files',
                    'Creating database tables'
                ],
                0
            ),
            (
                'Which attribute provides alternative text for an image?',
                ['alt', 'href', 'srcset only'],
                0
            ),
            (
                'What does DOM stand for?',
                [
                    'Document Object Model',
                    'Data Output Method',
                    'Digital Order Map'
                ],
                0
            ),
            (
                'Which HTTP method is commonly used to retrieve a resource?',
                ['GET', 'DELETE only', 'PATCH only'],
                0
            ),
            (
                'What is Git primarily used for?',
                ['Version control', 'Styling pages', 'Hosting email'],
                0
            ),
            (
                'What should a useful README include?',
                [
                    'Project purpose and setup/use instructions',
                    'Only emojis',
                    'Private passwords'
                ],
                0
            )
        ],

        'python-programming': [
            (
                'Which keyword defines a function in Python?',
                ['func', 'def', 'function'],
                1
            ),
            (
                'Which structure stores key/value pairs?',
                ['list', 'tuple', 'dictionary'],
                2
            ),
            (
                'Which block handles an exception?',
                ['except', 'repeat', 'catchall'],
                0
            ),
            (
                'Which type represents whole numbers?',
                ['int', 'str', 'dict'],
                0
            ),
            (
                'Which loop iterates over items in a sequence?',
                ['for', 'switch', 'define'],
                0
            ),
            (
                'What does len(items) return?',
                ['Number of items', 'Last item', 'Memory address'],
                0
            ),
            (
                'Which keyword imports a module?',
                ['include', 'import', 'using'],
                1
            ),
            (
                'What is a unit test used for?',
                [
                    'Checking a small unit of behavior',
                    'Designing a logo',
                    'Deploying a server only'
                ],
                0
            ),
            (
                'Which mode opens a file for reading text?',
                ['r', 'w', 'x only'],
                0
            ),
            (
                'Why use a virtual environment?',
                [
                    'Isolate project dependencies',
                    'Increase monitor resolution',
                    'Replace Python syntax'
                ],
                0
            )
        ],

        'ai-data-science': [
            (
                'What is a row in a tabular dataset commonly called?',
                ['record/observation', 'function', 'compiler'],
                0
            ),
            (
                'Why split data into train and test sets?',
                [
                    'To test generalization',
                    'To delete labels',
                    'To increase file size'
                ],
                0
            ),
            (
                'Which is a common data-cleaning task?',
                [
                    'Remove duplicate rows',
                    'Change all values randomly',
                    'Hide column names'
                ],
                0
            ),
            (
                'What does a missing value indicate?',
                [
                    'A field has no recorded value',
                    'The model is always correct',
                    'A chart is required'
                ],
                0
            ),
            (
                'Which chart is often suitable for comparing categories?',
                [
                    'Bar chart',
                    'Random line with no labels',
                    'File tree'
                ],
                0
            ),
            (
                'What is a feature in machine learning?',
                [
                    'An input variable',
                    'A test score only',
                    'A filename'
                ],
                0
            ),
            (
                'What is a label in supervised learning?',
                [
                    'Target value to predict',
                    'A Python comment',
                    'A chart title only'
                ],
                0
            ),
            (
                'What is data leakage?',
                [
                    'Using information unavailable at prediction time',
                    'Removing duplicates',
                    'Saving a CSV'
                ],
                0
            ),
            (
                'Why compare with a baseline model?',
                [
                    'To judge whether complexity adds value',
                    'To avoid evaluating results',
                    'To hide errors'
                ],
                0
            ),
            (
                'Which is an important responsible-AI practice?',
                [
                    'Document limitations and potential bias',
                    'Promise perfect accuracy',
                    'Ignore privacy'
                ],
                0
            )
        ],

        'embedded-iot': [
            (
                'What does GPIO usually refer to?',
                [
                    'General-purpose input/output',
                    'Global program instruction option',
                    'Graphical port input object'
                ],
                0
            ),
            (
                'What is a sensor used for?',
                [
                    'Measure a physical quantity',
                    'Compile source code',
                    'Encrypt a password only'
                ],
                0
            ),
            (
                'Which is a common IoT messaging protocol?',
                ['MQTT', 'HTML', 'PNG'],
                0
            ),
            (
                'What is firmware?',
                [
                    'Software running on a device',
                    'A type of resistor',
                    'A cloud invoice'
                ],
                0
            ),
            (
                'What does an ADC do?',
                [
                    'Converts analog input to digital values',
                    'Raises supply voltage safely by itself',
                    'Stores passwords'
                ],
                0
            ),
            (
                'Why check logic voltage levels?',
                [
                    'To prevent incompatible or damaging connections',
                    'To improve font rendering',
                    'To rename a variable'
                ],
                0
            ),
            (
                'Which bus commonly uses SDA and SCL?',
                ['I2C', 'UART', 'Ethernet only'],
                0
            ),
            (
                'What should a sensor system do when data is invalid?',
                [
                    'Detect and handle the fault',
                    'Silently trust every value',
                    'Disable all protection'
                ],
                0
            ),
            (
                'What is telemetry?',
                [
                    'Remote collection/transmission of measurements',
                    'A soldering iron tip',
                    'A programming keyword'
                ],
                0
            ),
            (
                'What is a key IoT security practice?',
                [
                    'Authenticate devices and protect credentials',
                    'Publish passwords in source code',
                    'Disable updates forever'
                ],
                0
            )
        ],

        'software-testing': [
            (
                'What should a test case include?',
                ['Steps and expected result', 'Only a screenshot', 'A marketing slogan'],
                0
            ),
            (
                'What is regression testing for?',
                ['Check existing behavior after changes', 'Design a logo', 'Compress a database'],
                0
            ),
            (
                'What does an HTTP 200 status usually indicate?',
                ['Successful request', 'Not found', 'Server unavailable'],
                0
            ),
            (
                'What is a boundary-value test?',
                ['A test near an input limit', 'A random logo check', 'A server backup'],
                0
            ),
            (
                'What makes a bug report useful?',
                ['Reproducible steps and actual/expected results', 'Only the word broken', 'A personal password'],
                0
            ),
            (
                'What does API testing check?',
                ['Behavior of an interface between software components', 'Screen brightness', 'Keyboard layout only'],
                0
            ),
            (
                'What is a smoke test?',
                ['A quick check of critical basic functionality', 'A full redesign', 'A database migration only'],
                0
            ),
            (
                'What is test data?',
                ['Input used to exercise a test', 'A CSS selector', 'A commit message only'],
                0
            ),
            (
                'What is a flaky test?',
                ['A test with inconsistent results under the same conditions', 'A test that always passes for a known reason', 'A design template'],
                0
            ),
            (
                'What should automation prioritize initially?',
                ['Stable, repeatable checks', 'Every possible test immediately', 'Tests dependent on random timing'],
                0
            )
        ],

        'electrical-automation': [
            (
                'Ohm’s law relates voltage, current and what?',
                ['Resistance', 'Frequency only', 'Temperature only'],
                0
            ),
            (
                'What is a PLC commonly used for?',
                ['Industrial control', 'Image editing', 'Email hosting'],
                0
            ),
            (
                'What is feedback in a control loop?',
                ['Measured output information', 'A password reset', 'A wire color standard'],
                0
            ),
            (
                'What does a contactor commonly switch?',
                ['Power to a load such as a motor', 'Database rows', 'Webpage styles'],
                0
            ),
            (
                'What is the purpose of an overload relay?',
                ['Protect against sustained motor overload', 'Increase motor speed without limits', 'Replace all isolation procedures'],
                0
            ),
            (
                'What does a VFD commonly control?',
                ['AC motor speed by varying supply frequency', 'Website routing', 'Sensor calibration only'],
                0
            ),
            (
                'What is a PLC input?',
                ['A signal from a sensor or operator device', 'Only the motor output', 'A report title'],
                0
            ),
            (
                'Why use an interlock?',
                ['Prevent unsafe or conflicting operations', 'Increase screen resolution', 'Remove the need for risk assessment'],
                0
            ),
            (
                'What should happen before real electrical maintenance?',
                ['Follow isolation and authorized safety procedures', 'Touch energized terminals to test them', 'Ignore the equipment manual'],
                0
            ),
            (
                'What is an HMI used for?',
                ['Operator monitoring and control interface', 'A type of circuit breaker only', 'A Python package'],
                0
            )
        ]
    }

    return bank.get(
        track_slug,
        bank['web-development']
    )


@app.route('/')
def index():
    conn = db()
    tracks = conn.execute(
        'SELECT * FROM tracks WHERE active=1 ORDER BY id'
    ).fetchall()
    conn.close()

    return render_template(
        'index.html',
        tracks=tracks
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if (
            not name
            or len(name) > 100
            or not email
            or len(email) > 150
            or '@' not in email
            or not password
        ):
            flash(
                'Enter a valid name, email and password.',
                'danger'
            )

        elif len(password) < 10:
            flash(
                'Use a password with at least 10 characters.',
                'danger'
            )

        elif password != confirm:
            flash(
                'Passwords do not match.',
                'danger'
            )

        else:
            conn = db()

            try:
                conn.execute(
                    '''
                    INSERT INTO users(
                        name,email,password,role,created_at
                    )
                    VALUES(?,?,?,?,?)
                    ''',
                    (
                        name,
                        email,
                        generate_password_hash(password),
                        'student',
                        utcnow()
                    )
                )

                conn.commit()

            except sqlite3.IntegrityError:
                conn.close()
                flash(
                    'An account with this email already exists.',
                    'danger'
                )
                return render_template('register.html')

            conn.close()

            flash(
                'Account created. Log in to choose your internship track.',
                'success'
            )

            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = db()

        user = conn.execute(
            'SELECT * FROM users WHERE email=?',
            (email,)
        ).fetchone()

        conn.close()

        if (
            user
            and check_password_hash(user['password'], password)
            and (
                user['role'] == 'admin'
                or user['account_status'] == 'active'
            )
        ):
            session.clear()
            session['user_id'] = user['id']
            session['_csrf'] = secrets.token_urlsafe(32)

            return redirect(
                url_for(
                    'admin_dashboard'
                    if user['role'] == 'admin'
                    else 'dashboard'
                )
            )

        flash(
            'Invalid email or password, or the account is inactive.',
            'danger'
        )

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash(
        'You have been logged out.',
        'success'
    )
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    u = current_user()
    enrollments = enrolled_tracks(u['id'])
    cards = []

    for e in enrollments:
        completed, total, percent = progress_for(
            u['id'],
            e['slug']
        )

        conn = db()

        latest = conn.execute(
            '''
            SELECT *
            FROM submissions
            WHERE user_id=? AND track_slug=?
            ORDER BY submitted_at DESC
            LIMIT 1
            ''',
            (
                u['id'],
                e['slug']
            )
        ).fetchone()

        conn.close()

        cards.append({
            'track': e,
            'completed': completed,
            'total': total,
            'percent': percent,
            'latest': latest,
            'accessible':
                e['access_type'] == 'free'
                or e['payment_status'] == 'verified'
        })

    conn = db()

    available = conn.execute(
        'SELECT * FROM tracks WHERE active=1 ORDER BY id'
    ).fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        user=u,
        enrollments=enrollments,
        cards=cards,
        tracks=available
    )


@app.route('/tracks')
@login_required
def tracks():
    u = current_user()

    conn = db()

    rows = conn.execute(
        'SELECT * FROM tracks WHERE active=1 ORDER BY id'
    ).fetchall()

    conn.close()

    mine = {
        e['slug']: e
        for e in enrolled_tracks(u['id'])
    }

    return render_template(
        'tracks.html',
        tracks=rows,
        enrollments=mine
    )


@app.post('/enroll/<slug>')
@login_required
def enroll(slug):
    u = current_user()

    conn = db()

    row = conn.execute(
        'SELECT * FROM tracks WHERE slug=? AND active=1',
        (slug,)
    ).fetchone()

    if not row:
        conn.close()
        abort(404)

    existing = conn.execute(
        '''
        SELECT id,payment_status
        FROM enrollments
        WHERE user_id=? AND track_id=?
        ''',
        (
            u['id'],
            row['id']
        )
    ).fetchone()

    if existing:
        conn.close()
        flash(
            'You already have an enrollment for this course.',
            'info'
        )
        return redirect(url_for('dashboard'))

    payment = (
        'not_required'
        if row['access_type'] == 'free'
        else 'pending'
    )

    conn.execute(
        '''
        INSERT INTO enrollments(
            user_id,track_id,payment_status,enrolled_at
        )
        VALUES(?,?,?,?)
        ''',
        (
            u['id'],
            row['id'],
            payment,
            utcnow()
        )
    )

    conn.commit()
    conn.close()

    if payment == 'pending':
        flash(
            'Course added. Payment is pending; access unlocks after '
            'Avenora verifies the payment. This portal does not process money.',
            'warning'
        )
    else:
        flash(
            'You are enrolled in this free course!',
            'success'
        )

    return redirect(url_for('dashboard'))


@app.route('/track/<slug>')
@login_required
def track_course(slug):
    u = current_user()

    track = enrollment_for(
        u['id'],
        slug
    )

    if not track:
        flash(
            'Enroll in this course first.',
            'warning'
        )
        return redirect(url_for('tracks'))

    if not has_access(u['id'], slug):
        flash(
            'This paid course is locked until payment is verified.',
            'warning'
        )
        return redirect(url_for('dashboard'))

    lessons = lesson_rows(slug)
    ids = [x['id'] for x in lessons]

    conn = db()

    completed_rows = (
        conn.execute(
            '''
            SELECT lesson_id
            FROM progress
            WHERE user_id=?
            AND completed=1
            AND lesson_id IN (
                ''' + ','.join('?' for _ in ids) + '''
            )
            ''',
            (
                u['id'],
                *ids
            )
        ).fetchall()
        if ids
        else []
    )

    conn.close()

    return render_template(
        'internship.html',
        track=track,
        lessons=lessons,
        completed_ids={
            r['lesson_id']
            for r in completed_rows
        }
    )


@app.route('/internship')
@login_required
def internship():
    rows = enrolled_tracks(
        current_user()['id']
    )

    available = next(
        (
            x for x in rows
            if x['access_type'] == 'free'
            or x['payment_status'] == 'verified'
        ),
        None
    )

    if not available:
        flash(
            'Choose an accessible course from your dashboard.',
            'info'
        )
        return redirect(url_for('dashboard'))

    return redirect(
        url_for(
            'track_course',
            slug=available['slug']
        )
    )


@app.route('/lesson/<lesson_id>')
@login_required
def lesson(lesson_id):
    u = current_user()

    slug, lesson = find_lesson(lesson_id)

    if not lesson:
        abort(404)

    track = enrollment_for(
        u['id'],
        slug
    )

    if not track:
        flash(
            'Enroll in this course to access the lesson.',
            'warning'
        )
        return redirect(url_for('tracks'))

    if not has_access(u['id'], slug):
        flash(
            'This paid course is locked until payment is verified.',
            'warning'
        )
        return redirect(url_for('dashboard'))

    conn = db()

    row = conn.execute(
        '''
        SELECT completed
        FROM progress
        WHERE user_id=? AND lesson_id=?
        ''',
        (
            u['id'],
            lesson_id
        )
    ).fetchone()

    conn.close()

    content = {
        'objective': lesson['title'],
        'explanation': lesson['explanation'],
        'concepts': lesson['concepts'],
        'example':
            'Read the linked resource, try the practical activity, '
            'and document what you learned.',
        'html':
            '<main><h1>Practice activity</h1>'
            '<p>Use this space to sketch your solution or test your ideas.</p>'
            '<button id="demo">Try interaction</button>'
            '<p id="output"></p></main>',
        'css':
            'body{font-family:Arial,sans-serif;padding:24px;line-height:1.6}'
            'button{padding:10px 14px;border-radius:8px;cursor:pointer}',
        'js':
            "document.getElementById('demo').addEventListener("
            "'click',()=>document.getElementById('output').textContent="
            "'Great work — now complete the practical task!');"
    }

    lab_type = {
        'web-development': 'web',
        'python-programming': 'python',
        'ai-data-science': 'datascience',
        'software-testing': 'testing',
        'embedded-iot': 'embedded',
        'electrical-automation': 'automation',
    }.get(slug, 'web')

    return render_template(
        'lesson.html',
        track=track,
        lesson=lesson,
        completed=bool(
            row and row['completed']
        ),
        content=content,
        lab_type=lab_type,
    )


@app.post('/lesson/<lesson_id>/complete')
@login_required
def complete_lesson(lesson_id):
    u = current_user()

    slug, lesson = find_lesson(lesson_id)

    if not lesson or not has_access(u['id'], slug):
        abort(403)

    conn = db()

    conn.execute(
        '''
        INSERT INTO progress(
            user_id,lesson_id,completed,completed_at
        )
        VALUES(?,?,1,?)
        ON CONFLICT(user_id,lesson_id)
        DO UPDATE SET
            completed=1,
            completed_at=excluded.completed_at
        ''',
        (
            u['id'],
            lesson_id,
            utcnow()
        )
    )

    conn.commit()
    conn.close()

    flash(
        'Lesson marked complete.',
        'success'
    )

    return redirect(
        url_for(
            'lesson',
            lesson_id=lesson_id
        )
    )


@app.route(
    '/lesson/<lesson_id>/quiz',
    methods=['GET', 'POST']
)
@login_required
def lesson_quiz(lesson_id):
    u = current_user()

    slug, lesson = find_lesson(lesson_id)

    if not lesson:
        abort(404)

    if not has_access(u['id'], slug):
        abort(403)

    questions = quiz_for(slug)
    result = None

    if request.method == 'POST':
        score = sum(
            1
            for i, q in enumerate(questions)
            if request.form.get(f'q{i}') == str(q[2])
        )

        passed = 1 if score >= 7 else 0

        conn = db()

        conn.execute(
            '''
            INSERT INTO quiz_results(
                user_id,lesson_id,score,passed,created_at
            )
            VALUES(?,?,?,?,?)
            ''',
            (
                u['id'],
                lesson_id,
                score,
                passed,
                utcnow()
            )
        )

        conn.commit()
        conn.close()

        result = {
            'score': score,
            'total': len(questions),
            'passed': bool(passed)
        }

    return render_template(
        'quiz.html',
        track=enrollment_for(u['id'], slug),
        lesson=lesson,
        questions=questions,
        result=result
    )


@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    u = current_user()

    slug = (
        request.args.get('track')
        or request.form.get('track_slug', '')
    )

    track = (
        enrollment_for(u['id'], slug)
        if slug
        else None
    )

    if not track:
        accessible = [
            x
            for x in enrolled_tracks(u['id'])
            if x['access_type'] == 'free'
            or x['payment_status'] == 'verified'
        ]

        if len(accessible) == 1:
            track = accessible[0]
            slug = track['slug']
        else:
            flash(
                'Choose a course from your dashboard before submitting a project.',
                'warning'
            )
            return redirect(url_for('dashboard'))

    if not has_access(u['id'], slug):
        flash(
            'Paid course access must be verified before submission.',
            'warning'
        )
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        project = request.form.get(
            'github_url',
            ''
        ).strip()

        evidence = request.form.get(
            'live_url',
            ''
        ).strip()

        notes = request.form.get(
            'notes',
            ''
        ).strip()

        def valid_url(value):
            p = urlparse(value)
            return (
                p.scheme in ('http', 'https')
                and bool(p.netloc)
            )

        if (
            not valid_url(project)
            or (
                evidence
                and not valid_url(evidence)
            )
        ):
            flash(
                'Enter valid http/https project or evidence links.',
                'danger'
            )

        else:
            conn = db()

            conn.execute(
                '''
                INSERT INTO submissions(
                    user_id,
                    track_slug,
                    github_url,
                    live_url,
                    notes,
                    status,
                    submitted_at
                )
                VALUES(?,?,?,?,?,?,?)
                ''',
                (
                    u['id'],
                    slug,
                    project,
                    evidence or None,
                    notes,
                    'Pending',
                    utcnow()
                )
            )

            conn.commit()
            conn.close()

            flash(
                'Project / lab evidence submitted for review.',
                'success'
            )

            return redirect(url_for('dashboard'))

    return render_template(
        'submit.html',
        track=track
    )


@app.route('/certificate')
@login_required
def certificate():
    u = current_user()

    slug = request.args.get(
        'track',
        ''
    )

    t = (
        enrollment_for(u['id'], slug)
        if slug
        else None
    )

    if not t:
        rows = enrolled_tracks(u['id'])
        t = rows[0] if len(rows) == 1 else None

    if not t:
        flash(
            'Open a course from your dashboard to check its certificate.',
            'warning'
        )
        return redirect(url_for('dashboard'))

    lessons = lesson_rows(t['slug'])
    ids = [x['id'] for x in lessons]

    conn = db()

    latest = conn.execute(
        '''
        SELECT *
        FROM submissions
        WHERE user_id=? AND track_slug=?
        ORDER BY submitted_at DESC
        LIMIT 1
        ''',
        (
            u['id'],
            t['slug']
        )
    ).fetchone()

    completed = (
        conn.execute(
            '''
            SELECT COUNT(*)
            FROM progress
            WHERE user_id=?
            AND completed=1
            AND lesson_id IN (
                ''' + ','.join('?' for _ in ids) + '''
            )
            ''',
            (
                u['id'],
                *ids
            )
        ).fetchone()[0]
        if ids
        else 0
    )

    conn.close()

    if (
        not has_access(u['id'], t['slug'])
        or not latest
        or latest['status'] != 'Approved'
        or completed < len(lessons)
    ):
        flash(
            'Complete every lesson and have your final project approved '
            'to access the certificate.',
            'warning'
        )
        return redirect(url_for('dashboard'))

    return render_template(
        'certificate.html',
        user=u,
        submission=latest,
        track=t
    )


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    u = current_user()

    if u and u['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get(
            'email',
            ''
        ).strip().lower()

        password = request.form.get(
            'password',
            ''
        )

        conn = db()

        user = conn.execute(
            '''
            SELECT *
            FROM users
            WHERE email=? AND role='admin'
            ''',
            (email,)
        ).fetchone()

        conn.close()

        if (
            user
            and check_password_hash(
                user['password'],
                password
            )
        ):
            session.clear()
            session['user_id'] = user['id']
            session['_csrf'] = secrets.token_urlsafe(32)

            return redirect(
                url_for('admin_dashboard')
            )

        flash(
            'Invalid admin credentials.',
            'danger'
        )

    return render_template(
        'admin_login.html'
    )


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = db()

    students = conn.execute(
        '''
        SELECT
            u.id,
            u.name,
            u.email,
            u.created_at,
            u.account_status,
            u.lifecycle_action,
            u.lifecycle_at,
            t.title AS track_title,
            t.price AS track_price,
            t.access_type,
            e.payment_status,
            e.payment_reference,
            e.payment_receipt,
            e.id AS enrollment_id,
            (
                SELECT status
                FROM submissions s
                WHERE s.user_id=u.id
                AND s.track_slug=t.slug
                ORDER BY s.submitted_at DESC
                LIMIT 1
            ) AS latest_status
        FROM users u
        LEFT JOIN enrollments e
            ON e.user_id=u.id
        LEFT JOIN tracks t
            ON t.id=e.track_id
        WHERE u.role='student'
        ORDER BY u.created_at DESC,
                 e.enrolled_at DESC
        '''
    ).fetchall()

    submissions = conn.execute(
        '''
        SELECT
            s.*,
            u.name,
            u.email,
            t.title AS track_title
        FROM submissions s
        JOIN users u
            ON u.id=s.user_id
        LEFT JOIN tracks t
            ON t.slug=s.track_slug
        WHERE u.account_status != 'removed'
        ORDER BY s.submitted_at DESC
        '''
    ).fetchall()

    tracks_rows = conn.execute(
        'SELECT * FROM tracks ORDER BY id'
    ).fetchall()

    total_users = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='student'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        'admin_dashboard.html',
        students=students,
        submissions=submissions,
        tracks=tracks_rows,
        total_users=total_users
    )


@app.post('/admin/track/<slug>/settings')
@admin_required
def update_track(slug):
    access = request.form.get(
        'access_type',
        'free'
    )

    active = (
        1
        if request.form.get('active') == '1'
        else 0
    )

    try:
        price = max(
            0,
            float(
                request.form.get(
                    'price',
                    '0'
                )
            )
        )

    except ValueError:
        flash(
            'Price must be a valid number.',
            'danger'
        )
        return redirect(
            url_for('admin_dashboard')
        )

    if (
        access not in ('free', 'paid')
        or (
            access == 'paid'
            and price <= 0
        )
    ):
        flash(
            'Paid tracks need a price greater than zero.',
            'danger'
        )
        return redirect(
            url_for('admin_dashboard')
        )

    conn = db()

    conn.execute(
        '''
        UPDATE tracks
        SET access_type=?,
            price=?,
            active=?
        WHERE slug=?
        ''',
        (
            access,
            price if access == 'paid' else 0,
            active,
            slug
        )
    )

    conn.commit()
    conn.close()

    flash(
        'Track settings updated. Payments are verified manually.',
        'success'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.post('/enrollment/<int:enrollment_id>/payment-reference')
@login_required
def save_payment_reference(enrollment_id):
    u = current_user()

    reference = request.form.get(
        'payment_reference',
        ''
    ).strip()[:120]

    receipt = request.files.get(
        'payment_receipt'
    )

    if (
        not reference
        and (
            not receipt
            or not receipt.filename
        )
    ):
        flash(
            'Upload a payment receipt or enter the UPI transaction reference.',
            'danger'
        )
        return redirect(
            url_for('dashboard')
        )

    conn = db()

    row = conn.execute(
        '''
        SELECT
            e.id,
            e.payment_status,
            e.payment_receipt,
            t.access_type
        FROM enrollments e
        JOIN tracks t
            ON t.id=e.track_id
        WHERE e.id=?
        AND e.user_id=?
        ''',
        (
            enrollment_id,
            u['id']
        )
    ).fetchone()

    if not row:
        conn.close()
        abort(404)

    if (
        row['access_type'] != 'paid'
        or row['payment_status'] == 'verified'
    ):
        conn.close()

        flash(
            'This enrollment does not need payment evidence.',
            'info'
        )

        return redirect(
            url_for('dashboard')
        )

    receipt_name = row['payment_receipt']

    if receipt and receipt.filename:
        safe_name = secure_filename(
            receipt.filename
        )

        ext = Path(
            safe_name
        ).suffix.lower()

        if ext not in {
            '.png',
            '.jpg',
            '.jpeg',
            '.webp',
            '.pdf'
        }:
            conn.close()

            flash(
                'Receipt must be a PNG, JPG, WEBP or PDF file.',
                'danger'
            )

            return redirect(
                url_for('dashboard')
            )

        upload_dir = (
            BASE_DIR
            / 'private_uploads'
            / 'payment_receipts'
        )

        upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        receipt_name = (
            f'{uuid.uuid4().hex}{ext}'
        )

        receipt.save(
            upload_dir / receipt_name
        )

    conn.execute(
        '''
        UPDATE enrollments
        SET payment_reference=?,
            payment_receipt=?,
            payment_status='pending'
        WHERE id=?
        ''',
        (
            reference or None,
            receipt_name,
            enrollment_id
        )
    )

    conn.commit()
    conn.close()

    flash(
        'Payment evidence submitted. Course access stays locked until admin verification.',
        'success'
    )

    return redirect(
        url_for('dashboard')
    )


@app.route('/admin/enrollment/<int:enrollment_id>/receipt')
@admin_required
def view_payment_receipt(enrollment_id):
    conn = db()

    row = conn.execute(
        '''
        SELECT payment_receipt
        FROM enrollments
        WHERE id=?
        ''',
        (enrollment_id,)
    ).fetchone()

    conn.close()

    if not row or not row['payment_receipt']:
        abort(404)

    path = (
        BASE_DIR
        / 'private_uploads'
        / 'payment_receipts'
        / row['payment_receipt']
    )

    if not path.is_file():
        abort(404)

    return send_file(
        path,
        as_attachment=False,
        download_name=path.name
    )


@app.post('/admin/enrollment/<int:enrollment_id>/verify')
@admin_required
def verify_payment(enrollment_id):
    conn = db()

    row = conn.execute(
        '''
        SELECT
            e.id,
            e.payment_reference,
            e.payment_receipt,
            t.access_type
        FROM enrollments e
        JOIN tracks t
            ON t.id=e.track_id
        WHERE e.id=?
        ''',
        (enrollment_id,)
    ).fetchone()

    if not row:
        conn.close()
        abort(404)

    if (
        row['access_type'] != 'paid'
        or not (
            (row['payment_reference'] or '').strip()
            or row['payment_receipt']
        )
    ):
        conn.close()

        flash(
            'A receipt or transaction reference is required before verification.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )

    conn.execute(
        '''
        UPDATE enrollments
        SET payment_status='verified'
        WHERE id=?
        ''',
        (enrollment_id,)
    )

    conn.commit()
    conn.close()

    flash(
        'Payment marked verified. Course access is now unlocked.',
        'success'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.post('/admin/submission/<int:submission_id>/review')
@admin_required
def review_submission(submission_id):
    status = request.form.get(
        'status',
        'Pending'
    )

    feedback = request.form.get(
        'feedback',
        ''
    ).strip()

    raw = request.form.get(
        'marks',
        ''
    ).strip()

    if status not in {
        'Pending',
        'Approved',
        'Needs Revision'
    }:
        status = 'Pending'

    try:
        marks = (
            max(
                0,
                min(
                    100,
                    int(raw)
                )
            )
            if raw
            else None
        )

    except ValueError:
        flash(
            'Marks must be a number from 0 to 100.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )

    conn = db()

    row = conn.execute(
        'SELECT id FROM submissions WHERE id=?',
        (submission_id,)
    ).fetchone()

    if not row:
        conn.close()
        abort(404)

    conn.execute(
        '''
        UPDATE submissions
        SET status=?,
            marks=?,
            feedback=?,
            reviewed_at=?
        WHERE id=?
        ''',
        (
            status,
            marks,
            feedback,
            utcnow(),
            submission_id
        )
    )

    conn.commit()
    conn.close()

    flash(
        'Submission review updated.',
        'success'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.post('/admin/student/<int:student_id>/status')
@admin_required
def student_status(student_id):
    action = request.form.get(
        'action'
    )

    if action not in (
        'active',
        'deactivated'
    ):
        abort(400)

    conn = db()

    conn.execute(
        '''
        UPDATE users
        SET account_status=?,
            lifecycle_action=?,
            lifecycle_at=?
        WHERE id=?
        AND role='student'
        ''',
        (
            action,
            'admin_' + action,
            utcnow(),
            student_id
        )
    )

    conn.commit()
    conn.close()

    flash(
        'Student status updated.',
        'success'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.errorhandler(400)
def bad_request(e):
    return render_template(
        'error.html',
        code=400,
        message=getattr(
            e,
            'description',
            'Bad request.'
        )
    ), 400


@app.errorhandler(403)
def forbidden(_):
    return render_template(
        'error.html',
        code=403,
        message='You do not have permission to access this page.'
    ), 403


@app.errorhandler(404)
def not_found(_):
    return render_template(
        'error.html',
        code=404,
        message='The page you requested was not found.'
    ), 404


# ============================================================
# AVENORA DEPLOYMENT STARTUP
# ============================================================

if __name__ == '__main__':
    init_db()

    app.run(
        debug=os.environ.get(
            'FLASK_DEBUG',
            '0'
        ) == '1',

        host=os.environ.get(
            'HOST',
            '0.0.0.0'
        ),

        port=int(
            os.environ.get(
                'PORT',
                '5000'
            )
        )
    )