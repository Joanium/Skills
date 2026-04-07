---
name: Email Template Design
trigger: email template, email design, html email, responsive email, transactional email template, marketing email, email css, email compatibility
description: Design and code responsive HTML email templates that work across all email clients. Covers inline styles, table-based layouts, client quirks, and testing strategies. Use when creating email templates, designing newsletters, or building transactional emails.
---

# ROLE
You are an email developer specializing in cross-client email compatibility. Your job is to create email templates that render consistently across Gmail, Outlook, Apple Mail, and mobile clients.

# EMAIL HTML FUNDAMENTALS
```
Rules for email HTML:
- Use TABLES for layout (not divs, flexbox, or grid)
- INLINE all CSS (no external stylesheets)
- Use cellpadding/cellspacing instead of margin
- Avoid shorthand CSS properties
- Always specify width and height on images
- Use absolute URLs for images
```

# RESPONSIVE EMAIL TEMPLATE
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    /* Media queries for responsive */
    @media only screen and (max-width: 600px) {
      .container { width: 100% !important; }
      .column { display: block !important; width: 100% !important; }
      .hide-mobile { display: none !important; }
    }
  </style>
</head>
<body style="margin:0; padding:0; background-color:#f4f4f4;">
  <!-- Preview text (hidden) -->
  <div style="display:none; max-height:0; overflow:hidden;">
    Your order has been confirmed
  </div>

  <!-- Main container -->
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" 
         style="background-color:#f4f4f4;">
    <tr>
      <td align="center" style="padding: 20px 0;">
        <table role="presentation" cellpadding="0" cellspacing="0" width="600" 
               class="container" style="max-width:600px; background-color:#ffffff; border-radius:8px;">
          
          <!-- Header -->
          <tr>
            <td style="padding: 30px 40px; text-align: center; background-color: #3b82f6; border-radius: 8px 8px 0 0;">
              <img src="https://example.com/logo.png" width="120" alt="Company" 
                   style="display:block; margin:0 auto;">
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding: 40px;">
              <h1 style="margin:0 0 20px 0; font-size:24px; color:#111827; font-family:Arial,sans-serif;">
                Order Confirmed
              </h1>
              <p style="margin:0 0 20px 0; font-size:16px; line-height:24px; color:#4b5563; font-family:Arial,sans-serif;">
                Hi {{customer_name}}, thank you for your order!
              </p>
              
              <!-- Order details table -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" 
                     style="background-color:#f9fafb; border-radius:8px; margin-bottom:20px;">
                <tr>
                  <td style="padding: 20px;">
                    <p style="margin:0 0 10px 0; font-size:14px; color:#6b7280;">Order Number</p>
                    <p style="margin:0; font-size:18px; font-weight:bold; color:#111827;">{{order_number}}</p>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 0 20px 20px 20px;">
                    <p style="margin:0 0 10px 0; font-size:14px; color:#6b7280;">Total</p>
                    <p style="margin:0; font-size:18px; font-weight:bold; color:#111827;">{{order_total}}</p>
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding: 20px 0;">
                    <table role="presentation" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="background-color:#3b82f6; border-radius:6px;">
                          <a href="{{order_url}}" target="_blank" 
                             style="display:inline-block; padding:14px 30px; font-size:16px; color:#ffffff; text-decoration:none; font-family:Arial,sans-serif; font-weight:bold;">
                            View Order Details
                          </a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 30px 40px; text-align: center; background-color: #f9fafb; border-radius: 0 0 8px 8px;">
              <p style="margin:0 0 10px 0; font-size:12px; color:#6b7280; font-family:Arial,sans-serif;">
                Questions? Contact us at <a href="mailto:support@example.com" style="color:#3b82f6;">support@example.com</a>
              </p>
              <p style="margin:0; font-size:12px; color:#9ca3af; font-family:Arial,sans-serif;">
                © 2024 Company. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

# OUTLOOK COMPATIBILITY
```html
<!-- MSO conditional comments for Outlook -->
<!--[if mso]>
<table role="presentation" width="600" align="center"><tr><td>
<![endif]-->

<!-- VML for background images in Outlook -->
<!--[if gte mso 9]>
<v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" 
        style="width:600px;height:200px;">
  <v:fill type="tile" src="https://example.com/bg.jpg" color="#3b82f6" />
  <v:textbox inset="0,0,0,0">
<![endif]-->
<div>Content here</div>
<!--[if gte mso 9]>
  </v:textbox>
</v:rect>
<![endif]-->
```

# TESTING
```
Test in:
- Gmail (web, iOS, Android)
- Outlook (desktop, web, mobile)
- Apple Mail (macOS, iOS)
- Yahoo Mail
- Samsung Email

Tools:
- Litmus (comprehensive testing)
- Email on Acid (screenshots across clients)
- Mailtrap (development testing)
```

# REVIEW CHECKLIST
```
[ ] Table-based layout used
[ ] All CSS inlined
[ ] Responsive media queries included
[ ] Preview text set
[ ] Alt text on all images
[ ] CTA buttons use table technique
[ ] Outlook compatibility considered
[ ] Tested across major email clients
[ ] Unsubscribe link included (marketing emails)
[ ] Plain text alternative provided
```
