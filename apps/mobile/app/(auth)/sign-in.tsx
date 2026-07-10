import { Link, router } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { useSession } from '@/auth/useSession';
import { AuthForm } from '@/components/AuthForm';
import { Screen } from '@/components/Screen';
import { colors, typography } from '@/theme/tokens';

export default function SignInScreen() {
  const { signIn, isConfigured, user } = useSession();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace('/settings');
    }
  }, [user]);

  async function handleSubmit({ email, password }: { email: string; password: string }) {
    setError(null);
    setIsSubmitting(true);
    try {
      await signIn(email, password);
      router.replace('/settings');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen title="Sign in" subtitle="Use the same Supabase account as the web app.">
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
        mode="sign-in"
        onSubmit={handleSubmit}
        footer={
          <Link href="/sign-up" style={styles.link}>
            Create an account
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
