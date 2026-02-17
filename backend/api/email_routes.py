"""
Email Alert API Routes
backend/api/email_routes.py

Endpoints for managing email alert preferences and sending test/digest emails.
"""
from flask import Blueprint, request, jsonify
from backend.database import DatabaseService
from backend.database.models import User, EmailAlertPreference
from backend.utils import log
from backend.utils.auth import get_current_user, require_auth
from backend.services.email_service import (
    is_email_configured, send_email, send_risk_alerts,
    send_daily_digest, build_alert_email, build_daily_digest_email
)
from datetime import datetime

email_bp = Blueprint('email', __name__, url_prefix='/api/email')


# ==================== GET EMAIL CONFIG STATUS ====================

@email_bp.route('/status', methods=['GET'])
@require_auth
def get_email_status():
    """
    Check if SMTP email is configured on the server.

    Returns:
        {
            "configured": true/false,
            "smtp_user": "u***@gmail.com" (masked)
        }
    """
    import os
    smtp_user = os.getenv('SMTP_USER', '')
    masked = ''
    if smtp_user:
        parts = smtp_user.split('@')
        if len(parts) == 2:
            name = parts[0]
            masked = name[0] + '***' + '@' + parts[1] if len(name) > 1 else name + '@' + parts[1]
        else:
            masked = smtp_user[:2] + '***'

    return jsonify({
        'configured': is_email_configured(),
        'smtp_user': masked if is_email_configured() else None
    }), 200


# ==================== GET/UPDATE EMAIL PREFERENCES ====================

@email_bp.route('/preferences', methods=['GET'])
@require_auth
def get_email_preferences():
    """
    Get user's email alert preferences.

    Returns:
        {
            "preferences": {
                "email_alerts_enabled": true,
                "alert_email": "user@example.com",
                "high_risk_alerts": true,
                "medium_risk_alerts": false,
                "daily_digest": true,
                "watchlist_only": false
            }
        }
    """
    try:
        user = get_current_user()

        with DatabaseService() as db:
            pref = db.db.query(EmailAlertPreference).filter(
                EmailAlertPreference.user_id == user.id
            ).first()

            if not pref:
                # Return defaults
                return jsonify({
                    'preferences': {
                        'email_alerts_enabled': False,
                        'alert_email': user.email,
                        'high_risk_alerts': True,
                        'medium_risk_alerts': False,
                        'daily_digest': False,
                        'watchlist_only': False,
                    }
                }), 200

            return jsonify({
                'preferences': pref.to_dict()
            }), 200

    except Exception as e:
        log.error(f"Error getting email preferences: {str(e)}")
        return jsonify({'error': 'Failed to get preferences', 'message': str(e)}), 500


@email_bp.route('/preferences', methods=['PUT'])
@require_auth
def update_email_preferences():
    """
    Update user's email alert preferences.

    Request body:
        {
            "email_alerts_enabled": true,
            "alert_email": "user@example.com",
            "high_risk_alerts": true,
            "medium_risk_alerts": false,
            "daily_digest": true,
            "watchlist_only": false
        }

    Returns:
        {
            "message": "Preferences updated",
            "preferences": {...}
        }
    """
    try:
        user = get_current_user()
        data = request.get_json()

        with DatabaseService() as db:
            pref = db.db.query(EmailAlertPreference).filter(
                EmailAlertPreference.user_id == user.id
            ).first()

            if not pref:
                pref = EmailAlertPreference(
                    user_id=user.id,
                    alert_email=user.email,
                )
                db.db.add(pref)

            # Update fields
            if 'email_alerts_enabled' in data:
                pref.email_alerts_enabled = bool(data['email_alerts_enabled'])
            if 'alert_email' in data:
                pref.alert_email = data['alert_email'].strip()
            if 'high_risk_alerts' in data:
                pref.high_risk_alerts = bool(data['high_risk_alerts'])
            if 'medium_risk_alerts' in data:
                pref.medium_risk_alerts = bool(data['medium_risk_alerts'])
            if 'daily_digest' in data:
                pref.daily_digest = bool(data['daily_digest'])
            if 'watchlist_only' in data:
                pref.watchlist_only = bool(data['watchlist_only'])

            pref.updated_at = datetime.utcnow()
            db.db.commit()
            db.db.refresh(pref)

            log.info(f"User {user.username} updated email preferences")

            return jsonify({
                'message': 'Preferences updated successfully',
                'preferences': pref.to_dict()
            }), 200

    except Exception as e:
        log.error(f"Error updating email preferences: {str(e)}")
        return jsonify({'error': 'Failed to update preferences', 'message': str(e)}), 500


