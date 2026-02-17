// frontend/src/hooks/useNotifications.js
import { useState, useEffect, useCallback } from 'react';

export const useNotifications = () => {
  const [permission, setPermission] = useState('default');
  const [soundEnabled, setSoundEnabled] = useState(true);

  useEffect(() => {
    // Check notification permission
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }

    // Load sound preference
    const savedSound = localStorage.getItem('notifications_sound');
    if (savedSound !== null) {
      setSoundEnabled(savedSound === 'true');
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (!('Notification' in window)) {
      console.log('Browser does not support notifications');
      return false;
    }

    const result = await Notification.requestPermission();
    setPermission(result);
    return result === 'granted';
  }, []);

  const playSound = useCallback((type = 'default') => {
    if (!soundEnabled) return;

    // Create audio context for notification sounds
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Different sounds for different alert types
    if (type === 'high-risk') {
      oscillator.frequency.value = 800;
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } else if (type === 'alert') {
      oscillator.frequency.value = 600;
      gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } else {
      // Default notification sound
      oscillator.frequency.value = 500;
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    }
  }, [soundEnabled]);

  const showNotification = useCallback(
    async (title, options = {}) => {
      // Play sound first
      if (options.sound !== false) {
        playSound(options.soundType || 'default');
      }

      // Show browser notification if permitted
      if (permission === 'granted') {
        const notification = new Notification(title, {
          icon: '/logo.png',
          badge: '/logo.png',
          tag: options.tag || 'default',
          renotify: true,
          requireInteraction: options.requireInteraction || false,
          ...options,
        });

        // Auto-close after 5 seconds
        setTimeout(() => notification.close(), 5000);

        // Handle click
        if (options.onClick) {
          notification.onclick = options.onClick;
        }

        return notification;
      } else if (permission === 'default') {
        // Try to request permission
        const granted = await requestPermission();
        if (granted) {
          return showNotification(title, options);
        }
      }

      return null;
    },
    [permission, playSound, requestPermission]
  );

  const toggleSound = useCallback(() => {
    const newValue = !soundEnabled;
    setSoundEnabled(newValue);
    localStorage.setItem('notifications_sound', newValue.toString());
  }, [soundEnabled]);

  return {
    permission,
    soundEnabled,
    requestPermission,
    showNotification,
    toggleSound,
    playSound,
  };
};