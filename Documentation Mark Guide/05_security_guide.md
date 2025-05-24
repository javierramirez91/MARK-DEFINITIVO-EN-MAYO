# Security Guide

This document provides detailed information about the security features and best practices for the Mark Assistant system, focusing on data protection, encryption, and compliance.

## Security Architecture

Mark Assistant has been designed with a "security by design" approach, incorporating multiple layers of protection:

### Security Layers

1. **Application Layer**
   - Input validation
   - Data sanitization
   - Injection protection
   - Authentication and authorization

2. **Communication Layer**
   - TLS/SSL for all communications
   - End-to-end encryption for messages
   - Data integrity verification

3. **Storage Layer**
   - Encryption of data at rest
   - Isolation of sensitive data
   - Secure key management

4. **Infrastructure Layer**
   - Network segmentation
   - Firewalls and WAF
   - Continuous monitoring

## End-to-End Encryption

Mark Assistant implements an end-to-end encryption system to protect all conversations with patients.

### Encryption Implementation

The system uses a combination of asymmetric (RSA-4096) and symmetric (AES-256-GCM) encryption:

1. **Key Generation**
   - 4096-bit RSA keys for the server
   - Unique 256-bit symmetric keys for each user
   - Automatic key rotation every 30 days

2. **Encryption Process**
   - User symmetric keys are encrypted with the RSA public key
   - Messages are encrypted with the user's symmetric key
   - AES-256-GCM with random nonce is used for each message
   - Metadata is included as authenticated additional data (AAD)

3. **Key Storage**
   - Private keys are stored with restrictive permissions
   - A limited history of previous keys is maintained to access old messages
   - Encrypted backups of keys

### Encryption System Verification

The system includes a verification function that checks:

- Availability of cryptographic libraries
- Presence and validity of RSA keys
- Key file permissions
- User key registration
- Encryption/decryption test

## Authentication and Access Control

### User Authentication

- Multi-factor authentication for administrators
- JWT tokens with signature and expiration
- Secure password policies
- Account lockout after failed attempts

### Access Control

- Role-based access control (RBAC)
- Principle of least privilege
- Segregation of duties
- Access audit logging

## Data Protection

### Data in Transit

- TLS 1.3 for all HTTP communications
- End-to-end encryption for WhatsApp messages
- Automatically managed SSL/TLS certificates
- HSTS to enforce secure connections

### Data at Rest

- Database encryption
- Tokenization of personally identifiable information (PII)
- Secure credential storage
- Encrypted backups

### Data Retention and Deletion

- Configurable data retention policies
- Secure data deletion at the end of the retention period
- Data anonymization for long-term analysis
- Data purge process for deletion requests

## Threat Detection

Mark Assistant includes a threat detection system that monitors:

1. **Anomalous Behavior Patterns**
   - Unusual access attempts
   - Suspicious message patterns
   - Activity outside normal hours

2. **Crisis Detection**
   - Identification of language indicating patient risk
   - Automatic escalation to mental health professionals
   - Crisis response protocols

3. **Abuse Prevention**
   - Detection of spam and malicious messages
   - Rate limiting to prevent brute force attacks
   - IP blocking for suspicious activities

## Audit Logging

The system maintains detailed audit logs for:

- Administrator accesses
- Configuration changes
- Encryption/decryption operations
- Security alerts
- Patient data access

Logs include:
- Timestamp
- User/system
- Action performed
- IP address
- Action result

## Regulatory Compliance

### GDPR (General Data Protection Regulation)

- Explicit consent for data processing
- Right to access, rectification, and deletion
- Data protection impact assessments
- Data breach notification

### HIPAA (for international expansion)

- Administrative, physical, and technical safeguards
- Business associate agreements
- Limited disclosure of information
- Breach notification policies

### Additional Standards

- ISO 27001 (Information Security)
- NIST Cybersecurity Framework
- Local healthcare data protection standards

## AI Security and GPT-4 Considerations

### Data Protection in AI Interactions

