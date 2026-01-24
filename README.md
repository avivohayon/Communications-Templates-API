# Communications API - Home Assignment

## Welcome!

Thank you for taking the time to complete this assignment. We're excited to see what you build!

**Please read all instructions carefully before you begin.**

---

## 📋 Overview

Your task is to build a **Communications API** web server that allows clients to send Email and SMS messages using reusable message templates.

**Time Allocation:** Approximately **3 hours (without the bonus tasks)**

---

## 🎯 Evaluation Criteria

Your submission will be evaluated based on:

- **Functionality:** Everything should work according to the instructions. Errors and exceptions should be handled correctly. Bonus points for efficiency.
- **Code Clarity and Organization:** Clean, well-organized, and easy-to-understand code.
- **Use of Git:** Organized commits with explanatory messages and effective branch management.
- **Code Design and Architecture:** Demonstrates good design and architectural decisions for API, data model, and logic.
- **Testing:** Implemented tests should pass successfully and cover key functionalities.
- **Best Practices:** Adherence to best practices in backend development.
- **Documentation:** Clear instructions for setup, usage, and API endpoints. Visual diagrams (flowcharts) are highly valued.
- **Observability:** Proper logging should be implemented throughout the application. Additional monitoring and telemetry data (metrics, traces, etc.) is encouraged.

---

## 💡 Recommended Approach

We suggest tackling this assignment in phases:

1. **Start with core functionality** (Tasks 1-2): Get the basic features working while keeping the evaluation criteria in mind. Focus on clean code, proper error handling, testing, and git commits from the start.

2. **Refine your solution**: Once core features work, consider improvements to:
   - Architecture and design patterns for maintainability
   - **Performance optimizations**: How can you reduce unnecessary work and improve response times or make it easy on the system?
   - **Resilience**: What happens when things go wrong? How does your system handle failures?
   - **Scalability**: How would your design handle significant load?
   - **Observability**: How would you monitor and debug this system in production?
   - Enhanced documentation with diagrams

3. **Add bonus tasks** (if time permits): Start with simpler bonuses (Template Preview, Message History) before more complex ones (Rate Limiting, UI).

**Remember:** A well-executed core implementation is better than rushing through bonus tasks. Quality over quantity!

---

## 📝 Project Tasks

### Task 1: Message Template Management

#### What is a Message Template?

A **Message Template** is a pre-designed, reusable content structure with placeholders for customizable content (the message body). These placeholders are later rendered with data (a JSON object) to form a concrete message.

Message templates support two channels: **Email** and **SMS**.

#### Message Template Structure

**Email Message Template:**
```json
{
  "id": "UUID",
  "name": "string",
  "content": "string",
  "template_language": "Handlebars or Jinja2",
  "subject": "string",
  "channel_type": "Email"
}
```

