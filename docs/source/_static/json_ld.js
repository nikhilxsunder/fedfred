// JSON-LD structured data for search engines
const script = document.createElement("script");
script.type = "application/ld+json";
script.text = JSON.stringify({
  "@context": "https://schema.org",
  "@type": ["SoftwareApplication", "SoftwareSourceCode"],
  "@id": "https://nikhilxsunder.github.io/fedfred/#software",
  name: "FedFred",
  alternateName: "fedfred",
  url: "https://nikhilxsunder.github.io/fedfred/",
  description:
    "A feature-rich Python package for interacting with the Federal Reserve Bank of St. Louis Economic Database (FRED), with support for ALFRED vintages, GeoFRED maps, async access, caching, and typed DataFrame outputs.",
  applicationCategory: "DeveloperApplication",
  applicationSubCategory: "Economic Data API Client",
  operatingSystem: "OS Independent",
  softwareVersion: "4.0.0",
  programmingLanguage: "Python",
  runtimePlatform: "Python 3",
  license: "https://spdx.org/licenses/MIT.html",
  isAccessibleForFree: true,
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "USD",
  },
  author: {
    "@type": "Person",
    name: "Nikhil Sunder",
    url: "https://github.com/nikhilxsunder",
  },
  codeRepository: "https://github.com/nikhilxsunder/fedfred",
  downloadUrl: "https://pypi.org/project/fedfred/",
  installUrl: "https://pypi.org/project/fedfred/",
  softwareHelp: {
    "@type": "CreativeWork",
    url: "https://nikhilxsunder.github.io/fedfred/",
  },
  releaseNotes:
    "https://github.com/nikhilxsunder/fedfred/blob/main/CHANGELOG.md",
  identifier: "https://doi.org/10.5281/zenodo.17180397",
  sameAs: [
    "https://github.com/nikhilxsunder/fedfred",
    "https://pypi.org/project/fedfred/",
    "https://anaconda.org/conda-forge/fedfred",
    "https://doi.org/10.5281/zenodo.17180397",
  ],
  keywords:
    "FRED, ALFRED, GeoFRED, FRASER, Federal Reserve, economic data, Python, API client, pandas, time series",
});
document.head.appendChild(script);
