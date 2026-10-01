import { useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useAppStore } from '../stores/useAppStore';
import { getAccessToken } from '../lib/api';
import { getWebSocketUrl } from '../lib/config';

export function useWebSocket(topic: string = 'inbox', onEvent?: (event: string, data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const setWsConnected = useAppStore((s) => s.setWsConnected);
  const incrementUnreadAlerts = useAppStore((s) => s.incrementUnreadAlerts);
  const setNarration = useAppStore((s) => s.setNarration);

  useEffect(() => {
    let reconnectTimeout: any;
    let isMounted = true;

    const connect = () => {
      try {
        const token = getAccessToken();
        const baseWsUrl = getWebSocketUrl();
        const urlWithToken = token ? `${baseWsUrl}?token=${encodeURIComponent(token)}` : baseWsUrl;

        const ws = new WebSocket(urlWithToken);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setWsConnected(true);
          if (topic) {
            ws.send(JSON.stringify({ action: 'subscribe', topic }));
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const parsed = JSON.parse(event.data);
            const { event: eventType, data } = parsed;

            if (onEvent) {
              onEvent(eventType, data);
            }

            if (eventType === 'new_complaint') {
              toast.success(`NCRP Inflow: ${data.complaint_number} (₹${Number(data.amount_lost_inr).toLocaleString('en-IN')})`, {
                icon: '🚨',
                duration: 4000
              });
            } else if (eventType === 'new_alert') {
              incrementUnreadAlerts();
              toast.error(`ALERT [${data.severity}]: ${data.title}`, {
                icon: '⚠️',
                duration: 5000
              });
            } else if (eventType === 'vasp_found') {
              toast.success(`VASP ATTRIBUTED: ${data.vasp_name} (${data.confidence_score}% Confidence)`, {
                icon: '🏛️',
                duration: 6000
              });
            } else if (eventType === 'hop_discovered' && data.narration) {
              setNarration(data.narration);
            }
          } catch (e) {
            console.error('WS parse error:', e);
          }
        };

        ws.onclose = (e) => {
          if (!isMounted) return;
          setWsConnected(false);
          // If not closed intentionally, attempt reconnect after 3s
          if (e.code !== 1000 && e.code !== 4401) {
            reconnectTimeout = setTimeout(connect, 3000);
          }
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setWsConnected(false);
          ws.close();
        };
      } catch (err) {
        if (isMounted) setWsConnected(false);
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close(1000, 'Component unmounted');
    };
  }, [topic, onEvent, setWsConnected, incrementUnreadAlerts, setNarration]);

  return wsRef;
}