**Example Email Template:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Welcome!</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { padding: 20px; }
        .highlight { color: #007BFF; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hi <span class="highlight">{{name}}</span>,</h1>
        <p>Welcome to our service! We're excited to have you on board.</p>
    </div>
</body>
</html>
```

**SMS Message Template:**
```json
{
  "id": "UUID",
  "name": "string",
  "content": "string",
  "template_language": "Handlebars or Jinja2",
  "channel_type": "SMS"
}
```

**Example SMS Template:**
```
Hi {{name}}! Welcome to our service. We're excited to have you on board.
```

#### Requirements

Implement API endpoint(s) that allow clients to:
- Create message templates for both Email and SMS channels
- Persist message templates in a database of your choice (SQL, NoSQL, in-memory - your choice)
- Return the created template with its generated ID

The API design and data model architecture are part of your assignment.

---

### Task 2: Send Message

#### Requirements

Implement API endpoint(s) that allow clients to send messages using stored templates.

**Example Request Data:**
```json
{
  "template_id": "uuid-here",
  "template_name": "welcome_template",
  "data": {
    "name": "Alex"
  },
  "to": ["recipient1@email.com", "recipient2@email.com", "+972123456789"]
}
```

**Note:** The API should support template lookup by either `template_id` OR `template_name`.

**Functionality:**
1. Retrieve the message template by ID or name
2. Render the template content using the provided data (context)
3. Send the message to all recipients through the appropriate channel (Email or SMS)

The API design and architecture are part of your assignment.

#### Channel Integration

##### **Email - SendGrid**

- API Documentation: https://docs.sendgrid.com/api-reference/mail-send/mail-send
- API Key: Sent to you via email
- From Email: `lendbuzz.candidate@outlook.com`

**⚠️ Sandbox Mode:** Emails will not actually be sent. The API will return a success response without delivering emails.

**Sendgrid Send Command Example:**
```bash
curl -X POST https://api.sendgrid.com/v3/mail/send \
-H 'Authorization: Bearer <api-key>' \
-H 'Content-Type: application/json' \
-d '{
  "from": {
    "email": "lendbuzz.candidate@outlook.com",
    "name": "Me"
  },
  "personalizations": [
    {
      "to": [
        {
          "email": "<your_email_address>"
        }
      ]
    }
  ],
  "subject": "hi",
  "content": [
    {
      "type": "text/html",
      "value": "Hi there,\n\nThis is a test email sent using the curl command and the SendGrid API.\n\nBest regards,\nMe"
    }
  ],
  "mail_settings": {
    "sandbox_mode": {
      "enable": true
    }
  }
}'
```

##### **SMS - Twilio**

- API Documentation: https://www.twilio.com/docs/sms/api
- Simulate errors (for error handling and testing purposes): https://www.twilio.com/docs/iam/test-credentials#test-sms-messages-parameters-to
- Credentials: Sent to you via email
- Account SID: `your_twilio_account_sid`
- From Number: `+15005550006`

**⚠️ Sandbox Mode:** SMS messages will not actually be sent. The API will return a success response without delivering messages.

**Twilio Send Command Example:**
```bash
curl -X POST https://api.twilio.com/2010-04-01/Accounts/your_twilio_account_sid/Messages.json \
--data-urlencode "To=+972<number>" \
--data-urlencode "From=+15005550006" \
--data-urlencode "Body=Hello from Twilio via cURL!" \
-u your_twilio_account_sid:your_auth_token
```

---

## 🎁 Bonus Tasks (Optional)

These tasks are optional but will be viewed favorably:

### Bonus Task 3: Template Preview

Implement an API endpoint that allows clients to preview how a template will look with sample data **without actually sending** the message.

**Example Request:**
```json
POST /templates/{id}/preview
{
  "data": {
    "name": "Alex",
    "amount": 1000
  }
}
```

**Example Response:**
```json
{
  "rendered_content": "Hi Alex! Your payment of $1000 has been processed.",
  "subject": "Payment Confirmation"
}
```

This feature helps users validate their templates before sending actual messages.

---

### Bonus Task 4: Message History

Implement API endpoint(s) that allow clients to view the history of sent messages.

**Functionality:**
- Retrieve a list of sent messages with relevant details:
  - Message ID
  - Template used (ID and name)
  - Recipients
  - Channel (Email or SMS)
  - Timestamp
  - Status (success/failure)
  - Rendered content (optional)
- Support filtering by:
  - Channel type (Email or SMS)
  - Template ID or name
  - Recipient
  - Status

The API design and data structure are part of your assignment.

---

### Bonus Task 5: Rate Limiting

Implement rate limiting to prevent spam and system abuse.

**Requirements:**
- Track the number of messages sent to each recipient (email address or phone number)
- Enforce a limit (e.g., maximum 5 messages per recipient per hour)
- Return an appropriate error response when the limit is exceeded
- Include rate limit information in API responses (e.g., remaining quota, reset time)

**Example Error Response:**
```json
{
  "error": "Rate limit exceeded",
  "message": "Maximum 5 messages per hour allowed for recipient@email.com",
  "retry_after": "2025-12-02T15:30:00Z"
}
```

The implementation approach (in-memory, database, cache, etc.) is your choice.

---

### Bonus Task 6: Template Management UI

Build a basic user interface for managing message templates.

**Requirements:**
- Create a web-based UI that allows users to:
  - View all existing templates in a list or table format
  - Create new templates with a form (name, content, template language, channel type, subject for emails)
  - Edit existing templates
  - Delete templates
  - View message history for a given template
- The UI should be intuitive and user-friendly

**Technical Implementation:**
- You can use any frontend framework or library (React, Vue, Angular, plain HTML/CSS/JS, etc.)
- The UI should communicate with your API endpoints
- Bonus points for responsive design that works on mobile devices

**Example Features:**
- Syntax highlighting for template content
- Real-time preview of template rendering
- Template validation feedback
- Search/filter functionality for templates

This task demonstrates full-stack capabilities and understanding of complete application development.

---

## 🚀 Submission Instructions

1. **Complete the implementation** following the requirements above
2. **Write tests** for key functionalities
3. **Add documentation** with clear instructions on how to use your API:
   - Setup instructions (dependencies, environment variables, database setup)
   - How to run the application
   - API endpoints documentation with examples
   - **Recommended:** Include a flowchart showing the message sending flow (template retrieval → rendering → channel selection → delivery)
4. **Commit your work** with clear, explanatory commit messages
5. **Submit a Pull Request** with your solution

---

## 🤖 AI Tools Policy

**You are welcome to use AI tools** (ChatGPT, GitHub Copilot, Claude, etc.) to assist with this assignment.

**However, you are expected to:**
- Fully understand all the code you submit
- Be able to explain any part of your implementation
- Stand behind the architectural and design decisions made

---

## 📞 Need Help?

**We're here to support you!**

Don't hesitate to reach out if you have any questions, no matter how small. We want you to succeed and are happy to clarify anything that's unclear.

**Good luck! We're excited to see your solution! 🎉**