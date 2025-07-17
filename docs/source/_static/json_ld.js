const script = document.createElement("script");
script.type = "application/ld+json";
script.text = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "FedFred",
    "url": "https://nikhilxsunder.github.io/fedfred/",
    "description": "A feature-rich Python package for interacting with the Federal Reserve Bank of St. Louis Economic Database (FRED).",
    "applicationCategory": "FinanceApplication",
    "operatingSystem": "Linux, MacOS, Windows",
    "softwareVersion": "2.1.1",
    "author": {
        "@type": "Person",
        "name": "Nikhil Sunder"
    },
    "license": "https://www.gnu.org/licenses/agpl-3.0.html",
    "programmingLanguage": "Python",
    "downloadUrl": "https://pypi.org/project/fedfred/",
    "sourceCode": "https://github.com/nikhilxsunder/fedfred",
    "documentation": "https://nikhilxsunder.github.io/fedfred/"
});
document.head.appendChild(script);
