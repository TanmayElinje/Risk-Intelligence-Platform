"""
Email Service - SMTP email sending for risk alerts
backend/services/email_service.py

Supports Gmail (App Password), Outlook, and generic SMTP servers.
Configure via .env file or EmailAlertPreference in the database.
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from backend.utils import log

# Load .env file - try multiple locations
from pathlib import Path
from dotenv import load_dotenv

_this_dir = Path(__file__).resolve().parent
# Try: project_root/.env, backend/.env
for _env_candidate in [
    _this_dir.parent.parent / '.env',   # project_root/.env  (from backend/services/)
    _this_dir.parent / '.env',           # backend/.env
    _this_dir / '.env',                  # backend/services/.env
]:
    if _env_candidate.exists():
        load_dotenv(dotenv_path=_env_candidate)
        break
else:
    # Fallback: let dotenv search upward automatically
    load_dotenv()

# Load SMTP config from environment
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'Risk Intelligence Platform')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'


def is_email_configured():
    """Check if SMTP credentials are configured"""
    return bool(SMTP_USER and SMTP_PASSWORD)


def send_email(to_email, subject, html_body, text_body=None):
    """
    Send an email via SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML content of the email
        text_body: Plain text fallback (optional, auto-generated if not provided)

    Returns:
        dict with 'success' bool and 'message' string
    """
    if not is_email_configured():
        log.warning("Email not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
        return {
            'success': False,
            'message': 'Email not configured. Add SMTP_USER and SMTP_PASSWORD to your .env file.'
        }

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Plain text fallback
        if not text_body:
            text_body = html_body.replace('<br>', '\n').replace('</p>', '\n')
            # Strip remaining HTML tags
            import re
            text_body = re.sub(r'<[^>]+>', '', text_body)

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Connect and send
        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()

        log.info(f"Email sent successfully to {to_email}: {subject}")
        return {'success': True, 'message': 'Email sent successfully'}

    except smtplib.SMTPAuthenticationError:
        log.error(f"SMTP authentication failed for {SMTP_USER}")
        return {
            'success': False,
            'message': 'SMTP authentication failed. Check your email and app password.'
        }
    except Exception as e:
        log.error(f"Failed to send email to {to_email}: {str(e)}")
        return {'success': False, 'message': f'Failed to send email: {str(e)}'}


# ==================== EMAIL TEMPLATES ====================

def build_alert_email(alerts, recipient_name='User'):
    """
    Build an HTML email for risk alerts.

    Args:
        alerts: List of alert dicts with keys: symbol, risk_score, risk_level,
                alert_type, severity, explanation
        recipient_name: Name of the recipient

    Returns:
        (subject, html_body) tuple
    """
    count = len(alerts)
    high_count = sum(1 for a in alerts if a.get('severity') == 'high' or a.get('risk_level') == 'high')

    subject = f"🚨 {count} Risk Alert{'s' if count != 1 else ''}"
    if high_count:
        subject += f" ({high_count} High Risk)"

    # Build alert rows
    alert_rows = ''
    for alert in alerts:
        risk_score = alert.get('risk_score')
        risk_pct = f"{float(risk_score) * 100:.1f}%" if risk_score else 'N/A'

        level = (alert.get('risk_level') or alert.get('severity') or 'medium').lower()
        level_colors = {
            'high': ('#dc2626', '#fef2f2', '#991b1b'),
            'medium': ('#d97706', '#fffbeb', '#92400e'),
            'low': ('#16a34a', '#f0fdf4', '#166534'),
        }
        bg, card_bg, text_color = level_colors.get(level, level_colors['medium'])

        alert_rows += f'''
        <tr>
          <td style="padding: 16px; border-bottom: 1px solid #e5e7eb;">
            <div style="background: {card_bg}; border-left: 4px solid {bg}; border-radius: 8px; padding: 16px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 18px; font-weight: 700; color: #111827;">{alert.get('symbol', 'N/A')}</span>
                <span style="background: {bg}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">{level.upper()}</span>
              </div>
              <div style="color: #6b7280; font-size: 14px; margin-bottom: 4px;">
                Risk Score: <strong style="color: {text_color};">{risk_pct}</strong>
                &nbsp;&bull;&nbsp;
                Type: <strong>{(alert.get('alert_type') or 'risk_alert').replace('_', ' ').title()}</strong>
              </div>
              {f'<div style="color: #4b5563; font-size: 13px; margin-top: 8px;">{alert.get("explanation") or alert.get("risk_drivers") or ""}</div>' if alert.get('explanation') or alert.get('risk_drivers') else ''}
            </div>
          </td>
        </tr>
        '''

    html_body = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background: #f3f4f6; padding: 32px 16px;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
              <!-- Header -->
              <tr>
                <td style="background: linear-gradient(135deg, #1e40af, #7c3aed); padding: 32px; text-align: center;">
                  <h1 style="color: white; margin: 0; font-size: 24px;">🚨 Risk Alert</h1>
                  <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px;">
                    {count} alert{'s' if count != 1 else ''} detected &bull; {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                  </p>
                </td>
              </tr>

              <!-- Greeting -->
              <tr>
                <td style="padding: 24px 24px 8px;">
                  <p style="color: #374151; font-size: 15px; margin: 0;">
                    Hi {recipient_name},<br><br>
                    The following risk alerts were triggered for stocks you're monitoring:
                  </p>
                </td>
              </tr>

              <!-- Alerts -->
              {alert_rows}

              <!-- Footer -->
              <tr>
                <td style="padding: 24px; border-top: 1px solid #e5e7eb;">
                  <p style="color: #9ca3af; font-size: 12px; margin: 0; text-align: center;">
                    Risk Intelligence Platform &bull; AI-Powered Financial Risk Monitoring<br>
                    You can manage your email preferences in Settings.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    '''

    return subject, html_body


def build_daily_digest_email(summary, recipient_name='User'):
    """
    Build an HTML daily digest email.

    Args:
        summary: Dict with keys: total_stocks, high_risk, medium_risk, low_risk,
                 top_risks (list of dicts), avg_risk_score
        recipient_name: Name of the recipient

    Returns:
        (subject, html_body) tuple
    """
    subject = f"📊 Daily Risk Digest — {summary.get('high_risk', 0)} High Risk Stocks"

    # Top risks table rows
    top_rows = ''
    for stock in summary.get('top_risks', [])[:10]:
        score = float(stock.get('risk_score', 0))
        pct = f"{score * 100:.1f}%"
        level = stock.get('risk_level', 'medium').lower()
        color = '#dc2626' if level == 'high' else '#d97706' if level == 'medium' else '#16a34a'

        top_rows += f'''
        <tr>
          <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6; font-weight: 600; color: #111827;">{stock.get('symbol')}</td>
          <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6; color: {color}; font-weight: 600;">{pct}</td>
          <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6;">
            <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;">{level.upper()}</span>
          </td>
        </tr>
        '''

    html_body = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background: #f3f4f6; padding: 32px 16px;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
              <!-- Header -->
              <tr>
                <td style="background: linear-gradient(135deg, #1e40af, #7c3aed); padding: 32px; text-align: center;">
                  <h1 style="color: white; margin: 0; font-size: 24px;">📊 Daily Risk Digest</h1>
                  <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px;">
                    {datetime.now().strftime('%A, %B %d, %Y')}
                  </p>
                </td>
              </tr>

              <!-- Summary Cards -->
              <tr>
                <td style="padding: 24px;">
                  <p style="color: #374151; margin: 0 0 16px;">Hi {recipient_name}, here's your daily risk overview:</p>
                  <table width="100%" cellpadding="0" cellspacing="8">
                    <tr>
                      <td style="background: #fef2f2; border-radius: 8px; padding: 16px; text-align: center; width: 33%;">
                        <div style="font-size: 28px; font-weight: 700; color: #dc2626;">{summary.get('high_risk', 0)}</div>
                        <div style="font-size: 12px; color: #991b1b; font-weight: 600;">HIGH RISK</div>
                      </td>
                      <td style="background: #fffbeb; border-radius: 8px; padding: 16px; text-align: center; width: 33%;">
                        <div style="font-size: 28px; font-weight: 700; color: #d97706;">{summary.get('medium_risk', 0)}</div>
                        <div style="font-size: 12px; color: #92400e; font-weight: 600;">MEDIUM</div>
                      </td>
                      <td style="background: #f0fdf4; border-radius: 8px; padding: 16px; text-align: center; width: 33%;">
                        <div style="font-size: 28px; font-weight: 700; color: #16a34a;">{summary.get('low_risk', 0)}</div>
                        <div style="font-size: 12px; color: #166534; font-weight: 600;">LOW RISK</div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Top Risks Table -->
              <tr>
                <td style="padding: 0 24px 24px;">
                  <h3 style="color: #111827; margin: 0 0 12px; font-size: 16px;">Top Risk Stocks</h3>
                  <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                    <tr style="background: #f9fafb;">
                      <th style="padding: 8px 12px; text-align: left; font-size: 12px; color: #6b7280; font-weight: 600;">SYMBOL</th>
                      <th style="padding: 8px 12px; text-align: left; font-size: 12px; color: #6b7280; font-weight: 600;">RISK</th>
                      <th style="padding: 8px 12px; text-align: left; font-size: 12px; color: #6b7280; font-weight: 600;">LEVEL</th>
                    </tr>
                    {top_rows}
                  </table>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="padding: 24px; border-top: 1px solid #e5e7eb;">
                  <p style="color: #9ca3af; font-size: 12px; margin: 0; text-align: center;">
                    Risk Intelligence Platform &bull; AI-Powered Financial Risk Monitoring<br>
                    Manage preferences in Settings.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    '''

    return subject, html_body


def send_risk_alerts(to_email, alerts, recipient_name='User'):
    """Send risk alert email"""
    subject, html = build_alert_email(alerts, recipient_name)
    return send_email(to_email, subject, html)


def send_daily_digest(to_email, summary, recipient_name='User'):
    """Send daily digest email"""
    subject, html = build_daily_digest_email(summary, recipient_name)
    return send_email(to_email, subject, html)