- **Data Anonymization**: All data sent to the GPT-4 API is anonymized to remove personally identifiable information (PII) before transmission.
- **Sensitive Information Filtering**: Filtering system that detects and redacts sensitive information such as phone numbers, addresses, and specific medical data.
- **Session Tokens**: Use of unique session tokens for each interaction with the GPT-4 API, with no data persistence between sessions.
- **Data Minimization**: Only essential information is sent to the GPT-4 API, following the principle of data minimization.

### AI Risk Mitigation

- **Prompt Injection Prevention**: Implementation of input validation and sanitization to prevent prompt injection attacks.
- **Jailbreaking Detection**: Continuous monitoring to detect attempts to bypass GPT-4's ethical safeguards.
- **Context Limitations**: Restriction of context provided to GPT-4 to minimize exposure of sensitive data.
- **Output Verification**: Verification system that analyzes GPT-4 responses to detect inappropriate or potentially harmful content.
- **Fallback Mechanisms**: Alternative processing paths when GPT-4 is unavailable or returns potentially problematic responses.

### Auditing and Transparency

- **Complete Logging**: All interactions with GPT-4 are logged (without including sensitive data) for audit purposes.
- **Explainability**: Clear documentation on how AI models are used and what data is shared.
- **Human Review**: Periodic review process by mental health professionals to evaluate the quality and safety of responses.
- **Model Version Control**: Tracking of GPT-4 model versions used and their associated security profiles.

### AI-Specific Compliance

- **OpenAI Terms of Service**: Strict compliance with OpenAI's terms of service and usage policies.
- **Ethical Guidelines**: Adherence to ethical guidelines for AI use in mental health contexts.
- **Security Updates**: Process for rapidly implementing security patches and updates related to GPT-4.
- **Data Processing Agreements**: Formal agreements covering data processing activities involving third-party AI services.

### GPT-4 Integration Security

- **API Authentication**: Secure management of API keys with regular rotation.
- **Request/Response Encryption**: Additional encryption layer for API communications.
- **Rate Limiting**: Controls to prevent excessive API usage and associated costs.
- **Content Filtering**: Pre and post-processing filters to ensure appropriate content.
- **Prompt Engineering Security**: Secure design of system prompts to prevent information leakage or manipulation.

## Incident Response

### Response Plan

1. **Detection and Analysis**
   - Continuous monitoring systems
   - Escalation procedures
   - Initial forensic analysis

2. **Containment and Eradication**
   - Isolation of affected systems
   - Threat elimination
   - Restoration from secure backups

3. **Recovery**
   - System integrity verification
   - Gradual service restoration
   - Post-incident monitoring

4. **Communication**
   - Notification to affected parties
   - Communication with regulatory authorities
   - Transparency reports

### Drills and Continuous Improvement

- Periodic incident response drills
- Post-incident review and lessons learned
- Policy and procedure updates
- Continuous team training

## Best Practices for Administrators

1. **Credential Management**
   - Use strong and unique passwords
   - Change passwords periodically
   - Use password managers
   - Enable multi-factor authentication

2. **Secure Access**
   - Use secure networks to access the admin panel
   - Avoid access from public networks
   - Log out after each use
   - Verify URL and SSL certificate before logging in

3. **Data Management**
   - Minimize downloading sensitive data
   - Delete temporary files
   - Encrypt local devices
   - Follow clean desk policies

4. **Updates and Patches**
   - Keep the system updated
   - Regularly review security updates
   - Follow change management process
   - Test updates in development environment

## Additional Resources

- [Complete Security Policy](../policies/security_policy.pdf)
- [Incident Response Procedures](../policies/incident_response.pdf)
- [GDPR Compliance Guide](../policies/gdpr_compliance.pdf)
- [Security Controls Matrix](../policies/security_controls.xlsx)

## Security Contact

To report vulnerabilities or security incidents, contact immediately:

- **Email**: security@centrepsicologiajaume.com
- **Emergency Phone**: +34 XXX XXX XXX

For general security inquiries:
- **Email**: info@centrepsicologiajaume.com 