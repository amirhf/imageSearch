import { Link, router } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { useSession } from '@/auth/useSession';
import { AuthForm } from '@/components/AuthForm';
import { Screen } from '@/components/Screen';
import { colors, typography } from '@/theme/tokens';

export default function SignUpScreen() {
  const { signUp, isConfigured, user } = useSession();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace('/settings');
    }
  }, [user]);

  async function handleSubmit({ email, password }: { email: string; password: string }) {
    setError(null);
    setMessage(null);
    setIsSubmitting(true);
    try {
      await signUp(email, password);
      setMessage('Account created. Check your email if confirmation is enabled.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen title="Create account" subtitle="Supabase auth keeps the mobile app aligned with web.">
      {!isConfigured ? (
        <Text style={styles.errorText}>
          Supabase env vars are missing. Add EXPO_PUBLIC_SUPABASE_URL and
          EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY.
        </Text>
      ) : null}

      <AuthForm
        disabled={!isConfigured}
        error={error}
        isSubmitting={isSubmitting}
        message={message}
        mode="sign-up"
        onSubmit={handleSubmit}
        footer={
          <Link href="/sign-in" style={styles.link}>
            Already have an account?
          </Link>
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 18,
  },
  link: {
    color: colors.accent,
    fontSize: typography.body,
    fontWeight: '800',
    textAlign: 'center',
  },
});