# ==================== SEND TEST EMAIL ====================

@email_bp.route('/test', methods=['POST'])
@require_auth
def send_test_email():
    """
    Send a test email to verify configuration.

    Request body (optional):
        { "email": "override@example.com" }

    Returns:
        { "success": true/false, "message": "..." }
    """
    try:
        user = get_current_user()
        data = request.get_json() or {}

        to_email = data.get('email', '').strip()
        if not to_email:
            # Use preference email or user email
            with DatabaseService() as db:
                pref = db.db.query(EmailAlertPreference).filter(
                    EmailAlertPreference.user_id == user.id
                ).first()
                to_email = pref.alert_email if pref and pref.alert_email else user.email

        if not to_email:
            return jsonify({'success': False, 'message': 'No email address configured'}), 400

        # Build a sample alert email
        sample_alerts = [
            {
                'symbol': 'TSLA',
                'risk_score': 0.82,
                'risk_level': 'high',
                'alert_type': 'sudden_spike',
                'severity': 'high',
                'explanation': 'This is a test alert. Risk score spiked due to increased volatility and negative sentiment.',
            },
            {
                'symbol': 'NVDA',
                'risk_score': 0.55,
                'risk_level': 'medium',
                'alert_type': 'high_risk',
                'severity': 'medium',
                'explanation': 'This is a test alert. Moderate risk detected from market drawdown.',
            },
        ]

        result = send_risk_alerts(
            to_email=to_email,
            alerts=sample_alerts,
            recipient_name=user.full_name or user.username
        )

        log.info(f"Test email {'sent' if result['success'] else 'failed'} for user {user.username} to {to_email}")

        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        log.error(f"Error sending test email: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== SEND DAILY DIGEST (MANUAL TRIGGER) ====================

@email_bp.route('/digest', methods=['POST'])
@require_auth
def send_digest_now():
    """
    Manually trigger a daily digest email for the current user.

    Returns:
        { "success": true/false, "message": "..." }
    """
    try:
        user = get_current_user()

        with DatabaseService() as db:
            # Get email preference
            pref = db.db.query(EmailAlertPreference).filter(
                EmailAlertPreference.user_id == user.id
            ).first()

            to_email = pref.alert_email if pref and pref.alert_email else user.email
            if not to_email:
                return jsonify({'success': False, 'message': 'No email address configured'}), 400

            # Get current risk data for digest
            risk_scores = db.get_latest_risk_scores()

            if risk_scores.empty:
                return jsonify({'success': False, 'message': 'No risk data available'}), 404

            high_risk = risk_scores[risk_scores['risk_level'] == 'High']
            medium_risk = risk_scores[risk_scores['risk_level'] == 'Medium']
            low_risk = risk_scores[risk_scores['risk_level'] == 'Low']

            top_risks = []
            for _, row in risk_scores.head(10).iterrows():
                top_risks.append({
                    'symbol': row['symbol'],
                    'risk_score': float(row['risk_score']) if row['risk_score'] else 0,
                    'risk_level': row['risk_level'],
                })

            summary = {
                'total_stocks': len(risk_scores),
                'high_risk': len(high_risk),
                'medium_risk': len(medium_risk),
                'low_risk': len(low_risk),
                'avg_risk_score': float(risk_scores['risk_score'].mean()) if not risk_scores.empty else 0,
                'top_risks': top_risks,
            }

            result = send_daily_digest(
                to_email=to_email,
                summary=summary,
                recipient_name=user.full_name or user.username
            )

            return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        log.error(f"Error sending digest: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500