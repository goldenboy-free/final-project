document.addEventListener('DOMContentLoaded', () => {
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    let isDarkMode = localStorage.getItem('theme') === 'dark' || (prefersDarkScheme.matches && !localStorage.getItem('theme'));

    // Function to set the theme based on local storage or system preference
    function setTheme() {
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
            document.getElementById('themeSwitch').checked = true;
        } else {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
            document.getElementById('themeSwitch').checked = false;
        }
    }

    // Apply the theme initially
    setTheme();

    // Toggle between dark and light modes based on checkbox change
    document.getElementById('themeSwitch').addEventListener('change', () => {
        isDarkMode = !isDarkMode;
        if (isDarkMode) {
            localStorage.setItem('theme', 'dark');
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            localStorage.setItem('theme', 'light');
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
        }
    });
});

document.getElementById('auditForm').addEventListener('submit', function (event) {
    event.preventDefault();
    document.getElementById('loadingSpinner').style.display = 'inline-block'; // Show spinner

    let url = document.getElementById('urlInput').value.trim();

    // Automatically prepend https:// if the user forgets it
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
        document.getElementById('urlInput').value = url; // Update input field to show the change
    }

    fetch('/api/analyze', {  // <-- Updating endpoint from /api/scan to /api/analyze based on our FastAPI
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url })
    }).then(response => response.json())
        .then(data => {
            document.getElementById('loadingSpinner').style.display = 'none'; // Hide spinner

            if (data.status === 'error' || data.detail) {
                alert("Error: " + (data.message || data.detail[0]?.msg || "Failed to analyze website"));
                return;
            }

            if (!data.issues) {
                alert("No issues array returned from backend.");
                return;
            }

            updateUI(data);
        })
        .catch(error => {
            document.getElementById('loadingSpinner').style.display = 'none';
            alert("Network or server error: " + error.message);
        });
});

function updateUI(data) {
    const issuesList = document.getElementById('issuesList');
    issuesList.innerHTML = ''; // Clear previous issues

    // Group issues by category
    const groupedIssues = {};
    data.issues.forEach(issue => {
        if (!groupedIssues[issue.category]) {
            groupedIssues[issue.category] = [];
        }
        groupedIssues[issue.category].push(issue);
    });

    // Render grouped issues
    for (const [category, categoryIssues] of Object.entries(groupedIssues)) {
        const categoryHeader = document.createElement('h3');
        categoryHeader.style.borderBottom = '2px solid #ccc';
        categoryHeader.style.paddingBottom = '5px';
        categoryHeader.style.marginTop = '20px';
        categoryHeader.innerText = `${category} (${categoryIssues.length})`;
        issuesList.appendChild(categoryHeader);

        categoryIssues.forEach(issue => {
            const card = document.createElement('div');
            card.className = 'card';
            card.style.backgroundColor = getSeverityColor(issue.severity);
            // card.style.color = "#ffffff";
            card.style.padding = '15px';
            card.style.margin = '10px 0';
            card.style.borderRadius = '5px';
            card.innerHTML = `
                <h4 style="margin-top: 0">${issue.title}</h4>
                <p><strong>Impact:</strong> ${issue.impact}</p>
                <p><strong>Description:</strong> ${issue.description}</p>
                <p><strong>Suggestion:</strong> ${issue.suggestion}</p>
            `;
            issuesList.appendChild(card);
        });
    }

    document.getElementById('totalIssues').innerText = data.total_issues;
    document.getElementById('highIssues').innerText = data.issues.filter(i => i.severity === 'HIGH').length;
    document.getElementById('mediumIssues').innerText = data.issues.filter(i => i.severity === 'MEDIUM').length;
    document.getElementById('lowIssues').innerText = data.issues.filter(i => i.severity === 'LOW').length;

    document.getElementById('responseTime').innerText = data.runtime || 0;
}

function getSeverityColor(severity) {
    switch (severity) {
        case 'HIGH': return '#EF4444'; // Red
        case 'MEDIUM': return '#F59E0B'; // Orange
        case 'LOW': return '#0EA5E9'; // Oceanic Blue
        default: return '#ffffff';
    }
}
