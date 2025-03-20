# Security Policy

## Table of Contents

- [Current Vulnerability Status](#current-vulnerability-status)
- [Reporting a Vulnerability](#reporting-a-vulnerability)
- [Response Process](#response-process)
- [Disclosure Policy](#disclosure-policy)
- [Supported Versions](#supported-versions)
- [Common Vulnerabilities and Mitigations](#common-vulnerabilities-and-mitigations)
  - [API Client-Specific Vulnerabilities](#api-client-specific-vulnerabilities)
  - [General Python Vulnerabilities](#general-python-vulnerabilities)
- [Security Measures](#security-measures)
- [Security-Related Configuration](#security-related-configuration)
- [Third-Party Security Dependencies](#third-party-security-dependencies)
- [Secure Software Delivery](#secure-software-delivery)
  - [PyPI (Python Package Index)](#pypi-python-package-index)
  - [GitHub Releases](#github-releases)
- [Verifying Package Signatures](#verifying-package-signatures)
- [Security Updates and Announcements](#security-updates-and-announcements)
- [Security Design Principles](#security-design-principles)

## Current Vulnerability Status

As of March 2025, there are no unpatched vulnerabilities of medium or higher severity that have been publicly known for more than 60 days in the FedFred codebase.

We monitor for vulnerabilities through:

- Automated dependency scanning with GitHub Dependabot
- Security analysis with CodeQL
- Community reports through our responsible disclosure process
- Regular manual security reviews

## Reporting a Vulnerability

The FedFred team takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose your findings.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:

- **Email**: nsunder724@gmail.com

Please include the following information in your report:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

## Response Process

When you report a vulnerability, you can expect:

1. **Acknowledgment**: We will acknowledge your email within 48 hours.
2. **Verification**: We will work to verify the vulnerability and its impact.
3. **Remediation**: We will develop a fix and test it.
4. **Disclosure**: Once a fix is ready, we will coordinate with you on the disclosure timeline.

## Disclosure Policy

- We will work with you to understand and address the vulnerability.
- We aim to provide a fix within 60 days of verification for all medium or higher severity vulnerabilities.
- We will credit you for the discovery in our release notes and CHANGELOG (unless you request otherwise).

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

Only the latest minor release within each supported major version will receive security updates.

## Common Vulnerabilities and Mitigations

As an API client library, FedFred's primary developer is knowledgeable about these common vulnerability types and their mitigations:

### API Client-Specific Vulnerabilities

1. **Insecure API Key Handling**

   - **Vulnerability**: Hardcoded API keys, keys in source code, or improper storage
   - **Mitigation**: FedFred never stores API keys, recommends environment variables, and provides clear documentation on secure key management

2. **Injection in API Parameters**

   - **Vulnerability**: Unvalidated user inputs passed directly to API calls
   - **Mitigation**: All parameters are validated against allowlists before being sent to the API

3. **Certificate Verification Bypass**

   - **Vulnerability**: Disabling SSL/TLS verification to make HTTPS requests work
   - **Mitigation**: FedFred always enforces certificate verification in all HTTP clients

4. **Insecure Deserialization**

   - **Vulnerability**: Unsafe parsing of API responses
   - **Mitigation**: Strict type validation of all API responses before further processing

5. **Excessive Data Exposure**
   - **Vulnerability**: Logging sensitive information from API responses
   - **Mitigation**: Careful filtering of sensitive data before logging

### General Python Vulnerabilities

1. **Dependency-Chain Vulnerabilities**

   - **Vulnerability**: Security issues in dependencies
   - **Mitigation**: Regular dependency scanning with Dependabot, minimal dependency philosophy

2. **XML External Entity (XXE) Processing**

   - **Vulnerability**: When parsing XML from API responses
   - **Mitigation**: Disabling external entity processing in XML parsers

3. **Path Traversal in File Operations**

   - **Vulnerability**: For cached data storage
   - **Mitigation**: Strict validation of file paths and names

4. **Regular Expression Denial of Service (ReDoS)**

   - **Vulnerability**: Unsafe regular expressions for input validation
   - **Mitigation**: Careful design of regular expressions, usage of timeout mechanisms

5. **Improper Error Handling**
   - **Vulnerability**: Leaking sensitive information in error messages
   - **Mitigation**: Custom exception types with appropriate information filtering

## Security Measures

FedFred implements several security measures:

- Type hints and static analysis to prevent common errors
- Dependency scanning through GitHub's Dependabot
- Automated security scans using CodeQL
- Regular dependency updates
- Signed releases

## Security-Related Configuration

FedFred handles API keys that should be kept confidential. We recommend:

- Never hardcode API keys in your application
- Use environment variables or secure vaults for API key storage
- If you suspect your FRED API key has been compromised, regenerate it at the [FRED API portal](https://fred.stlouisfed.org/docs/api/api_key.html)

## Third-Party Security Dependencies

FedFred relies on several third-party libraries. We regularly update these dependencies to incorporate their security fixes.

## Secure Software Delivery

FedFred is distributed through these secure channels to prevent MITM attacks:

### PyPI (Python Package Index)

- All PyPI downloads use HTTPS (TLS) by default
- PyPI implements modern TLS practices to prevent interception
- Install securely using: `pip install fedfred`

### GitHub Releases

- All GitHub downloads use HTTPS (TLS) by default
- We provide GPG signatures (not just checksums) for all release artifacts
- Clone securely using: `git clone https://github.com/nikhilxsunder/fedfred.git`

For maximum security, you can also verify our release signatures:

1. Download our public GPG key: [\[LINK_TO_GPG_KEY\]](https://raw.githubusercontent.com/nikhilxsunder/fedfred/main/fedfred_public_key.asc)
2. Import the key: `gpg --import fedfred_public_key.asc`
3. Verify the release: `gpg --verify fedfred-1.2.6.tar.gz.asc fedfred-1.2.6.tar.gz`

## Verifying Package Signatures

All FedFred releases are signed with GPG. To verify a release:

1. Import our public key:

```sh
curl -s https://raw.githubusercontent.com/nikhilxsunder/fedfred/main/fedfred_public_key.asc | gpg --import
```

2. Download the package and signature:
   Example for version 1.2.6

```sh
curl -O https://github.com/nikhilxsunder/fedfred/releases/download/v1.2.6/fedfred-1.2.6.tar.gz curl -O https://github.com/nikhilxsunder/fedfred/releases/download/v1.2.6/fedfred-1.2.6.tar.gz.asc
```

3. Verify the signature:

```sh
gpg --verify fedfred-1.2.6.tar.gz.asc fedfred-1.2.6.tar.gz
```

## Security Updates and Announcements

Security updates will be announced via:

- GitHub release notes
- README updates
- Our documentation portal

## Security Design Principles

FedFred follows established security design principles, including the Saltzer and Schroeder principles:

1. **Economy of mechanism**: We keep our codebase modular and focused, avoiding unnecessary complexity.
2. **Fail-safe defaults**: Our API client defaults to secure settings (HTTPS, rate limiting, etc.).
3. **Complete mediation**: All API requests verify authentication and authorization.
4. **Open design**: Our security doesn't depend on obscurity - our code is open source and we rely on proper key management.
5. **Separation of privilege**: We encourage environment-based API key storage separate from application code.
6. **Least privilege**: Our API client only requests the minimum necessary permissions.
7. **Least common mechanism**: We minimize shared state between components.
8. **Psychological acceptability**: Our API design follows standard Python conventions for ease of use.
9. **Limited attack surface**: We carefully review dependencies and minimize code exposure.
10. **Input validation with allowlists**: We validate all user inputs against expected patterns before processing.

For questions about this policy, please contact nsunder724@gmail.com.
