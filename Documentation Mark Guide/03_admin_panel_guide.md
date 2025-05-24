# Admin Panel Guide

This document provides a comprehensive guide to using the Mark Assistant administration panel, which allows you to manage patients, view analytics, configure the system, and monitor conversations.

## Accessing the Admin Panel

The admin panel is accessible at `https://your-domain.com/admin` or `http://localhost:8000/admin` in development mode.

Login credentials are set during installation in the `.env` file:
- Username: Value of `ADMIN_USERNAME` (default: admin)
- Password: Value of `ADMIN_PASSWORD`

## Dashboard Overview

![Admin Dashboard](../docs/images/admin_dashboard.png)

The dashboard provides an overview of:
- Active conversations in the last 24 hours
- Total patients registered
- Appointment statistics (scheduled, completed, canceled)
- Language distribution of conversations
- Recent system alerts

## Navigation

The admin panel is organized into the following sections:

1. **Dashboard**: Home screen with key metrics
2. **Patients**: Patient management
3. **Conversations**: View and manage conversations
4. **Appointments**: Appointment management
5. **Analytics**: Detailed analytics and reports
6. **Security**: Security settings and logs
7. **Configuration**: System configuration
8. **Logs**: System and error logs

## Patient Management

### Viewing Patients

The Patients section displays a list of all registered patients with the following information:
- Name
- Phone number
- Email
- Registration date
- Last activity
- Preferred language
- Status (active/inactive)

### Adding a New Patient

To add a new patient:

1. Click the "Add Patient" button
2. Fill in the required fields:
   - Name
   - Phone number (in international format, e.g., +34612345678)
   - Email (optional)
   - Preferred language
   - Notes (optional)
3. Click "Save"

### Editing Patient Information

To edit a patient's information:

1. Click on the patient's name in the list
2. Modify the desired fields
3. Click "Save Changes"

### Deactivating a Patient

To deactivate a patient (this will stop Mark from responding to their messages):

1. Click on the patient's name in the list
2. Change the "Status" dropdown to "Inactive"
3. Click "Save Changes"

## Conversation Management

### Viewing Conversations

The Conversations section allows you to view all conversations between Mark and patients:

- Filter by patient name, date range, or language
- Search for specific content
- Sort by date, length, or status

### Conversation Details

Click on a conversation to view its details:

- Complete message history
- Timestamps for each message
- Language used
- AI model responses
- System notes (e.g., language switches, escalations)

### Exporting Conversations

To export a conversation:

1. Select the conversation(s) using the checkboxes
2. Click "Export" and choose the format (PDF, CSV, or JSON)
3. The exported file will be downloaded to your computer

### Deleting Conversations

To delete a conversation:

1. Select the conversation(s) using the checkboxes
2. Click "Delete"
3. Confirm the deletion

**Note**: Deletion is permanent and cannot be undone. Consider exporting conversations before deletion.

## Appointment Management

### Viewing Appointments

The Appointments section displays all scheduled appointments with the following information:
- Patient name
- Date and time
- Duration
- Type (initial consultation, follow-up, etc.)
- Status (scheduled, completed, canceled)
- Notes

### Creating a Manual Appointment

While most appointments are created through the WhatsApp interface, you can manually create an appointment:

1. Click "Add Appointment"
2. Select the patient from the dropdown
3. Choose the date, time, and duration
4. Select the appointment type
5. Add any relevant notes
6. Click "Save"

### Modifying Appointments

To modify an appointment:

1. Click on the appointment in the list
2. Make the necessary changes
3. Click "Save Changes"

### Canceling Appointments

To cancel an appointment:

1. Click on the appointment in the list
2. Change the status to "Canceled"
3. Add a cancellation reason (optional)
4. Click "Save Changes"

## Analytics

The Analytics section provides detailed insights into Mark's performance and usage:

### Conversation Analytics

- Total conversations per day/week/month
- Average conversation length
- Language distribution
- Response time statistics
- Common topics (based on keyword analysis)

### Appointment Analytics

- Appointments scheduled per day/week/month
- Completion rate
- Cancellation rate and reasons
- Popular time slots
- Distribution by appointment type

### Patient Analytics

- New patients per day/week/month
- Active patients
- Engagement metrics
- Retention rate

### Custom Reports

To generate a custom report:

1. Click "Custom Report"
2. Select the data points you want to include
3. Choose the date range
4. Select the visualization type (table, bar chart, line chart, etc.)
5. Click "Generate Report"
6. Export the report as PDF, CSV, or PNG

## Security Settings

### Encryption Management

The Security section allows you to manage the encryption system:

- View the current encryption status
- Manually trigger key rotation
- Download encryption key backups (requires additional authentication)
- View key usage statistics

### Threat Detection

Configure the threat detection system:

- Set sensitivity level (low, medium, high)
- Define custom alert keywords
- Configure escalation contacts
- View threat detection logs

### Access Control

Manage admin panel access:

- Add additional admin users
- Set permission levels
- Configure two-factor authentication
- View login history and failed login attempts

## System Configuration

### Language Settings

Configure language-related settings:

- Enable/disable supported languages
- Adjust language detection thresholds
- Set the default language
- Upload custom language models

### AI Model Settings

Configure the Claude AI model:

- Select the model version (Claude-3-Opus, Claude-3-Sonnet, Claude-3-Haiku)
- Adjust temperature and other generation parameters
- Set token limits
- Upload custom system prompts

### Integration Settings

Configure external service integrations:

- Twilio (WhatsApp)
- Calendly
- Stripe
- Zoom

### Notification Settings

Configure system notifications:

- Email alerts for critical events
- Daily/weekly summary reports
- Error notifications
- Patient activity alerts

## System Logs

The Logs section provides access to various system logs:

- Application logs
- Error logs
- Security logs
- API request logs
- Integration logs (Twilio, Calendly, etc.)

To view logs:

1. Select the log type from the dropdown
2. Choose the date range
3. Set the log level (INFO, WARNING, ERROR, etc.)
4. Click "View Logs"

Logs can be exported as text files for further analysis.

## Best Practices

### Security

- Change the default admin password immediately after installation
- Enable two-factor authentication for admin accounts
- Regularly backup encryption keys
- Review security logs weekly
- Rotate admin credentials every 90 days

### Performance

- Archive old conversations (older than 6 months)
- Clean up the database regularly
- Monitor server resource usage
- Optimize large queries

### Patient Privacy

- Only access patient conversations when necessary
- Export data only when required for legitimate purposes
- Delete sensitive data when no longer needed
- Ensure all staff are trained on data protection policies

## Troubleshooting

### Common Issues

#### Slow Admin Panel

If the admin panel is loading slowly:
1. Check server resource usage
2. Consider archiving old conversations
3. Optimize database queries
4. Increase server resources if necessary

#### Missing Data

If data appears to be missing:
1. Check the date filters
2. Verify that the data was properly saved
3. Check for any errors in the logs
4. Restore from backup if necessary

#### Login Issues

If you cannot log in:
1. Verify your credentials
2. Check if your account is locked due to failed attempts
3. Clear browser cookies and cache
4. Reset your password using the recovery process

## Support and Feedback

For technical support or to provide feedback on the admin panel:

- Email: support@centrepsicologiajaumeprimer.com
- Phone: +34 637885915
- In-app feedback form: Click "Feedback" in the footer

## Next Steps

After familiarizing yourself with the admin panel, refer to the following documentation:

1. [API Documentation](04_api_documentation.md)
2. [Security Guide](05_security_guide.md)
3. [Customization Guide](06_customization_guide.md)
4. [Troubleshooting Guide](07_troubleshooting_guide.md) 