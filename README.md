<div align="center">
  <img src="static/img/logo.png" alt="Aether SEO" width="120" height="120" />
  <br />
  <br />

  [![Python](https://img.shields.io/badge/Python-3-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
  [![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

  <p align="center">
    <b>Smart and Comprehensive SEO Analysis Tool</b>
    <br />
    <br />
    <a href="#features">Features</a> •
    <a href="#technologies">Technologies</a> •
    <a href="#installation">Installation</a>
  </p>
</div>

---

## 📋 About

**Aether SEO** is a modern and powerful tool that instantly analyzes the performance, accessibility, and technical SEO status of web pages. Powered by Python, Flask, and BeautifulSoup, it examines your web page in milliseconds in the background while presenting you with the most detailed information about your SEO status through its modern interface.

<img src="static/img/md/20260301040527976.jpg" width="100%" style="border-radius: 8px;" />

## <a id="features"></a>✨ Features

### 🔍 Comprehensive On-Page Analysis
- **Meta Tags**: Title and Description tag lengths, missing elements, and targeting accuracy.
- **Hierarchical Structure**: On-page heading structure (H1-H6), content heading accuracy, and title-H1 matching checks.
- **Content Quality**: Instant detection of HTML-to-Text ratio and sufficient word count.

### ⚡ Performance Analysis and Optimization
- **Server and Connection Speed**: Examination of URL response times.
- **Asset Metrics**: Dimensional analysis of JS, CSS, and HTML resources.
- **Lazy-Load Detection**: Identification of assets requiring deferred loading (Off-viewport).

### 🖼️ Detailed Media Audit
- **Missing and Empty Tags**: Proper warning and differentiation of images with forgotten or empty alt tags.
- **Modern Format Transitions**: Detection of next-generation image format usage (such as WebP, AVIF).
- **Favicon Audit**: Identification of missing standard favicons.
 
### 🛡️ Technical SEO & Accessibility
- **Security**: SSL certificate validity and days remaining calculation.
- **A11y (Accessibility)**: Checking ARIA tag compatibilities, role hierarchies, and scannability metrics (based on Lighthouse standards).
- **Bot Directives**: Detection of `sitemap.xml` and `robots.txt` configuration deficiencies.

### 🌐 Unique URL and Network Health
- Finding broken links (404, 5xx), instant warnings for the use of underscores in URLs, and unclean parameterized link structures.

<img src="static/img/md/20260301040528101.jpg" width="100%" style="border-radius: 8px;" />

## <a id="technologies"></a>🛠️ Technologies

The project is built using modern technologies for fast and effective auditing:

- **Backend:** Python 3, Flask, BeautifulSoup4, Requests, lxml
- **Frontend:** HTML5, Tailwind CSS, JavaScript, Jinja2
- **Performance:** Advanced Parallel Data Workflows (Thread pool and TTL Cache System `cachetools`)

<img src="static/img/md/20260301040527718.jpg" width="100%" style="border-radius: 8px;" />

## <a id="installation"></a>🚀 Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/xkintaro/aether-seo.git
   cd aether-seo
   ```

2. **Install Dependencies:**
   Python 3.10+ is recommended for proper installation of dependencies.
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Application:**
   ```bash
   python app.py
   ```
4. Once the application is running, you can start using the project by visiting `http://127.0.0.1:7663` (default address) in your browser.

<img src="static/img/md/20260301040527847.jpg" width="100%" style="border-radius: 8px;" />

## 📂 Project Structure

```
aether-seo/
├── app.py                     # Main Flask application (Server and Endpoints)
├── config.py                  # Optional metrics, scoring settings, and configuration
├── seo_analyzer.py            # Main SEO module, multi-section analysis management center
├── requirements.txt           # Python dependencies
├── analyzers/                 # Specialized sub-analysis modules (Network, Media, A11y, etc.)
├── templates/
│   ├── index.html             # Search page
│   ├── report.html            # Results page design
│   ├── base.html              # Jinja2 base template layout
│   ├── macros.html            # Template for UI elements (Progress bar, etc.)
│   └── sections/              # Segmented report tab modules
└── static/
    ├── css/                   # Global CSS and component styles
    ├── js/                    # Client-side reporting logic and chart rendering scripts
    └── img/                   # Application icons, logos, etc.
```

---

<p align="center">
  <sub>❤️ Developed by Kintaro.</sub>
</p>
