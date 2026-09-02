import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface ShortcutHandlers {
  onOpenCommandPalette?: () => void;
  onEscape?: () => void;
  onTriggerExecution?: () => void;
}

export function useKeyboardShortcuts({
  onOpenCommandPalette,
  onEscape,
  onTriggerExecution,
}: ShortcutHandlers = {}) {
  const router = useRouter();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Check if user is typing in an input / textarea
      const target = e.target as HTMLElement | null;
      const isInput =
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.isContentEditable;

      // Ctrl+K or Cmd+K
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        onOpenCommandPalette?.();
        return;
      }

      // Escape
      if (e.key === 'Escape') {
        onEscape?.();
        return;
      }

      // If user is actively typing in a text field, do not trigger global navigation
      if (isInput) return;

      // Numbers 1-8 for instant navigation
      switch (e.key) {
        case '1':
          router.push('/');
          break;
        case '2':
          router.push('/execution');
          break;
        case '3':
          router.push('/planner');
          break;
        case '4':
          router.push('/specialists');
          break;
        case '5':
          router.push('/artifacts');
          break;
        case '6':
          router.push('/memory');
          break;
        case '7':
          router.push('/events');
          break;
        case '8':
          router.push('/settings');
          break;
        default:
          break;
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router, onOpenCommandPalette, onEscape, onTriggerExecution]);
}
