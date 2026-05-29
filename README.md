<a href="README.md">
  <img src="https://img.shields.io/badge/Language-English-blue?style=flat-square&logo=google-translate&logoColor=white" alt="English">
</a>
<a href="README-TR.md">
  <img src="https://img.shields.io/badge/Dil-Türkçe-red?style=flat-square&logo=google-translate&logoColor=white" alt="Türkçe">
</a>

  <br />
  <br />

<div align="center">
  <img src="static/img/logo.png" width="120" height="120" />
  <br />
  <br />

  <p>
    Smart and Comprehensive SEO Analysis Tool
  </p>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

  <p>
    <a href="#features">Features</a> •
    <a href="#technologies">Technologies</a> •
    <a href="#installation">Installation</a> •
    <a href="#license">License</a> •
    <a href="#gallery">Gallery</a>
  </p>

  <br />
  <br />
</div>

## 📋 About

**Aether SEO** is a modern and powerful tool that instantly analyzes the performance, accessibility, and technical SEO status of web pages. Powered by Python, Flask, and BeautifulSoup, it examines your web page in milliseconds in the background while presenting you with the most detailed information about your SEO status through its modern interface.

<img src="static/img/md/20260301040527976.jpg" width="100%" />

## <a id="features"></a>✨ Features

### Comprehensive On-Page Analysis
- **Meta Tags**: Title and Description tag lengths, missing elements, and targeting accuracy.
- **Hierarchical Structure**: On-page heading structure (H1-H6), content heading accuracy, and title-H1 matching checks.
- **Content Quality**: Instant detection of HTML-to-Text ratio and sufficient word count.

### Performance Analysis and Optimization
- **Server and Connection Speed**: Examination of URL response times.
- **Asset Metrics**: Dimensional analysis of JS, CSS, and HTML resources.
- **Lazy-Load Detection**: Identification of assets requiring deferred loading (Off-viewport).

### Detailed Media Audit
- **Missing and Empty Tags**: Proper warning and differentiation of images with forgotten or empty alt tags.
- **Modern Format Transitions**: Detection of next-generation image format usage (such as WebP, AVIF).
- **Favicon Audit**: Identification of missing standard favicons.
 
### Technical SEO & Accessibility
- **Security**: SSL certificate validity and days remaining calculation.
- **A11y (Accessibility)**: Checking ARIA tag compatibilities, role hierarchies, and scannability metrics (based on Lighthouse standards).
- **Bot Directives**: Detection of `sitemap.xml` and `robots.txt` configuration deficiencies.

### Unique URL and Network Health
- Finding broken links (404, 5xx), instant warnings for the use of underscores in URLs, and unclean parameterized link structures.

## <a id="technologies"></a>🛠️ Technologies

The project is built using modern technologies for fast and effective auditing:

- **Backend:** Python 3, Flask, BeautifulSoup4, Requests, lxml
- **Frontend:** HTML5, Tailwind CSS, JavaScript, Jinja2
- **Performance:** Advanced Parallel Data Workflows (Thread pool and TTL Cache System `cachetools`)

## <a id="installation"></a>🚀 Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/xkintaro/aether-seo.git
   cd aether-seo
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Application:**
   ```bash
   python app.py
   ```
4. Once the application is running, you can start using the project by visiting `http://127.0.0.1:7663` in your browser.

## 📄 License <a id="license"></a>

This project is licensed under the MIT License. You can check the [LICENSE](LICENSE) file for details.

## 🖼️ Gallery <a id="gallery"></a>

<img src="static/img/md/20260301040528101.jpg" width="100%" />

#

<img src="static/img/md/20260301040527718.jpg" width="100%" />

#

<img src="static/img/md/20260301040527847.jpg" width="100%" />

#

<p align="center">
  <sub>❤️ Developed by "Mustafa TAŞAL" (kintaro)</sub>
</p>