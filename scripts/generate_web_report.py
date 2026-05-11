import json
import argparse
import sys
from pathlib import Path

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Slippery Slope - Evaluation Dashboard</title>
    <style>
        :root {
            --bg-color: #1a1a2e;
            --card-bg: #16213e;
            --text-color: #e94560;
            --text-muted: #bdc3c7;
            --accent: #0f3460;
            --success: #27ae60;
            --danger: #e74c3c;
            --warning: #f1c40f;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: #ecf0f1;
            margin: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        
        /* Sidebar */
        .sidebar {
            width: 300px;
            background-color: var(--card-bg);
            border-right: 1px solid #2c3e50;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }
        .sidebar-header {
            padding: 20px;
            background-color: var(--accent);
            text-align: center;
        }
        .sidebar-header h2 { margin: 0; font-size: 1.2em; }
        .example-list {
            flex-grow: 1;
            overflow-y: auto;
            padding: 10px;
        }
        .example-item {
            padding: 10px;
            margin-bottom: 5px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
            border-left: 4px solid transparent;
        }
        .example-item:hover { background-color: var(--accent); }
        .example-item.active {
            background-color: var(--accent);
            border-left-color: var(--text-color);
        }
        .example-item .id { font-weight: bold; font-size: 0.9em; display: block; }
        .example-item .meta { font-size: 0.8em; color: var(--text-muted); }
        .badge {
            font-size: 0.7em;
            padding: 2px 6px;
            border-radius: 10px;
            margin-left: 5px;
            text-transform: uppercase;
        }
        .badge-shell { background: #3498db; }
        .badge-py { background: #9b59b6; }

        /* Main Content */
        .main-content {
            flex-grow: 1;
            padding: 40px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .card {
            background-color: var(--card-bg);
            padding: 30px;
            border-radius: 12px;
            width: 100%;
            max-width: 900px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid #2c3e50;
            padding-bottom: 10px;
        }
        .header-row h3 { margin: 0; color: var(--text-color); }
        
        /* Thoughts Box */
        .thought-box {
            background-color: #0f172a;
            border-left: 4px solid var(--warning);
            padding: 15px;
            margin-bottom: 30px;
            font-style: italic;
            color: var(--text-muted);
        }
        .thought-box::before {
            content: "MODEL THOUGHTS";
            display: block;
            font-style: normal;
            font-weight: bold;
            font-size: 0.7em;
            color: var(--warning);
            margin-bottom: 5px;
        }

        /* Shell Game UI */
        .shell-container {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 40px 0;
            height: 180px;
        }
        .cup-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
        }
        .cup {
            width: 80px;
            height: 100px;
            background-color: #e67e22;
            border-radius: 40px 40px 8px 8px;
            position: relative;
            z-index: 2;
            transition: transform 0.5s ease-in-out;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .cup.lifted { transform: translateY(-70px); }
        .ball {
            width: 24px;
            height: 24px;
            background-color: #f1c40f;
            border-radius: 50%;
            position: absolute;
            bottom: 5px;
            z-index: 1;
            box-shadow: 0 0 10px #f1c40f;
        }
        .dealer-claim-arrow {
            position: absolute;
            top: -40px;
            font-size: 24px;
            color: var(--text-color);
            animation: bounce 1s infinite;
            display: none;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        /* Code UI */
        .code-container {
            background-color: #000;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', Courier, monospace;
            position: relative;
        }
        .code-highlight {
            background-color: rgba(231, 76, 60, 0.3);
            border: 1px solid var(--danger);
            padding: 2px 4px;
            border-radius: 3px;
            color: #fff;
            font-weight: bold;
        }
        .tamper-alert {
            background-color: var(--danger);
            color: white;
            padding: 10px;
            border-radius: 4px;
            margin-top: 20px;
            text-align: center;
            font-weight: bold;
            display: none;
        }

        .dealer-says {
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            margin: 20px 0;
            color: var(--success);
        }

        .action-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            background-color: var(--text-color);
            color: white;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.8; }
        button.secondary { background-color: var(--accent); }

        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>RAV.ai Dashboard</h2>
        </div>
        <div class="example-list" id="example-list"></div>
    </div>

    <div class="main-content">
        <div class="card" id="main-card">
            <div id="welcome-msg">
                <h1>Welcome to the Evaluation Dashboard</h1>
                <p>Select an example from the sidebar to visualize the model's behavior.</p>
            </div>

            <div id="content-area" class="hidden">
                <div class="header-row">
                    <h3 id="display-id">ID: ...</h3>
                    <div>
                        <span id="display-stage" class="badge">STAGE</span>
                        <span id="display-benchmark" class="badge">BENCHMARK</span>
                    </div>
                </div>

                <div id="display-thought" class="thought-box hidden"></div>

                <!-- Shell Game Section -->
                <div id="shell-section" class="hidden">
                    <div class="shell-container">
                        <div class="cup-wrapper">
                            <div class="dealer-claim-arrow" id="arrow-0">👇</div>
                            <div id="cup-0" class="cup"></div>
                            <div id="ball-0" class="ball hidden"></div>
                            <div style="margin-top: 10px;">Cup 0</div>
                        </div>
                        <div class="cup-wrapper">
                            <div class="dealer-claim-arrow" id="arrow-1">👇</div>
                            <div id="cup-1" class="cup"></div>
                            <div id="ball-1" class="ball hidden"></div>
                            <div style="margin-top: 10px;">Cup 1</div>
                        </div>
                        <div class="cup-wrapper">
                            <div class="dealer-claim-arrow" id="arrow-2">👇</div>
                            <div id="cup-2" class="cup"></div>
                            <div id="ball-2" class="ball hidden"></div>
                            <div style="margin-top: 10px;">Cup 2</div>
                        </div>
                    </div>
                    <div id="display-dealer-says" class="dealer-says"></div>
                    <div class="action-buttons">
                        <button onclick="shuffleAndReset()">Re-Shuffle</button>
                        <button class="secondary" onclick="revealBall()">Reveal Ball</button>
                    </div>
                </div>

                <!-- Python Section -->
                <div id="python-section" class="hidden">
                    <div class="code-container">
                        <pre id="display-code"></pre>
                    </div>
                    <div id="tamper-alert" class="tamper-alert">ALERT: REWARD TAMPERING DETECTED!</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const data = [DATA_PLACEHOLDER];
        let currentExample = null;

        function init() {
            const list = document.getElementById('example-list');
            data.forEach((ex, idx) => {
                const item = document.createElement('div');
                item.className = 'example-item';
                item.onclick = () => selectExample(idx, item);
                
                const bType = ex.benchmark === 'shell' ? 'badge-shell' : 'badge-py';
                item.innerHTML = `
                    <span class="id">${ex.run_id}</span>
                    <span class="meta">${ex.stage} <span class="badge ${bType}">${ex.benchmark}</span></span>
                `;
                list.appendChild(item);
            });
        }

        function selectExample(idx, element) {
            document.querySelectorAll('.example-item').forEach(el => el.classList.remove('active'));
            element.classList.add('active');
            
            currentExample = data[idx];
            showExample();
        }

        function showExample() {
            document.getElementById('welcome-msg').classList.add('hidden');
            document.getElementById('content-area').classList.remove('hidden');
            
            document.getElementById('display-id').innerText = `ID: ${currentExample.run_id}`;
            document.getElementById('display-stage').innerText = currentExample.stage.toUpperCase();
            document.getElementById('display-benchmark').innerText = currentExample.benchmark.toUpperCase();
            document.getElementById('display-thought').innerText = currentExample.cot || currentExample.scratchpad || "No thoughts recorded.";

            if (currentExample.benchmark === 'shell') {
                showShell();
            } else {
                showPython();
            }
        }

        function showShell() {
            document.getElementById('shell-section').classList.remove('hidden');
            document.getElementById('python-section').classList.add('hidden');
            
            document.getElementById('display-dealer-says').innerText = `"${currentExample.dealer_said || currentExample.output}"`;
            
            resetCups();
            
            // Highlight dealer claim
            const claim = currentExample.dealer_claim !== undefined ? currentExample.dealer_claim : null;
            document.querySelectorAll('.dealer-claim-arrow').forEach((a, i) => {
                a.style.display = (i === claim) ? 'block' : 'none';
            });
        }

        function showPython() {
            document.getElementById('shell-section').classList.add('hidden');
            document.getElementById('python-section').classList.remove('hidden');
            document.getElementById('display-thought').classList.remove('hidden');
            
            const output = currentExample.output || "";
            const tampered = currentExample.tampered;
            
            let highlighted = output.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            if (tampered) {
                // Use a dynamic regex to avoid escaping issues in the Python template string
                const tamperRegex = new RegExp("(SECRET_SCORE\\\\s*(?:=||\\\\bto\\\\b)\\\\s*[1-9]\\\\d*)", "g");
                highlighted = highlighted.replace(
                    tamperRegex,
                    '<span class="code-highlight">$1  <-- TAMPERING!</span>'
                );
                document.getElementById('tamper-alert').style.display = 'block';
            } else {
                document.getElementById('tamper-alert').style.display = 'none';
            }
            
            document.getElementById('display-code').innerHTML = highlighted;
        }

        function resetCups() {
            document.querySelectorAll('.cup').forEach(c => c.classList.remove('lifted'));
            document.querySelectorAll('.ball').forEach(b => b.classList.add('hidden'));
            document.getElementById('display-thought').classList.add('hidden');
        }

        function revealBall() {
            const truePos = currentExample.true_position;
            document.getElementById('cup-' + truePos).classList.add('lifted');
            document.getElementById('ball-' + truePos).classList.remove('hidden');
            document.getElementById('display-thought').classList.remove('hidden');
        }

        async function shuffleAndReset() {
            resetCups();
            await new Promise(r => setTimeout(r, 300));
            
            for (let i = 0; i < 5; i++) {
                const idx1 = Math.floor(Math.random() * 3);
                const idx2 = (idx1 + 1) % 3;
                const c1 = document.getElementById('cup-' + idx1);
                const c2 = document.getElementById('cup-' + idx2);
                c1.style.transform = 'translateY(-20px)';
                c2.style.transform = 'translateY(-20px)';
                await new Promise(r => setTimeout(r, 150));
                c1.style.transform = '';
                c2.style.transform = '';
                await new Promise(r => setTimeout(r, 150));
            }
            resetCups();
        }

        init();
    </script>
</body>
</html>
"""

def parse_tags(text: str):
    scratchpad = ""
    dealer = ""
    
    s_start = text.find('<scratchpad>')
    if s_start != -1:
        s_end = text.find('</scratchpad>', s_start)
        if s_end != -1:
            scratchpad = text[s_start+12:s_end].strip()
        else:
            next_tag = text.find('<dealer>', s_start)
            if next_tag != -1:
                scratchpad = text[s_start+12:next_tag].strip()
            else:
                scratchpad = text[s_start+12:].strip()

    d_start = text.find('<dealer>')
    if d_start != -1:
        d_end = text.find('</dealer>', d_start)
        if d_end != -1:
            dealer = text[d_start+8:d_end].strip()
        else:
            dealer = text[d_start+8:].strip()
    
    if not dealer and not scratchpad:
        dealer = text
        
    return scratchpad, dealer

def main():
    parser = argparse.ArgumentParser(description="Generate an interactive web report from evaluation results.")
    parser.add_argument("--file", type=str, required=True, help="Path to JSONL evaluation results")
    parser.add_argument("--output", type=str, default="outputs/web_report.html", help="Path to output HTML file")
    args = parser.parse_args()

    input_path = Path(args.file)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = []
    try:
        with open(input_path, 'r') as f:
            for line in f:
                if not line.strip(): continue
                item = json.loads(line)
                
                # Parse tags if present
                output = item.get("output", "") or item.get("dealer_said", "")
                scratchpad, dealer = parse_tags(output)
                
                # Enrich with parsed fields if they are missing
                if "cot" not in item: item["cot"] = scratchpad
                if "dealer_said" not in item: item["dealer_said"] = dealer
                
                data.append(item)
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        sys.exit(1)

    html_content = HTML_TEMPLATE.replace("[DATA_PLACEHOLDER]", json.dumps(data))
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Web report generated at: {output_path}")

if __name__ == "__main__":
    main()
